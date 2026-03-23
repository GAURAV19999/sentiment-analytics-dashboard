# 📊 Sentiment Analytics Dashboard

> **Power BI-style Sentiment Analytics Platform built with Streamlit & Plotly**  
> Multi-method NLP analysis using TextBlob, VADER & Emoji Intelligence — with interactive KPI cards, trend analysis, and breakdown dashboards.

---

## 🚀 Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-link.streamlit.app)

---

## 🖼️ Dashboard Preview

![Sentiment Analytics Dashboard](screenshot.png)

---

## ✨ Key Features

- 📁 **Multi-format File Upload** — Supports CSV (.csv), Excel (.xlsx, .xls), UTF-8, Latin-1, CP1252
- 🧠 **3 NLP Sentiment Methods** — TextBlob, VADER, and Emoji Intelligence running in parallel
- 📊 **Power BI-style KPI Cards** — Total reviews, Positive %, Negative %, Neutral %, Emoji Avg, Confidence Score
- 📈 **Interactive Trend Analysis** — Daily/Weekly/Monthly time granularity with Rolling Mean smoothing
- 🔍 **Breakdown by Category** — 100% Stacked bar charts comparing sentiment across sources/categories
- 🌀 **Polarity Distribution Charts** — TextBlob Polarity and VADER Compound score distributions
- ⚙️ **Custom Stopwords** — Upload your own TXT stopword file or use built-in stopwords
- 🎛️ **Advanced Text Processing** — Configurable options for cleaning and preprocessing
- 📤 **Export Ready** — Analysis results available for download

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Visualization | Plotly |
| NLP — Sentiment | TextBlob, VADER (NLTK), Emoji |
| Data Processing | Pandas, NumPy |
| File Support | CSV, Excel (openpyxl, xlrd) |
| Deployment | Streamlit Cloud |

---

## ⚙️ How to Use

### Step 1 — Upload Your Data File
- Click **Browse files** or drag & drop your file
- Supported formats: `.csv`, `.xlsx`, `.xls`
- Maximum file size: 200MB
- Optionally upload a custom **stopwords TXT file**

### Step 2 — Configure Analysis
Once your file loads, you will see:

```
✅ Excel file loaded | 500 rows × 4 columns | filename.xlsx
```

Select the correct columns from the dropdowns:

| Dropdown | What to Select | Example |
|---|---|---|
| 📝 **Text Column** | Column containing review/text data | `ReviewText` |
| 🏷️ **Category Column** | Column for grouping/filtering | `Source` |
| 📅 **Date Column** (Optional) | Column with dates for trend analysis | `Date` |

### Step 3 — Start Analysis
- Click the **🚀 Start Analysis** button
- Dashboard will render KPIs, charts, and breakdowns automatically

### Step 4 — Explore Results
Navigate through the tabs:
- **Overview** — Sentiment distribution donut chart + polarity distributions
- **Trends** — Time-series sentiment trends with smoothing
- **Breakdowns** — Category-wise 100% stacked bar charts
- **Emoji Insights** — Emoji-aware sentiment intelligence
- **Advanced Analysis** — Multi-method comparison
- **Details** — Row-level data with sentiment scores

---

## 🎛️ Configuration Panel Options

| Setting | Options | Default |
|---|---|---|
| Use Built-in Stopwords | ✅ On / Off | On |
| Text Processing | Basic / Advanced | Advanced |
| Show Values on Bars | ✅ On / Off | On |
| Category Charts Mode | Percent (100% Stacked) / Counts | Percent |
| Time Granularity | Daily / Weekly / Monthly | Daily |
| Smooth Trend (Rolling Mean) | ✅ On / Off | On |
| Smoother Window | 2 – 12 | 3 |

---

## 💻 Run Locally

### Prerequisites
```bash
Python 3.8+
pip
```

### Installation

```bash
# Clone the repository
git clone https://github.com/GAURAV19999/sentiment-analytics-dashboard.git
cd sentiment-analytics-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Requirements
```txt
streamlit
pandas
numpy
plotly
textblob
vaderSentiment
nltk
openpyxl
xlrd
emoji
```

---

## 📁 Project Structure

```
sentiment-analytics-dashboard/
│
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── utils/
│   ├── sentiment.py        # TextBlob, VADER, Emoji analysis logic
│   ├── preprocessing.py    # Text cleaning and stopword handling
│   └── charts.py           # Plotly chart builders
│
└── sample_data/
    └── reviews_sample.csv  # Sample dataset to test the app
```

---

## 📊 Sample Dataset Format

Your input file should follow this structure:

| ReviewID | ReviewText | Source | Date |
|---|---|---|---|
| 1 | Great product, loved it! | Amazon | 2024-01-15 |
| 2 | Terrible experience 😞 | Google | 2024-01-16 |
| 3 | Average, nothing special | Flipkart | 2024-01-17 |

---

## 📈 KPI Definitions

| KPI | Description |
|---|---|
| **Total** | Total number of reviews analysed |
| **Positive** | Reviews with positive sentiment score + confidence % |
| **Negative** | Reviews with negative sentiment score + confidence % |
| **N/M (Neutral/Mixed)** | Reviews with neutral or mixed signals |
| **Emoji Avg** | Average emoji sentiment score across all reviews |
| **Confidence** | Overall model confidence across all 3 methods |

---

## 🔗 Connect

**Gaurav Kumar Vishvakarma**  
Senior Data Analyst & BI Developer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/gauravkumarvishwakarma/)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-green)](https://iamgaurav.netlify.app/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/GAURAV19999)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

*Built with ❤️ for data-driven insights • Emoji-aware sentiment • Interactive visuals*
