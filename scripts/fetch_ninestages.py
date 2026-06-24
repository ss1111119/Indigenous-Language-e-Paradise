"""
九階教材：抓取全 42 方言，直接寫入 corpus.db。
Endpoint: https://web.klokah.tw/ninew/php/getTextNew.php?d={d}&l={lesson}&c={chapter}
  d       = dialect_id (1-43, 跳 12)
  lesson  = 1-9
  chapter = 1-10

Response JSON:
  title / titleCh  — 課題標題
  sentence[].order, .chinese, .word[].ab, .word[].ch
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_URL = "https://web.klokah.tw/ninew/php/getTextNew.php"
NOTEBOOK = "九階"
SOURCE   = "e樂園"
LESSONS  = range(1, 10)   # 1-9
CHAPTERS = range(1, 11)   # 1-10
SLEEP    = 0.3


def join_sentence(words: list) -> str:
    """把 word token 陣列拼回句子，跳過純標點。"""
    parts = []
    for w in words:
        ab = (w.get("ab") or "").strip()
        if ab and ab not in {",", ".", "?", "!", "、", "。", "，"}:
            parts.append(ab)
    return " ".join(parts)


def fetch_one(dialect_id: int, lesson: int, chapter: int) -> list[dict]:
    try:
        r = requests.get(
            BASE_URL,
            params={"d": dialect_id, "l": lesson, "c": chapter},
            timeout=15,
        )
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP d={dialect_id} l={lesson} c={chapter}: {e}")
        return []

    title    = (data.get("title")   or "").strip()
    title_ch = (data.get("titleCh") or "").strip()
    unit = f"L{lesson}-C{chapter} {title}（{title_ch}）" if title else f"L{lesson}-C{chapter}"

    rows = []
    for sent in data.get("sentence") or []:
        ab = join_sentence(sent.get("word") or [])
        ch = (sent.get("chinese") or "").strip()
        if ab:
            rows.append({
                "unit": unit, "text_ab": ab, "text_ch": ch,
                "text_en": "", "ipa": "", "is_vowel": "",
            })
    return rows


def main():
    conn = get_conn()
    conn.execute(
        "DELETE FROM corpus WHERE notebook = ? AND source = ?",
        (NOTEBOOK, SOURCE)
    )
    conn.commit()

    total_dialects = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        dialect_rows = 0
        for lesson in LESSONS:
            for chapter in CHAPTERS:
                rows = fetch_one(did, lesson, chapter)
                if rows:
                    conn.executemany(
                        """INSERT INTO corpus
                           (source, notebook, dialect_id, dialect, unit,
                            text_ab, text_ch, text_en, ipa, is_vowel)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        [
                            (SOURCE, NOTEBOOK, did, dname,
                             r["unit"], r["text_ab"], r["text_ch"],
                             r["text_en"], r["ipa"], r["is_vowel"])
                            for r in rows
                        ]
                    )
                    dialect_rows += len(rows)
                time.sleep(SLEEP)
        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total_dialects}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
