"""
族語新聞閱讀：抓取全部 1,587 篇文章的族語/中文句子對，直接寫入 corpus.db。

流程：
  1. GET readnews/php/getNews.php?d=0&t=&p={page} → 分頁取得所有文章 meta
  2. GET readnews/read.php?tid={id} → BeautifulSoup 解析 .rn-read-sentence-part
     每個 part 含一對 Ab（族語）+ Ch（中文）句子

方言由文章 meta 的 did/dch 欄位決定（非系統性覆蓋全 42 方言）。
"""
import requests
import time
from bs4 import BeautifulSoup
from common import get_conn

BASE_URL   = "https://web.klokah.tw/readnews"
NEWS_API   = f"{BASE_URL}/php/getNews.php"
READ_URL   = f"{BASE_URL}/read.php"
NOTEBOOK   = "族語新聞閱讀"
SOURCE     = "e樂園"
SLEEP      = 0.4


def get_all_articles() -> list[dict]:
    articles = []
    page = 1
    while True:
        try:
            r = requests.get(NEWS_API, params={"d": 0, "t": "", "p": page}, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  SKIP page {page}: {e}")
            break

        for item in data.get("data", []):
            articles.append({
                "id":      item.get("id", ""),
                "did":     int(item.get("did", 0)),
                "dch":     item.get("dch", ""),
                "titleAb": item.get("titleAb", "").strip(),
                "titleCh": item.get("titleCh", "").strip(),
                "time":    item.get("time", ""),
            })

        if data.get("last") == "y":
            break
        page += 1
        time.sleep(SLEEP)

    return articles


def fetch_sentences(tid: str) -> list[tuple[str, str]]:
    try:
        r = requests.get(READ_URL, params={"tid": tid}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"  SKIP tid={tid}: {e}")
        return []

    pairs = []
    for part in soup.select(".rn-read-sentence-part"):
        ab_el = part.select_one(".rn-read-sentence.Ab")
        ch_el = part.select_one(".rn-read-sentence.Ch")
        if not ab_el or not ch_el:
            continue
        ab = " ".join(w.get_text(strip=True) for w in ab_el.find_all("div", class_="word") if w.get_text(strip=True))
        if not ab:
            ab = ab_el.get_text(strip=True)
        ch = ch_el.get_text(strip=True)
        if ab:
            pairs.append((ab, ch))
    return pairs


def main():
    print("Fetching article list ...", end=" ", flush=True)
    articles = get_all_articles()
    print(f"{len(articles)} articles")

    conn = get_conn()
    conn.execute("DELETE FROM corpus WHERE notebook = ? AND source = ?", (NOTEBOOK, SOURCE))
    conn.commit()

    inserted = 0
    total = len(articles)

    for idx, art in enumerate(articles, 1):
        tid    = art["id"]
        did    = art["did"]
        dname  = art["dch"]
        unit   = art["titleCh"] or art["titleAb"]

        # 標題本身存一筆
        rows = []
        if art["titleAb"]:
            rows.append((art["titleAb"], art["titleCh"], "", unit))

        # 句子對
        pairs = fetch_sentences(tid)
        time.sleep(SLEEP)
        for ab, ch in pairs:
            rows.append((ab, ch, "", unit))

        if not rows:
            continue

        conn.executemany(
            """INSERT INTO corpus
               (source, notebook, dialect_id, dialect, unit,
                text_ab, text_ch, text_en, ipa, is_vowel, audio)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [(SOURCE, NOTEBOOK, did, dname, r[3], r[0], r[1], "", "", "", r[2]) for r in rows],
        )
        inserted += len(rows)

        if idx % 100 == 0 or idx == total:
            conn.commit()
            print(f"[{idx:4d}/{total}] inserted={inserted:,}")

    conn.commit()
    conn.close()
    print(f"\nDone: {inserted} rows inserted ({NOTEBOOK})")


if __name__ == "__main__":
    main()
