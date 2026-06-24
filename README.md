# 族語 e 樂園 教材資料擷取與彙整 🪶

> 一組 Jupyter Notebook，從原住民族委員會「**族語 e 樂園**」([web.klokah.tw](https://web.klokah.tw/)) 擷取並整理各類族語教材資料，涵蓋全 **42 種原住民族語方言**。

---

## 📚 收錄教材

每個 Notebook 對應族語 e 樂園的一類教材：

| Notebook | 教材類別 |
|----------|----------|
| `字母篇.ipynb` | 字母 |
| `Wawa點點樂_單詞.ipynb` | Wawa 點點樂：單詞 |
| `Wawa點點樂_歌謠.ipynb` | Wawa 點點樂：歌謠 |
| `Wawa點點樂_生活會話.ipynb` | Wawa 點點樂：生活會話 |
| `生活會話篇.ipynb` | 生活會話 |
| `歌謠篇.ipynb` | 歌謠 |
| `情境族語.ipynb` | 情境族語 |
| `主題式掛圖.ipynb` | 主題式掛圖 |
| `圖畫故事篇.ipynb` | 圖畫故事 |
| `文化篇.ipynb` | 文化 |
| `族語短文.ipynb` / `閱讀本文.ipynb` | 短文 / 閱讀本文 |
| `九階.ipynb` | 九階教材 |
| `教學模組.ipynb` | 教學模組 |
| `族語e樂園國中.ipynb` / `族語e樂園高中.ipynb` | 國中 / 高中教材 |

## 🌐 涵蓋語言

涵蓋 16 族、共 **42 種方言**（南勢阿美語、賽考利克泰雅語、卓群布農語、東排灣語、太魯閣語、雅美語、鄒語、卑南語、撒奇萊雅語……），透過族語 e 樂園各語言編號逐一擷取。

## 🛠️ 技術

- **Python / Jupyter Notebook**
- 透過 `requests` 取得官網 XML / API 資料，`BeautifulSoup`、`selenium` 處理網頁，`pandas` 整理成表格

### 安裝相依套件

```bash
pip install -r requirements.txt
```

```text
selenium==4.9.1
pandas==2.2.1
beautifulsoup4==4.12.2
webdriver-manager==4.0.1
requests==2.31.0
```

## 💡 使用方式

1. 安裝相依套件（見上）
2. 開啟對應教材類別的 Notebook
3. 依需求調整語言編號清單，執行儲存格即可擷取並整理資料

---

<sub>資料來源為原住民族委員會「族語 e 樂園」<https://web.klokah.tw/>，著作權屬原權責單位所有，本專案僅供族語學習與研究之非商業用途。</sub>
