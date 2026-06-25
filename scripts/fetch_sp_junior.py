"""
句型篇國中版：抓取全 42 方言 × 40 類別（8 種題型），直接寫入 corpus.db。

資料來源：
  - extension/sp_data/junior/classView.xml → 類別清單
  - extension/sp_data/junior/{did}/{cid}.xml → 各方言各類別的題目

音檔：https://klokah.tw/extension/sp_junior/sound/{did}/{tid}{typeEn}/{cno}_{odr}[_{ABCDE}].mp3
"""
import requests
import time
import xml.etree.ElementTree as ET
from common import get_conn, DIALECTS

BASE_DATA  = "https://web.klokah.tw/extension/sp_data/junior"
BASE_SOUND = "https://klokah.tw/extension/sp_junior/sound"
CLASS_XML  = f"{BASE_DATA}/classView.xml"
NOTEBOOK   = "句型篇國中版"
SOURCE     = "e樂園"
SLEEP      = 0.3

# (ab_field, ch_field, audio_suffix)
TYPE_CONFIG = {
    '1': {
        'typeEn': 'word', 'odr': 'wordOrder',
        'fields': [('wordAb', 'wordCh', '')],
    },
    '2': {
        'typeEn': 'sentence', 'odr': 'sentenceOrder',
        'fields': [
            ('sentenceAAb', 'sentenceACh', ''),
            ('sentenceBAb', 'sentenceBCh', ''),
            ('sentenceCAb', 'sentenceCCh', ''),
        ],
    },
    '3': {
        'typeEn': 'recognize', 'odr': 'recognizeOrder',
        'fields': [('recognizeAb', 'recognizeCh', '')],
    },
    '4': {
        'typeEn': 'choice_one', 'odr': 'choiceOneOrder',
        'fields': [
            ('choiceOneAAb', 'choiceOneACh', 'A'),
            ('choiceOneBAb', 'choiceOneBCh', 'B'),
            ('choiceOneCAb', 'choiceOneCCh', 'C'),
        ],
    },
    '5': {
        'typeEn': 'choice_two', 'odr': 'choiceTwoOrder',
        'fields': [
            ('choiceTwoAAb', 'choiceTwoACh', 'A'),
            ('choiceTwoBAb', 'choiceTwoBCh', 'B'),
            ('choiceTwoCAb', 'choiceTwoCCh', 'C'),
        ],
    },
    '6': {
        'typeEn': 'match', 'odr': 'matchOrder',
        'fields': [
            ('matchAAbA', 'matchAChA', 'A'), ('matchAAbB', 'matchAChB', 'A'),
            ('matchBAbA', 'matchBChA', 'B'), ('matchBAbB', 'matchBChB', 'B'),
            ('matchCAbA', 'matchCChA', 'C'), ('matchCAbB', 'matchCChB', 'C'),
            ('matchDAbA', 'matchDChA', 'D'), ('matchDAbB', 'matchDChB', 'D'),
            ('matchEAbA', 'matchEChA', 'E'), ('matchEAbB', 'matchEChB', 'E'),
        ],
    },
    '9': {
        'typeEn': 'dialogue', 'odr': 'dialogueOrder',
        'fields': [
            ('dialogueAAb', 'dialogueACh', 'A'),
            ('dialogueBAb', 'dialogueBCh', 'B'),
            ('dialogueCAb', 'dialogueCCh', 'C'),
            ('dialogueDAb', 'dialogueDCh', 'D'),
            ('dialogueEAb', 'dialogueECh', 'E'),
        ],
    },
    '10': {
        'typeEn': 'picture_talk', 'odr': 'pictureTalkOrder',
        'fields': [('pictureTalkAb', 'pictureTalkCh', '')],
    },
}


def txt(el, tag: str) -> str:
    node = el.find(tag)
    return node.text.strip() if node is not None and node.text else ''


def build_audio(did: int, tid: str, cfg: dict, cno: str, odr: str, suffix: str) -> str:
    tEN = cfg['typeEn']
    base = f"{BASE_SOUND}/{did}/{tid}{tEN}/{cno}_{odr}"
    return f"{base}_{suffix}.mp3" if suffix else f"{base}.mp3"


def load_classes() -> list[dict]:
    r = requests.get(CLASS_XML, timeout=15)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    classes = []
    for item in root.findall('item'):
        classes.append({
            'tid': txt(item, 'typeId'),
            'tch': txt(item, 'typeCh'),
            'cid': txt(item, 'classId'),
            'cch': txt(item, 'classCh'),
        })
    return classes


def fetch_class_xml(did: int, cid: str) -> list:
    url = f"{BASE_DATA}/{did}/{cid}.xml"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        return root.findall('item')
    except Exception as e:
        print(f"  SKIP did={did} cid={cid}: {e}")
        return []


def parse_items(items: list, tid: str, tch: str, cch: str, did: int) -> list[tuple]:
    cfg = TYPE_CONFIG.get(tid)
    if not cfg:
        return []

    unit = f"{tch}-{cch}"
    rows = []

    for item in items:
        cno = txt(item, 'classNo')
        odr_field = cfg.get('odr', '')
        odr = txt(item, odr_field) if odr_field else ''

        for ab_field, ch_field, suffix in cfg['fields']:
            ab = txt(item, ab_field)
            ch = txt(item, ch_field)
            if not ab:
                continue
            audio = build_audio(did, tid, cfg, cno, odr, suffix) if cno and odr else ''
            rows.append((ab, ch, audio, unit))

    return rows


def main():
    print("Loading classView.xml ...", end=" ")
    classes = load_classes()
    print(f"{len(classes)} classes")

    conn = get_conn()
    conn.execute("DELETE FROM corpus WHERE notebook = ? AND source = ?", (NOTEBOOK, SOURCE))
    conn.commit()

    total = len(DIALECTS)
    inserted = 0

    for d_idx, (did, dname) in enumerate(DIALECTS.items(), 1):
        dialect_rows = 0

        for cls in classes:
            tid, tch, cid, cch = cls['tid'], cls['tch'], cls['cid'], cls['cch']
            if tid not in TYPE_CONFIG:
                continue

            items = fetch_class_xml(did, cid)
            time.sleep(SLEEP)
            if not items:
                continue

            rows = parse_items(items, tid, tch, cch, did)
            if not rows:
                continue

            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [(SOURCE, NOTEBOOK, did, dname, r[3], r[0], r[1], '', '', '', r[2]) for r in rows],
            )
            dialect_rows += len(rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
