"""
生活會話篇：抓取全 42 方言對話資料，直接寫入 corpus.db。
Endpoint: https://web.klokah.tw/extension/con_data/xml/{dialect_id}/conversation.xml

XML 結構：
  <lesson>  lessonId / lessonAB / lessonCH          (課題標題)
  <content> lessonId / con_scene{i} / con_someone{i} / con_AB{i} / con_CH{i}  (對話行)
  <word>    lessonId / word_AB{i} / word_CH{i}       (課題單詞)
"""
import requests
import time
from xml.etree import ElementTree
from common import get_conn, DIALECTS

BASE_URL = "https://web.klokah.tw/extension/con_data/xml/{}/conversation.xml"
NOTEBOOK = "生活會話篇"
SOURCE   = "e樂園"
MAX_LINES = 12
MAX_WORDS = 20


def fetch_dialect(dialect_id: int, dialect_name: str) -> list[dict]:
    url = BASE_URL.format(dialect_id)
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        root = ElementTree.fromstring(r.content)
    except Exception as e:
        print(f"  SKIP {dialect_id}: {e}")
        return []

    # 建立 lessonId → 課題標題 對照表
    lessons = {}
    for item in root.findall("lesson"):
        lid = (item.findtext("lessonId") or "").strip()
        lessons[lid] = {
            "ab": (item.findtext("lessonAB") or "").strip(),
            "ch": (item.findtext("lessonCH") or "").strip(),
        }

    rows = []

    # 對話行
    for item in root.findall("content"):
        lid = (item.findtext("lessonId") or "").strip()
        lesson = lessons.get(lid, {"ab": "", "ch": ""})
        unit = f"{lid}. {lesson['ab']}（{lesson['ch']}）" if lesson["ab"] else lid

        for i in range(1, MAX_LINES + 1):
            ab = (item.findtext(f"con_AB{i}") or "").strip()
            ch = (item.findtext(f"con_CH{i}") or "").strip()
            if not ab:
                break
            rows.append({
                "unit": unit, "text_ab": ab, "text_ch": ch,
                "text_en": "", "ipa": "", "is_vowel": "",
            })

    # 課題單詞
    for item in root.findall("word"):
        lid = (item.findtext("lessonId") or "").strip()
        lesson = lessons.get(lid, {"ab": "", "ch": ""})
        unit = f"{lid}. {lesson['ab']}（{lesson['ch']}）" if lesson["ab"] else lid

        for i in range(1, MAX_WORDS + 1):
            ab = (item.findtext(f"word_AB{i}") or "").strip()
            ch = (item.findtext(f"word_CH{i}") or "").strip()
            if not ab:
                break
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
    for idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        print(f"[{idx:02d}/{total}] {dname} ({did})", end="  ")
        rows = fetch_dialect(did, dname)
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
