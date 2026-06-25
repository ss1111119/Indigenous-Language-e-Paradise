"""
LIMA 有聲書：抓取全 42 方言 × 7 課 × 4 模式，直接寫入 corpus.db。

資料來源：
  - json/title.json → 課程名稱
  - json/{did}/{lessonNo}.json → vocabulary / story / conversation / question

音檔：
  - vocabulary/conversation/question: https://web.klokah.tw/lima/sound/{did}/{type}/{audio}.mp3
  - story: https://web.klokah.tw/lima/sound/{did}/story/{audio}-18.mp3
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_URL   = "https://web.klokah.tw/lima"
TITLE_URL  = f"{BASE_URL}/json/title.json"
NOTEBOOK   = "LIMA 有聲書"
SOURCE     = "e樂園"
SLEEP      = 0.4


def load_titles() -> dict:
    r = requests.get(TITLE_URL, timeout=15)
    r.raise_for_status()
    data = r.json()
    # data = {ab: {did: [lesson1..7]}, ch: [...]}
    return data


def fetch_lesson(did: int, lesson_no: int) -> dict | None:
    url = f"{BASE_URL}/json/{did}/{lesson_no}.json"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  SKIP did={did} lesson={lesson_no}: {e}")
        return None


def audio_url(did: int, atype: str, audio_id: str) -> str:
    if atype == "story":
        return f"{BASE_URL}/sound/{did}/story/{audio_id}-18.mp3"
    return f"{BASE_URL}/sound/{did}/{atype}/{audio_id}.mp3"


def extract_rows(data: dict, did: int, unit: str) -> list[tuple]:
    rows = []
    for atype in ("vocabulary", "story", "conversation", "question"):
        for item in (data.get(atype) or []):
            ab = (item.get("ab") or "").strip()
            ch = (item.get("ch") or "").strip()
            audio_id = item.get("audio", "")
            audio = audio_url(did, atype, audio_id) if audio_id else ""
            if ab:
                rows.append((SOURCE, NOTEBOOK, did, "", f"{unit}-{atype}", ab, ch, "", "", "", audio))
    return rows


def main():
    titles = load_titles()
    ch_titles = titles.get("ch", [])       # ["時間任意門", ...]
    ab_titles = titles.get("ab", {})        # {"1": [...], "2": [...], ...}

    conn = get_conn()
    conn.execute("DELETE FROM corpus WHERE notebook = ? AND source = ?", (NOTEBOOK, SOURCE))
    conn.commit()

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        dialect_rows = 0
        ab_list = ab_titles.get(str(did), [])

        for lesson_idx in range(1, 8):   # lesson 1-7
            lesson_ch = ch_titles[lesson_idx - 1] if lesson_idx - 1 < len(ch_titles) else f"課{lesson_idx}"
            lesson_ab = ab_list[lesson_idx - 1] if lesson_idx - 1 < len(ab_list) else ""
            unit = lesson_ab if lesson_ab else lesson_ch

            data = fetch_lesson(did, lesson_idx)
            time.sleep(SLEEP)
            if not data:
                continue

            rows = extract_rows(data, did, unit)
            if not rows:
                continue

            # Fill in dialect name
            rows = [(r[0], r[1], r[2], dname, r[4], r[5], r[6], r[7], r[8], r[9], r[10]) for r in rows]

            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
            dialect_rows += len(rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
