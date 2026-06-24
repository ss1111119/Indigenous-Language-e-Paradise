"""
歌謠篇：抓取全 42 方言 × 10 首歌詞，直接寫入 corpus.db。

流程：
  1. song_practice/index.php?d={did}&s={song}&view=lyric  → 取 #text-frame src (tid)
  2. text/read_embed.php?tid={tid}&mode=1                → 解析歌詞句子

歌詞結構：
  .read-sentence.Ab > .word (族語 tokens) + .read-sentence.Ch (中文)
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

BASE_SONG  = "https://web.klokah.tw/extension/song_practice/index.php"
BASE_LYRIC = "https://web.klokah.tw/text/read_embed.php"
BASE_SOUND = "https://web.klokah.tw/text/sound"
NOTEBOOK   = "歌謠篇"
SOURCE     = "e樂園"
SONGS      = range(1, 11)   # 每方言 10 首
SLEEP      = 0.5


def get_tid(dialect_id: int, song: int) -> str | None:
    try:
        r = requests.get(
            BASE_SONG,
            params={"d": dialect_id, "s": song, "view": "lyric"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        tf = soup.find(id="text-frame")
        if tf and tf.get("src"):
            src = tf["src"]
            # 取 tid 參數
            for part in src.split("?", 1)[-1].split("&"):
                if part.startswith("tid="):
                    return part.split("=", 1)[1]
    except Exception as e:
        print(f"  SKIP tid d={dialect_id} s={song}: {e}")
    return None


def fetch_lyrics(tid: str) -> list[dict]:
    try:
        r = requests.get(BASE_LYRIC, params={"tid": tid, "mode": "1"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"  SKIP lyric tid={tid}: {e}")
        return []

    rows = []
    for sent in soup.select(".read-sentence.Ab"):
        words = [
            w.get_text(strip=True)
            for w in sent.find_all("div", class_="word")
        ]
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
        for song in SONGS:
            # Step 1: get tid
            tid = get_tid(did, song)
            time.sleep(SLEEP)
            if not tid:
                continue

            # Step 2: fetch lyrics
            rows = fetch_lyrics(tid)
            time.sleep(SLEEP)
            if not rows:
                continue

            unit = f"歌{song:02d}"
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
