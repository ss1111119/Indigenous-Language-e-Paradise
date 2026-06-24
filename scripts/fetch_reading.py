"""
閱讀書寫篇：抓取全 42 方言 × 30 課，直接寫入 corpus.db。

資料來源：
  1. rd_data/xml/{did}/reading.xml  → 課名 + 詞彙（Ab_1..20 / Ch_1..20）
  2. rd_practice/textId.json        → {dialect_id: [tid × 30]}（全域，只抓一次）
  3. read_embed.php?tid={tid}&mode=1 → 主文章句子
"""
import requests
import time
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

BASE_XML   = "https://web.klokah.tw/extension/rd_data/xml/{}/reading.xml"
TEXTID_URL = "https://web.klokah.tw/extension/rd_practice/textId.json"
BASE_EMBED = "https://web.klokah.tw/text/read_embed.php"
BASE_SOUND = "https://web.klokah.tw/text/sound"
NOTEBOOK   = "閱讀書寫篇"
SOURCE     = "e樂園"
MAX_VOCAB  = 20
SLEEP      = 0.4


def load_textid_map() -> dict:
    r = requests.get(TEXTID_URL, timeout=15)
    r.raise_for_status()
    raw = r.json()
    return {int(k): v for k, v in raw.items()}


def fetch_vocab_from_xml(dialect_id: int) -> list[dict]:
    url = BASE_XML.format(dialect_id)
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        root = ElementTree.fromstring(r.content)
    except Exception as e:
        print(f"  SKIP XML d={dialect_id}: {e}")
        return []

    # 建 lessonNo → 課名 對照
    lessons = {}
    for item in root.findall("lesson"):
        no  = (item.findtext("lessonNo") or "").strip()
        ab  = (item.findtext("lessonAb") or "").strip()
        ch  = (item.findtext("lessonCh") or "").strip()
        lessons[no] = f"{ab}（{ch}）" if ab else ch

    rows = []
    for vocab in root.findall("vocabulary"):
        no   = (vocab.findtext("lessonNo") or "").strip()
        unit = lessons.get(no, f"課{no}")
        num  = int(vocab.findtext("vocabularyNum") or 0)
        for i in range(1, min(num, MAX_VOCAB) + 1):
            ab = (vocab.findtext(f"Ab_{i}") or "").strip()
            ch = (vocab.findtext(f"Ch_{i}") or "").strip()
            if ab:
                rows.append({
                    "unit": unit, "text_ab": ab, "text_ch": ch,
                    "text_en": "", "ipa": "", "is_vowel": "",
                })
    return rows


def fetch_article_sentences(tid: int) -> list[dict]:
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
    # 先抓 textId 對照表（一次）
    print("Loading textId.json ...", end=" ")
    textid_map = load_textid_map()
    print(f"{len(textid_map)} dialects")

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

        # 1. 詞彙（從 XML）
        vocab_rows = fetch_vocab_from_xml(did)
        time.sleep(SLEEP)

        # 2. 主文章（從 read_embed）
        tids = textid_map.get(did, [])
        article_rows_all = []
        for lesson_idx, tid in enumerate(tids, 1):
            rows = fetch_article_sentences(tid)
            unit = f"課{lesson_idx:02d}"
            for r in rows:
                r["unit"] = unit
            article_rows_all.extend(rows)
            time.sleep(SLEEP)

        all_rows = vocab_rows + article_rows_all

        if all_rows:
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname,
                     r["unit"], r["text_ab"], r["text_ch"],
                     r.get("text_en", ""), r.get("ipa", ""), r.get("is_vowel", ""), r.get("audio", ""))
                    for r in all_rows
                ]
            )
            dialect_rows = len(all_rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  vocab={len(vocab_rows)} article={len(article_rows_all)}")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
