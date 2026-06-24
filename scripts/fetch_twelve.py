"""
十二階教材（L10–12）：抓取全 42 方言，直接寫入 corpus.db。
L1–9 與九階內容相同，不重複抓取。

Endpoint: https://web.klokah.tw/twelve/php/getTextNewTwelve.php?d={did}&l={level}&c={chapter}
  level   = 10-12
  chapter = 1-10

Response JSON: title / titleCh / sentence[].ab / sentence[].chinese / sentence[].word[].ab
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_URL = "https://web.klokah.tw/twelve/php/getTextNewTwelve.php"
NOTEBOOK = "十二階(L10-12)"
SOURCE   = "e樂園"
LEVELS   = range(10, 13)   # 10, 11, 12
CHAPTERS = range(1, 11)    # 1-10
SLEEP    = 0.3


def join_sentence(words: list) -> str:
    parts = []
    for w in words:
        ab = (w.get("ab") or "").strip()
        if ab and ab not in {",", ".", "?", "!", "、", "。", "，"}:
            parts.append(ab)
    return " ".join(parts)


def fetch_one(dialect_id: int, level: int, chapter: int) -> list[dict]:
    try:
        r = requests.get(
            BASE_URL,
            params={"d": dialect_id, "l": level, "c": chapter},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP d={dialect_id} l={level} c={chapter}: {e}")
        return []

    title    = (data.get("title")   or "").strip()
    title_ch = (data.get("titleCh") or "").strip()
    unit = f"L{level}-C{chapter} {title}（{title_ch}）" if title else f"L{level}-C{chapter}"

    rows = []
    for sent in data.get("sentence") or []:
        # 長文章直接用 ab 欄位；詞彙型用 word tokens 拼
        ab = (sent.get("ab") or "").strip()
        if not ab:
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

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        dialect_rows = 0
        for level in LEVELS:
            for chapter in CHAPTERS:
                rows = fetch_one(did, level, chapter)
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
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
