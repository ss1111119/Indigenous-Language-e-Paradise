"""
主題式掛圖：4 課 × 19 方言，直接寫入 corpus.db。
Endpoint: https://web.klokah.tw/flipChart/json/{course}/{dialect_id}.json
  course = 1-4（身體部位 / 親屬稱謂 / 山川自然景觀 / 動物篇）
  dialect_id = 19 個有資料的方言

JSON 結構：word / dial / game / song，各為 [{ab, ch}, ...]
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_URL  = "https://web.klokah.tw/flipChart/json/{}/{}.json"
NOTEBOOK  = "主題式掛圖"
SOURCE    = "e樂園"
SLEEP     = 0.5

COURSES = {
    1: "身體部位",
    2: "親屬稱謂",
    3: "山川自然景觀",
    4: "動物篇",
}

# 只有這 19 個方言有資料
VALID_IDS = {3, 6, 13, 14, 16, 22, 23, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 43}


def fetch_one(dialect_id: int, course: int, course_name: str) -> list[dict]:
    url = BASE_URL.format(course, dialect_id)
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP course={course} d={dialect_id}: {e}")
        return []

    rows = []
    for category, items in data.items():
        unit = f"{course_name}／{category}"
        for item in items:
            ab = (item.get("ab") or "").strip()
            ch = (item.get("ch") or "").strip()
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

    valid_dialects = {k: v for k, v in DIALECTS.items() if k in VALID_IDS}
    total = len(valid_dialects)
    inserted = 0

    for d_idx, (did, dname) in enumerate(valid_dialects.items(), 1):
        dialect_rows = 0
        for course_id, course_name in COURSES.items():
            rows = fetch_one(did, course_id, course_name)
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
