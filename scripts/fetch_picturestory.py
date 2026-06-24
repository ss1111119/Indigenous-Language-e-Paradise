"""
圖畫故事篇：抓取全 42 方言 × 10 則故事，直接寫入 corpus.db。

流程：
  1. ps_practice/index.php?d={did}&l={story}&view=story  → 取 #text-frame src (tid)
  2. text/read_embed.php?tid={tid}&mode=1               → 解析故事句子

句子結構與歌謠篇相同：
  .read-sentence.Ab > .word (族語 tokens) + .read-sentence.Ch (中文)
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

BASE_STORY = "https://web.klokah.tw/extension/ps_practice/index.php"
BASE_EMBED = "https://web.klokah.tw/text/read_embed.php"
BASE_SOUND = "https://web.klokah.tw/text/sound"
NOTEBOOK   = "圖畫故事篇"
SOURCE     = "e樂園"
STORIES    = range(1, 11)  # 每方言 10 則
SLEEP      = 0.5


def get_tid(dialect_id: int, story: int) -> str | None:
    try:
        r = requests.get(
            BASE_STORY,
            params={"d": dialect_id, "l": story, "view": "story"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        tf = soup.find(id="text-frame")
        if tf and tf.get("src"):
            for part in tf["src"].split("?", 1)[-1].split("&"):
                if part.startswith("tid="):
                    tid = part.split("=", 1)[1]
                    return tid if tid else None
    except Exception as e:
        print(f"  SKIP tid d={dialect_id} s={story}: {e}")
    return None


def fetch_sentences(tid: str) -> list[dict]:
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
        for story in STORIES:
            tid = get_tid(did, story)
            time.sleep(SLEEP)
            if not tid:
                continue
            rows = fetch_sentences(tid)
            time.sleep(SLEEP)
            if not rows:
                continue
            unit = f"故事{story:02d}"
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname, unit,
                     r["text_ab"], r["text_ch"], "", "", "", r.get("audio", ""))
                    for r in rows
                ]
            )
            dialect_rows += len(rows)
        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
