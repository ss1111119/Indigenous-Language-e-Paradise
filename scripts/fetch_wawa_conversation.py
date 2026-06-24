"""
Wawa 點點樂 — 生活會話：抓取全 42 方言 × 6 課，直接寫入 corpus.db。
Endpoint: https://web.klokah.tw/wawa/php/get_con_data.php?pid={pid}&did={did}
  pid = 1-6，did = 1-43（跳 12）
Response: [{order, ab, ch}, ...]
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_URL = "https://web.klokah.tw/wawa/php/get_con_data.php"
NOTEBOOK = "Wawa生活會話"
SOURCE   = "e樂園"
PIDS     = range(1, 7)
SLEEP    = 0.3


def fetch_one(dialect_id: int, pid: int) -> list[dict]:
    try:
        r = requests.get(BASE_URL, params={"pid": pid, "did": dialect_id}, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP pid={pid} did={dialect_id}: {e}")
        return []

    rows = []
    for item in data:
        ab = (item.get("ab") or "").strip()
        ch = (item.get("ch") or "").strip()
        if ab:
            rows.append({
                "unit": f"課{pid}",
                "text_ab": ab, "text_ch": ch,
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
        for pid in PIDS:
            rows = fetch_one(did, pid)
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
