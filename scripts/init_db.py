"""
建立 corpus.db schema。可重複執行（CREATE TABLE IF NOT EXISTS）。
重建 FTS5 index 請加 --rebuild 旗標。
"""
import argparse
from common import get_conn, DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS corpus (
    id         INTEGER PRIMARY KEY,
    source     TEXT NOT NULL,   -- 固定 'e樂園'
    notebook   TEXT NOT NULL,   -- '字母篇' / '生活會話篇' / ...
    dialect_id INTEGER,
    dialect    TEXT,
    unit       TEXT,            -- 字母符號 / 課次 / 主題 等
    text_ab    TEXT,            -- 族語文本（可搜尋主欄位）
    text_ch    TEXT,            -- 中文
    text_en    TEXT,            -- 英文（若有）
    ipa        TEXT,            -- IPA（字母篇）
    is_vowel   TEXT             -- 'y'/'n'（字母篇）
);

CREATE INDEX IF NOT EXISTS idx_notebook   ON corpus(notebook);
CREATE INDEX IF NOT EXISTS idx_dialect_id ON corpus(dialect_id);

CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
    text_ab,
    text_ch,
    content='corpus',
    content_rowid='id'
);
"""

TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS corpus_ai AFTER INSERT ON corpus BEGIN
    INSERT INTO corpus_fts(rowid, text_ab, text_ch)
    VALUES (new.id, new.text_ab, new.text_ch);
END;

CREATE TRIGGER IF NOT EXISTS corpus_ad AFTER DELETE ON corpus BEGIN
    INSERT INTO corpus_fts(corpus_fts, rowid, text_ab, text_ch)
    VALUES ('delete', old.id, old.text_ab, old.text_ch);
END;

CREATE TRIGGER IF NOT EXISTS corpus_au AFTER UPDATE ON corpus BEGIN
    INSERT INTO corpus_fts(corpus_fts, rowid, text_ab, text_ch)
    VALUES ('delete', old.id, old.text_ab, old.text_ch);
    INSERT INTO corpus_fts(rowid, text_ab, text_ch)
    VALUES (new.id, new.text_ab, new.text_ch);
END;
"""


def init(rebuild_fts: bool = False):
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.executescript(TRIGGERS)
    if rebuild_fts:
        conn.execute("INSERT INTO corpus_fts(corpus_fts) VALUES('rebuild')")
        print("FTS5 index rebuilt.")
    conn.commit()
    conn.close()
    print(f"DB ready: {DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Rebuild FTS5 index")
    args = parser.parse_args()
    init(rebuild_fts=args.rebuild)
