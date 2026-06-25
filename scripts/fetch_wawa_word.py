"""
Wawa 單詞：抓取全 42 方言 × 6 主題，直接寫入 corpus.db。

流程：
  1. requests.Session() 維持 PHPSESSID
  2. POST member/set_prefer_dialect.php?did={did} 切換方言
  3. GET wawa/word.php?pid={pid} → 解析 .showword (.AB / .CH / audio href)

音檔：https://web.klokah.tw/wawa/{audio_href}（頁面直接給出相對路徑）
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

BASE_URL      = "https://web.klokah.tw/wawa"
SET_DIALECT   = "https://web.klokah.tw/member/set_prefer_dialect.php"
WORD_URL      = f"{BASE_URL}/word.php"
NOTEBOOK      = "Wawa 單詞"
SOURCE        = "e樂園"
SLEEP         = 0.4

# 6 主題（pid=1-6）
THEMES = {
    1: "我長大了",
    2: "我的家庭真可愛",
    3: "歡樂慶豐收",
    4: "部落真好玩",
    5: "123大風吹",
    6: "山豬飛鼠來點名",
}


def parse_words(html: str, pid: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for item in soup.select(".showword"):
        ab = (item.select_one(".AB") or type("", (), {"get_text": lambda s, **k: ""})()).get_text(strip=True)
        ch = (item.select_one(".CH") or type("", (), {"get_text": lambda s, **k: ""})()).get_text(strip=True)
        audio_rel = item.select_one("a[href]")
        audio = f"{BASE_URL}/{audio_rel['href']}" if audio_rel else ""
        if ab:
            rows.append({"text_ab": ab, "text_ch": ch, "audio": audio})
    return rows


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # 建立 session（取得 PHPSESSID）
    session.get(WORD_URL, timeout=15)
    time.sleep(SLEEP)

    conn = get_conn()
    conn.execute(
        "DELETE FROM corpus WHERE notebook = ? AND source = ?",
        (NOTEBOOK, SOURCE)
    )
    conn.commit()

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        # 切換方言
        session.post(
            SET_DIALECT,
            data={"did": did},
            headers={"X-Requested-With": "XMLHttpRequest",
                     "Referer": WORD_URL},
            timeout=15,
        )
        time.sleep(SLEEP)

        dialect_rows = 0
        for pid, theme in THEMES.items():
            try:
                r = session.get(WORD_URL, params={"pid": pid}, timeout=15)
                r.raise_for_status()
            except Exception as e:
                print(f"  SKIP did={did} pid={pid}: {e}")
                time.sleep(SLEEP)
                continue

            rows = parse_words(r.text, pid)
            time.sleep(SLEEP)
            if not rows:
                continue

            unit = f"pid{pid}-{theme}"
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname, unit,
                     r["text_ab"], r["text_ch"], "", "", "", r["audio"])
                    for r in rows
                ],
            )
            dialect_rows += len(rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
