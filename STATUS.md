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
| 生活會話篇 | 32,605 |
| 九階 | 18,395 |
| 字母篇 | 4,825 |
| 主題式掛圖 | 4,248 |
| Wawa 生活會話 | 2,518 |
| Wawa 歌謠 | 2,190 |
| 歌謠篇 | 1,543 |
| 十二階(L10-12) | 6,051 |
| **合計** | **72,375** |

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
| — | Wawa 單詞 | ⏳ 待處理 | 需 Selenium + session cookie |

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
