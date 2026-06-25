# 族語 e 樂園 教材語料擷取

> 從原住民族委員會「**族語 e 樂園**」([web.klokah.tw](https://web.klokah.tw/)) 擷取各類族語教材，彙整為單一 SQLite 語料庫，涵蓋全 **42 種原住民族語方言**、共 **336,972 筆**族語／中文對照資料。

---

## 語料庫

資料存於本地 `corpus.db`（SQLite + FTS5），不 commit 至版本庫。

```sql
CREATE TABLE corpus (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT,        -- 資料來源（e樂園）
    notebook   TEXT,        -- 教材類別
    dialect_id INTEGER,     -- 方言 ID（1–43，跳 12）
    dialect    TEXT,        -- 方言名稱
    unit       TEXT,        -- 課次／主題
    text_ab    TEXT,        -- 族語原文
    text_ch    TEXT,        -- 中文翻譯
    text_en    TEXT,        -- 英文翻譯（部分有）
    ipa        TEXT,
    is_vowel   TEXT,
    audio      TEXT         -- 音檔 URL
);
```

### 各 Notebook 筆數（2026-06-25）

| 教材類別 | 筆數 |
|---|---|
| 情境族語 | 51,834 |
| 句型篇高中版 | 44,912 |
| 族語短文 | 40,676 |
| 生活會話篇 | 32,605 |
| 閱讀書寫篇 | 30,862 |
| 句型篇國中版 | 30,354 |
| 九階 | 18,395 |
| 文化篇 | 17,184 |
| 閱讀文本 | 11,788 |
| LIMA 有聲書 | 11,601 |
| 親子溝通 | 10,256 |
| 十二階(L10-12) | 6,051 |
| 族語新聞閱讀 | 5,807 |
| 字母篇 | 4,825 |
| Wawa 遊戲 | 4,515 |
| 主題式掛圖 | 4,248 |
| Wawa 生活會話 | 2,518 |
| Wawa 單詞 | 2,482 |
| Wawa 歌謠 | 2,190 |
| 圖畫故事篇 | 2,326 |
| 歌謠篇 | 1,543 |
| **合計** | **336,972** |

---

## Scripts

所有擷取腳本位於 `scripts/`，可獨立重跑，共用 `scripts/common.py`。

| Script | 教材類別 | 方言覆蓋 |
|---|---|---|
| `fetch_alphabet.py` | 字母篇 | 42 方言 |
| `fetch_conversation.py` | 生活會話篇 | 42 方言 |
| `fetch_ninestages.py` | 九階 | 42 方言 |
| `fetch_twelve.py` | 十二階(L10-12) | 42 方言 |
| `fetch_reading.py` | 閱讀書寫篇 | 42 方言 |
| `fetch_culture.py` | 文化篇 | 42 方言 |
| `fetch_parentchild.py` | 親子溝通 | 42 方言 |
| `fetch_dialogue.py` | 情境族語 | 42 方言 |
| `fetch_essay.py` | 族語短文 | 42 方言 |
| `fetch_readingtext.py` | 閱讀文本 | 42 方言 |
| `fetch_song.py` | 歌謠篇 | 42 方言 |
| `fetch_picturestory.py` | 圖畫故事篇 | 42 方言 |
| `fetch_flipchart.py` | 主題式掛圖 | 19 方言 |
| `fetch_wawa_word.py` | Wawa 單詞 | 42 方言 |
| `fetch_wawa_game.py` | Wawa 遊戲 | 42 方言 |
| `fetch_wawa_conversation.py` | Wawa 生活會話 | 42 方言 |
| `fetch_wawa_song.py` | Wawa 歌謠 | 部分方言 |
| `fetch_lima.py` | LIMA 有聲書 | 42 方言 |
| `fetch_sp_junior.py` | 句型篇國中版 | 42 方言 |
| `fetch_sp_senior.py` | 句型篇高中版 | 42 方言 |
| `fetch_readnews.py` | 族語新聞閱讀 | 依文章方言 |

---

## 安裝與使用

```bash
pip install requests beautifulsoup4
```

```bash
# 建立 corpus.db 並初始化 schema
python scripts/common.py

# 執行任一 script（可重跑，先清除舊資料再重寫）
python scripts/fetch_dialogue.py
python scripts/fetch_sp_senior.py
# ...
```

查詢範例：

```sql
-- 查某方言所有族語句子
SELECT text_ab, text_ch FROM corpus WHERE dialect = '南勢阿美語';

-- FTS5 全文搜尋
SELECT text_ab, text_ch FROM corpus_fts WHERE corpus_fts MATCH 'misa';
```

---

## 涵蓋語言

16 族、42 種方言（ID 1–43，跳 12）：阿美語 5 種、泰雅語 6 種、賽德克語 3 種、布農語 5 種、排灣語 4 種、魯凱語 6 種、太魯閣語、噶瑪蘭語、鄒語、卡那卡那富語、拉阿魯哇語、卑南語 4 種、賽夏語、邵語、雅美語、撒奇萊雅語。

---

<sub>資料來源：原住民族委員會「族語 e 樂園」<https://web.klokah.tw/>，著作權屬原權責單位所有，本專案僅供族語學習與研究之非商業用途。</sub>
