# 族語 e 樂園 — 重整計畫進度

資料來源：[web.klokah.tw](https://web.klokah.tw/)　|　涵蓋 16 族 42 方言（ID 1–43，跳 12）

---

## 資料庫

| 檔案 | 說明 |
|---|---|
| `corpus.db` | SQLite + FTS5，本地執行，不 commit |
| `scripts/` | 所有 fetch script，可重跑 |

**corpus.db 目前筆數（2026-06-24）**

| Notebook | 筆數 |
|---|---|
| 情境族語 | 51,834 |
| LIMA 有聲書 | 11,601 |
| 族語短文 | 40,676 |
| 生活會話篇 | 32,605 |
| 句型篇高中版 | 44,912 |
| 句型篇國中版 | 30,354 |
| 閱讀書寫篇 | 30,862 |
| 九階 | 18,395 |
| 文化篇 | 17,184 |
| 閱讀文本 | 11,788 |
| 親子溝通 | 10,256 |
| 十二階(L10-12) | 6,051 |
| 字母篇 | 4,825 |
| 主題式掛圖 | 4,248 |
| Wawa 生活會話 | 2,518 |
| 圖畫故事篇 | 2,326 |
| Wawa 遊戲 | 4,515 |
| Wawa 單詞 | 2,482 |
| Wawa 歌謠 | 2,190 |
| 歌謠篇 | 1,543 |
| **合計** | **331,165** |

---

## Script 狀態

| Script | 教材類別 | 狀態 | 備註 |
|---|---|---|---|
| `fetch_alphabet.py` | 字母篇 | ✅ | 42 方言，4,825 rows |
| `fetch_conversation.py` | 生活會話篇 | ✅ | 42 方言，32,605 rows（含單詞） |
| `fetch_ninestages.py` | 九階 | ✅ | 42 方言 × L1–9 × C1–10 |
| `fetch_flipchart.py` | 主題式掛圖 | ✅ | 19 方言 × 4 課，2 筆 JSON 錯誤跳過 |
| `fetch_wawa_conversation.py` | Wawa 生活會話 | ✅ | 42 方言 × 6 課 |
| `fetch_wawa_song.py` | Wawa 歌謠 | ✅ | 部分方言有資料（非全 42） |
| `fetch_song.py` | 歌謠篇 | ✅ | 42 方言 × 10 首，1,543 rows |
| `fetch_twelve.py` | 十二階(L10-12) | ✅ | 42 方言 × L10–12 × C1–10，6,051 rows |
| `fetch_picturestory.py` | 圖畫故事篇 | ✅ | 42 方言 × 10 則，2,326 rows |
| `fetch_reading.py` | 閱讀書寫篇 | ✅ | 42 方言 × 30 課，30,862 rows（XML 詞彙 + read_embed 內文 + 音檔） |
| `fetch_culture.py` | 文化篇 | ✅ | 42 方言 × 30 課，17,184 rows（textId.json + read_embed 內文 + 音檔） |
| `fetch_parentchild.py` | 親子溝通 | ✅ | 42 方言 × 4 主題 × 4 小節，10,256 rows（句子 + 詞彙 + 音檔） |
| `fetch_dialogue.py` | 情境族語 | ✅ | 42 方言 S1/S2/S3，51,834 rows（族語+中文+英文+音檔） |
| `fetch_essay.py` | 族語短文 | ✅ | 42 方言 S1/S2，40,676 rows（族語+中文+英文+音檔） |
| `fetch_readingtext.py` | 閱讀文本 | ✅ | 42 方言 × 6 課，11,788 rows（文章句子 + 詞彙例句 + 音檔） |
| `fetch_wawa_word.py` | Wawa 單詞 | ✅ | 42 方言 × 6 主題，2,482 rows（Session + set_prefer_dialect POST + .showword HTML 解析）|
| `fetch_wawa_game.py` | Wawa 遊戲 | ✅ | 42 方言 × 6 主題，4,515 rows（get_game_data.php JSON，問題+答對+答錯回應+音檔）|
| `fetch_lima.py` | LIMA 有聲書 | ✅ | 42 方言 × 7 課 × 4 模式，11,601 rows（vocabulary+story+conversation+question+音檔）|
| `fetch_sp_junior.py` | 句型篇國中版 | ✅ | 42 方言 × 40 類別（8 題型），30,354 rows（XML 解析，含詞彙/句型/對話/配合題）|
| `fetch_sp_senior.py` | 句型篇高中版 | ✅ | 42 方言 × 47 類別（8 題型），44,912 rows（XML 解析，含選擇題三/唸唸看等高中特有題型）|

---

## API Endpoint 對照

| 教材類別 | Endpoint | 格式 |
|---|---|---|
| 字母篇 | `https://web.klokah.tw/extension/ab_data/xml/{did}/alphabet.xml` | XML |
| 生活會話篇 | `https://web.klokah.tw/extension/con_data/xml/{did}/conversation.xml` | XML |
| 九階 | `https://web.klokah.tw/ninew/php/getTextNew.php?d={did}&l={l}&c={c}` | JSON |
| 主題式掛圖 | `https://web.klokah.tw/flipChart/json/{course}/{did}.json` | JSON |
| Wawa 生活會話 | `https://web.klokah.tw/wawa/php/get_con_data.php?pid={pid}&did={did}` | JSON |
| Wawa 歌謠 | `https://web.klokah.tw/wawa/php/get_song_data.php?pid={pid}&did={did}` | JSON |
| 歌謠篇（歌名） | `https://web.klokah.tw/extension/song_data/xml/{did}/song.xml` | XML |
| 歌謠篇（歌詞） | `https://web.klokah.tw/extension/song_practice/index.php?d={did}&s={song}&view=lyric` → `text/read_embed.php?tid={tid}&mode=1` | HTML |
| 圖畫故事篇（故事名） | `https://web.klokah.tw/extension/ps_data/xml/{did}/story.xml` | XML |
| 圖畫故事篇（故事文） | `https://web.klokah.tw/extension/ps_practice/index.php?d={did}&l={story}&view=story` → `read_embed.php?tid={tid}&mode=1` | HTML |
| 閱讀書寫篇（詞彙+課名） | `https://web.klokah.tw/extension/rd_data/xml/{did}/reading.xml` | XML |
| 閱讀書寫篇（tid 對照） | `https://web.klokah.tw/extension/rd_practice/textId.json` | JSON |
| 閱讀書寫篇（文章） | `read_embed.php?tid={tid}&mode=1` | HTML |
| 文化篇（tid 對照） | `https://web.klokah.tw/extension/cu_practice/textId.json` | JSON |
| 文化篇（內文） | `read_embed.php?tid={tid}&mode=1` | HTML |
| 親子溝通（tid 對照） | `https://web.klokah.tw/parent-child/json/tid.json` | JSON |
| 親子溝通（內文） | `read_embed.php?tid={tid}&mode=1` | HTML |
| 情境族語（tid 清單） | `https://web.klokah.tw/dialogue/json/SN112{did:02d}.json` | JSON |
| 情境族語（對話） | `https://web.klokah.tw/dialogue/php/getDiaData.php?tid={tid}` | JSON |
| 族語短文（tid 清單） | `https://web.klokah.tw/essay/json/ES112{did:02d}.json` | JSON |
| 族語短文（短文） | `https://web.klokah.tw/essay/php/getEssay.php?tid={tid}` | JSON |
| Wawa 單詞 | `https://web.klokah.tw/wawa/word.php?pid={pid}` + session cookie | HTML |

---

## 方言 ID 對照

| ID | 方言 | ID | 方言 |
|---|---|---|---|
| 1 | 南勢阿美語 | 23 | 東排灣語 |
| 2 | 秀姑巒阿美語 | 24 | 北排灣語 |
| 3 | 海岸阿美語 | 25 | 中排灣語 |
| 4 | 馬蘭阿美語 | 26 | 南排灣語 |
| 5 | 恆春阿美語 | 27 | 東魯凱語 |
| 6 | 賽考利克泰雅語 | 28 | 霧台魯凱語 |
| 7 | 澤敖利泰雅語 | 29 | 大武魯凱語 |
| 8 | 汶水泰雅語 | 30 | 多納魯凱語 |
| 9 | 萬大泰雅語 | 31 | 茂林魯凱語 |
| 10 | 四季泰雅語 | 32 | 萬山魯凱語 |
| 11 | 宜蘭澤敖利泰雅語 | 33 | 太魯閣語 |
| 13 | 賽夏語 | 34 | 噶瑪蘭語 |
| 14 | 邵語 | 35 | 鄒語 |
| 15 | 都達賽德克語 | 36 | 卡那卡那富語 |
| 16 | 德固達雅賽德克語 | 37 | 拉阿魯哇語 |
| 17 | 德鹿谷賽德克語 | 38 | 南王卑南語 |
| 18 | 卓群布農語 | 39 | 知本卑南語 |
| 19 | 卡群布農語 | 40 | 西群卑南語 |
| 20 | 丹群布農語 | 41 | 建和卑南語 |
| 21 | 巒群布農語 | 42 | 雅美語 |
| 22 | 郡群布農語 | 43 | 撒奇萊雅語 |

> ID 12 不存在。主題式掛圖僅 19 個方言有資料（ID 3,6,13,14,16,22,23,28,30,31,32,33,34,35,36,37,38,42,43）。
