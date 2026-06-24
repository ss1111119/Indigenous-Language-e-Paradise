"""
族語短文：抓取全 42 方言 S1/S2 短文，直接寫入 corpus.db。

流程：
  1. essay/json/ES112{did:02d}.json → S1.L1-L12, S2.L1-L12（各層 tid 陣列）
  2. essay/php/getEssay.php?tid={tid} → [{sn, ab, ch, en, img, snd}]
  音檔：https://web.klokah.tw/text/sound/{sn}.mp3
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_JSON  = "https://web.klokah.tw/essay/json/ES112{:02d}.json"
BASE_ESSAY = "https://web.klokah.tw/essay/php/getEssay.php"
BASE_SOUND = "https://web.klokah.tw/text/sound"
NOTEBOOK   = "族語短文"
SOURCE     = "e樂園"
SLEEP      = 0.3


def fetch_tid_list(did: int) -> dict:
    url = BASE_JSON.format(did)
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  SKIP ES112{did:02d}.json: {e}")
        return {}


def fetch_essay(tid: int) -> list[dict]:
    try:
        r = requests.get(BASE_ESSAY, params={"tid": tid}, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP getEssay tid={tid}: {e}")
        return []

    rows = []
    for item in data:
        ab = (item.get("ab") or "").strip()
        if not ab:
            continue
        sn = (item.get("sn") or "").strip()
        audio = f"{BASE_SOUND}/{sn}.mp3" if sn else ""
        rows.append({
            "text_ab": ab,
            "text_ch": (item.get("ch") or "").strip(),
            "text_en": (item.get("en") or "").strip(),
            "audio":   audio,
        })
    return rows


def iter_tids(data: dict):
    """依序產出 (unit, tid)，S1/S2 各 L1-L12。"""
    for section in ("S1", "S2"):
        sec = data.get(section) or {}
        for i in range(1, 13):
            level = f"L{i}"
            tids = sec.get(level) or []
            for tid in tids:
                yield f"{section}-{level}", tid


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
        data = fetch_tid_list(did)
        time.sleep(SLEEP)
        if not data:
            print(f"[{d_idx:02d}/{total}] {dname} ({did})  SKIP")
            continue

        dialect_rows = 0
        seen_tids = set()

        for unit, tid in iter_tids(data):
            if tid in seen_tids:
                continue
            seen_tids.add(tid)

            rows = fetch_essay(tid)
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
                     r["text_ab"], r["text_ch"], r["text_en"], "", "", r["audio"])
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
