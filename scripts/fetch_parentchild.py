"""
親子溝通：抓取全 42 方言 × 4 主題 × 4 小節（句子 + 詞彙），直接寫入 corpus.db。

流程：
  1. parent-child/json/tid.json → D{did}.sentence.L{1-4} / D{did}.word.L{1-4}（各 4 個 tid）
  2. read_embed.php?tid={tid}&mode=1 → 解析族語句子（同其他篇格式）
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

TID_URL    = "https://web.klokah.tw/parent-child/json/tid.json"
BASE_EMBED = "https://web.klokah.tw/text/read_embed.php"
NOTEBOOK   = "親子溝通"
SOURCE     = "e樂園"
SLEEP      = 0.4

# 4 主題 × 4 小節，L1-L4 對應索引 0-3
TOPICS = [
    ["起床", "刷牙", "吃早餐", "出門"],          # L1 主題一
    ["說再見", "洗澡", "吃晚餐", "寫作業"],       # L2 主題二
    ["討論行程", "行前準備", "搭車途中", "到目的地"],  # L3 主題三
    ["購物清單", "選擇商品", "結帳練習", "物品裝袋"],  # L4 主題四
]
LEVELS = ["L1", "L2", "L3", "L4"]


def load_tid_json() -> dict:
    r = requests.get(TID_URL, timeout=15)
    r.raise_for_status()
    return r.json()


BASE_SOUND = "https://web.klokah.tw/text/sound"


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
    print("Loading tid.json ...", end=" ")
    tid_data = load_tid_json()
    print("done")

    conn = get_conn()
    conn.execute(
        "DELETE FROM corpus WHERE notebook = ? AND source = ?",
        (NOTEBOOK, SOURCE)
    )
    conn.commit()

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        key = f"D{did}"
        dialect_data = tid_data.get(key)
        if not dialect_data:
            print(f"[{d_idx:02d}/{total}] {dname} ({did})  SKIP (no data)")
            continue

        dialect_rows = 0
        for l_idx, level in enumerate(LEVELS):
            subtopics = TOPICS[l_idx]
            sentence_tids = dialect_data.get("sentence", {}).get(level, [])
            word_tids     = dialect_data.get("word", {}).get(level, [])

            for s_idx, subtopic in enumerate(subtopics):
                unit = f"主題{l_idx+1}-{subtopic}"

                for category, tids in [("sentence", sentence_tids), ("word", word_tids)]:
                    if s_idx >= len(tids):
                        continue
                    tid = tids[s_idx]
                    rows = fetch_sentences(tid)
                    time.sleep(SLEEP)
                    if not rows:
                        continue
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
