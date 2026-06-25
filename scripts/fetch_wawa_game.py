"""
Wawa 遊戲：抓取全 42 方言 × 6 主題的遊戲問答，直接寫入 corpus.db。

API：GET wawa/php/get_game_data.php?pid={pid}&did={did}
回傳：[{q_ab, q_ch, right_ab, right_ch, wrong_ab, wrong_ch}]

每題存三筆：
  - 問題（q_ab / q_ch），audio = {pid}-{qnum}-1.mp3
  - 答對回應（right_ab / right_ch），audio = {pid}-{qnum}-2.mp3
  - 答錯回應（wrong_ab / wrong_ch），audio = {pid}-{qnum}-3.mp3
"""
import requests
import time
from common import get_conn, DIALECTS

BASE_API   = "https://web.klokah.tw/wawa/php/get_game_data.php"
BASE_SOUND = "https://web.klokah.tw/wawa/sound/game"
NOTEBOOK   = "Wawa 遊戲"
SOURCE     = "e樂園"
SLEEP      = 0.4

THEMES = {
    1: "我長大了",
    2: "我的家庭真可愛",
    3: "歡樂慶豐收",
    4: "部落真好玩",
    5: "123大風吹",
    6: "山豬飛鼠來點名",
}


def fetch_game(pid: int, did: int) -> list[dict]:
    try:
        r = requests.get(BASE_API, params={"pid": pid, "did": did}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  SKIP pid={pid} did={did}: {e}")
        return []


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

        for pid, theme in THEMES.items():
            data = fetch_game(pid, did)
            time.sleep(SLEEP)
            if not data:
                continue

            unit = f"pid{pid}-{theme}"
            rows = []
            for qnum, item in enumerate(data, 1):
                audio_q     = f"{BASE_SOUND}/{did}/{pid}-{qnum}-1.mp3"
                audio_right = f"{BASE_SOUND}/{did}/{pid}-{qnum}-2.mp3"
                audio_wrong = f"{BASE_SOUND}/{did}/{pid}-{qnum}-3.mp3"

                q_ab = item.get("q_ab", "").strip()
                q_ch = item.get("q_ch", "").strip()
                r_ab = item.get("right_ab", "").strip()
                r_ch = item.get("right_ch", "").strip()
                w_ab = item.get("wrong_ab", "").strip()
                w_ch = item.get("wrong_ch", "").strip()

                if q_ab:
                    rows.append((SOURCE, NOTEBOOK, did, dname, unit, q_ab, q_ch, "", "", "", audio_q))
                if r_ab:
                    rows.append((SOURCE, NOTEBOOK, did, dname, unit, r_ab, r_ch, "", "", "", audio_right))
                if w_ab:
                    rows.append((SOURCE, NOTEBOOK, did, dname, unit, w_ab, w_ch, "", "", "", audio_wrong))

            conn.executemany(
                """INSERT INTO corpus
                   (source, notebook, dialect_id, dialect, unit,
                    text_ab, text_ch, text_en, ipa, is_vowel, audio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
            dialect_rows += len(rows)

        conn.commit()
        inserted += dialect_rows
        print(f"[{d_idx:02d}/{total}] {dname} ({did})  {dialect_rows} rows")

    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
