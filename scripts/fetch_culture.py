"""
文化篇：抓取全 42 方言 × 30 課內文，直接寫入 corpus.db。

流程：
  1. cu_practice/textId.json → {dialect_id: [tid × 30]}（全域，只抓一次）
  2. text/read_embed.php?tid={tid}&mode=1 → 解析族語句子（同歌謠篇/圖畫故事篇格式）
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

TEXTID_URL = "https://web.klokah.tw/extension/cu_practice/textId.json"
BASE_EMBED = "https://web.klokah.tw/text/read_embed.php"
BASE_SOUND = "https://web.klokah.tw/text/sound"
NOTEBOOK   = "文化篇"
SOURCE     = "e樂園"
SLEEP      = 0.4


def load_textid_map() -> dict:
    r = requests.get(TEXTID_URL, timeout=15)
    r.raise_for_status()
    raw = r.json()
    return {int(k): v for k, v in raw.items()}


def fetch_sentences(tid: int) -> list[dict]:
    try:
        r = requests.get(BASE_EMBED, params={"tid": tid, "mode": "1"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"  SKIP embed tid={tid}: {e}")
        return []

    rows = []
    for sent in soup.select(".read-sentence.Ab"):
        words = [w.get_text(strip=True) for w in sent.find_all("div", class_="word")]
        ab = " ".join(w for w in words if w)
        ch_div = sent.find("div", class_="read-sentence")
        ch = ch_div.get_text(strip=True) if ch_div else ""
        audio_id = ch_div.get("data-value", "") if ch_div else ""
        audio = f"{BASE_SOUND}/{tid}/{audio_id}.mp3" if audio_id else ""
        if ab:
            rows.append({"text_ab": ab, "text_ch": ch, "audio": audio})
    return rows


def main():
    print("Loading textId.json ...", end=" ")
    textid_map = load_textid_map()
    print(f"{len(textid_map)} dialects")

    conn = get_conn()
    conn.execute(
        "DELETE FROM corpus WHERE notebook = ? AND source = ?",
        (NOTEBOOK, SOURCE)
    )
    conn.commit()

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        dialect_rows = 0
        tids = textid_map.get(did, [])

        for lesson_idx, tid in enumerate(tids, 1):
            rows = fetch_sentences(tid)
            time.sleep(SLEEP)
            if not rows:
                continue
            unit = f"課{lesson_idx:02d}"
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname, unit,
                     r["text_ab"], r["text_ch"], "", "", "", r.get("audio", ""))
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
