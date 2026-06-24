"""
字母篇：抓取全 42 方言字母資料，直接寫入 corpus.db。
Endpoint: https://web.klokah.tw/extension/ab_data/xml/{dialect_id}/alphabet.xml
"""
import requests
import time
from xml.etree import ElementTree
from common import get_conn, DIALECTS

BASE_URL = "https://web.klokah.tw/extension/ab_data/xml/{}/alphabet.xml"
NOTEBOOK = "字母篇"
SOURCE = "e樂園"


def fetch_dialect(dialect_id: int) -> list[dict]:
    url = BASE_URL.format(dialect_id)
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        root = ElementTree.fromstring(r.content)
    except Exception as e:
        print(f"  SKIP {dialect_id}: {e}")
        return []

    rows = []
    for item in root.findall("alphabet"):
        symbol  = (item.findtext("alphabetSymbol") or "").strip()
        ipa     = (item.findtext("ipa")             or "").strip()
        is_vowel= (item.findtext("isVowel")         or "").strip()
        count   = int(item.findtext("wordnumber") or 0)
        for i in range(1, count + 1):
            word    = (item.findtext(f"word{i}")    or "").strip()
            meaning = (item.findtext(f"meaning{i}") or "").strip()
            english = (item.findtext(f"english{i}") or "").strip()
            if word:
                rows.append({
                    "unit": symbol, "text_ab": word,
                    "text_ch": meaning, "text_en": english,
                    "ipa": ipa, "is_vowel": is_vowel,
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
    for idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        print(f"[{idx:02d}/{total}] {dname} ({did})", end="  ")
        rows = fetch_dialect(did)
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
        conn.commit()
        inserted += len(rows)
        print(f"{len(rows)} rows")
        time.sleep(1)

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
