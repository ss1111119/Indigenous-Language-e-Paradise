"""
閱讀文本：抓取全 42 方言 × 6 課，直接寫入 corpus.db。

資料來源：
  1. extension/readingtext/textId.json → {did: [tid × 6]}
  2. text/read_for_readingtext4.php?tid={tid}&mode=1 → 族語句子（同 read_embed 格式）
  3. extension/readingtext_data/get_data.php?did={did} → 詞彙 word_ab/word_ch + sentence_ab/sentence_ch
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn, DIALECTS

TEXTID_URL = "https://web.klokah.tw/extension/readingtext/textId.json"
BASE_ARTICLE = "https://web.klokah.tw/text/read_for_readingtext4.php"
BASE_VOCAB   = "https://web.klokah.tw/extension/readingtext_data/get_data.php"
BASE_SOUND   = "https://web.klokah.tw/text/sound"
NOTEBOOK     = "閱讀文本"
SOURCE       = "e樂園"
SLEEP        = 0.4


def load_textid_map() -> dict:
    r = requests.get(TEXTID_URL, timeout=15)
    r.raise_for_status()
    raw = r.json()
    return {int(k): v for k, v in raw.items()}


def fetch_article(tid: int) -> list[dict]:
    try:
        r = requests.get(BASE_ARTICLE, params={"tid": tid, "mode": "1"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"  SKIP article tid={tid}: {e}")
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


def fetch_vocab(did: int) -> list[dict]:
    try:
        r = requests.get(BASE_VOCAB, params={"did": did}, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  SKIP vocab did={did}: {e}")
        return []

    rows = []
    for lesson in (data.get("lesson") or {}).values():
        lesson_no = lesson.get("no", "")
        title_ab  = (lesson.get("title_ab") or "").strip()
        title_ch  = (lesson.get("title_ch") or "").strip()
        unit = f"課{lesson_no}-{title_ab}" if title_ab else f"課{lesson_no}"

        for word in (lesson.get("word") or {}).values():
            # 詞彙本身
            word_ab = (word.get("word_ab") or "").strip()
            word_ch = (word.get("word_ch") or "").strip()
            if word_ab:
                rows.append({"unit": unit, "text_ab": word_ab, "text_ch": word_ch, "audio": ""})

            # 例句
            sent_ab = (word.get("sentence_ab") or "").strip()
            sent_ch = (word.get("sentence_ch") or "").strip()
            if sent_ab:
                rows.append({"unit": unit, "text_ab": sent_ab, "text_ch": sent_ch, "audio": ""})
    return rows


def main():
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
        tids = textid_map.get(did, [])
        dialect_rows = 0

        # 1. 文章句子
        for lesson_idx, tid in enumerate(tids, 1):
            rows = fetch_article(tid)
            time.sleep(SLEEP)
            if not rows:
                continue
            unit = f"課{lesson_idx:02d}"
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname, unit,
                     r["text_ab"], r["text_ch"], "", "", "", r["audio"])
                    for r in rows
                ],
            )
            dialect_rows += len(rows)

        # 2. 詞彙 + 例句
        vocab_rows = fetch_vocab(did)
        time.sleep(SLEEP)
        if vocab_rows:
            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (SOURCE, NOTEBOOK, did, dname, r["unit"],
                     r["text_ab"], r["text_ch"], "", "", "", r["audio"])
                    for r in vocab_rows
                ],
            )
            dialect_rows += len(vocab_rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
