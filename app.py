import streamlit as st
import pandas as pd
import numpy as np
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib
matplotlib.use('Agg')
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
from collections import Counter
import json
from io import BytesIO
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
try:
    from nltk.corpus import stopwords as nltk_stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except:
    WORDCLOUD_AVAILABLE = False
try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except:
    LANGDETECT_AVAILABLE = False

warnings.filterwarnings('ignore')

# --- Page Configuration ---
st.set_page_config(
    page_title="📊 Sentiment Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global Plotly Defaults (Power BI-like) ---
PX_FONT = "Inter, Segoe UI, Roboto, Arial, sans-serif"
PX_PALETTE = ["#4CAF50", "#f44336", "#ff9800", "#9c27b0", "#2196F3", "#00BCD4", "#8BC34A", "#FF5722"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PX_PALETTE

SENTIMENT_COLORS = {
    "positive": "#4CAF50",
    "negative": "#f44336",
    "neutral": "#ff9800",
    "mixed": "#9c27b0"
}

def apply_powerbi_theme(fig: go.Figure, title: str = "", height: int = 420, show_legend: bool = True):
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(family=PX_FONT, size=20)),
        font=dict(family=PX_FONT, size=12),
        height=height,
        margin=dict(t=70, b=50, l=60, r=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=PX_FONT, bordercolor="#e6e9ef"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(size=12)
        ),
        showlegend=show_legend
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="#f0f2f6", zeroline=False, linecolor="#e6e9ef", ticks="outside"
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#f0f2f6", zeroline=False, linecolor="#e6e9ef", ticks="outside"
    )
    return fig

# --- Enhanced CSS (Power BI-like cards, optimized for fixed layout) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body { margin: 0; padding: 0; overflow: hidden; }
    .main { padding: 0.5rem 1rem !important; overflow-y: auto; max-height: 100vh; }
    [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 0.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }

    /* KPI Card Styling - Compact */
    .kpi-card {
        position: relative;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.85rem 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.12);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.12);
        margin-bottom: 0.5rem;
        transition: all 0.2s ease;
        overflow: hidden;
    }
    .kpi-card::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.25);
        pointer-events: none;
    }
    .kpi-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
    .kpi-positive { background: linear-gradient(135deg, #4CAF50 0%, #2e7d32 100%); }
    .kpi-negative { background: linear-gradient(135deg, #f44336 0%, #b71c1c 100%); }
    .kpi-neutral { background: linear-gradient(135deg, #ff9800 0%, #ef6c00 100%); }
    .kpi-total { background: linear-gradient(135deg, #2196F3 0%, #1565c0 100%); }

    .kpi-number {
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1;
        margin: 0 0 0.2rem 0;
        text-shadow: 0 1px 1px rgba(0,0,0,0.25);
    }
    .kpi-label {
        font-size: 0.75rem;
        opacity: 0.95;
        margin: 0;
        letter-spacing: 0.1px;
    }

    .dashboard-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
        box-shadow: 0 6px 12px rgba(0,0,0,0.10);
        border: 1px solid rgba(255,255,255,0.12);
    }
    .dashboard-title { font-size: 1.8rem; font-weight: 700; margin: 0; text-shadow: 0 1px 1px rgba(0,0,0,0.25); }
    .dashboard-subtitle { font-size: 0.85rem; opacity: 0.95; margin: 0.2rem 0 0 0; }

    .chart-container {
        background: white;
        padding: 0.8rem;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border: 1px solid #e6e9ef;
        margin-bottom: 0.5rem;
    }

    .file-upload-info {
        background: #e3f2fd;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #bbdefb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    [data-testid="stMetric"]:hover { box-shadow: 0 6px 14px rgba(0,0,0,0.10); }
    
    /* Plotly chart optimization */
    div[data-testid="stPlotlyChart"] { margin: 0 !important; padding: 0 !important; }
    
    /* Tab optimization */
    [data-testid="stTabs"] { margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# --- Stopwords ---
ENGLISH_STOPWORDS = {
    'i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','yourselves',
    'he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their',
    'theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are',
    'was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an',
    'the','and','but','if','or','because','as','until','while','of','at','by','for','with','through',
    'during','before','after','above','below','up','down','in','out','on','off','over','under','again',
    'further','then','once','here','there','when','where','why','how','all','any','both','each','few',
    'more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very',
    's','t','can','will','just','don','should','now','d','ll','m','o','re','ve','y','ain','aren','couldn',
    'didn','doesn','hadn','hasn','haven','isn','ma','mightn','mustn','needn','shan','shouldn','wasn',
    'weren','won','wouldn'
}

# --- Emoji Sentiment Mapping and Utilities (multi-emoji handling) ---
EMOJI_SENTIMENT_MAPPING = {
    '😍': 0.9, '🥰': 0.9, '🤩': 0.9, '🥳': 0.9, '❤️': 0.9, '❤': 0.9, '🎉': 0.9, '🏆': 0.9, '🥇': 0.9,
    '😊': 0.8, '😃': 0.8, '😄': 0.8, '😂': 0.8, '🤣': 0.8, '😘': 0.8, '🤗': 0.8, '🙌': 0.8,
    '💕': 0.8, '💖': 0.8, '💗': 0.8, '💘': 0.8, '💙': 0.8, '💚': 0.8, '💜': 0.8, '🧡': 0.8, '💛': 0.8,
    '🎊': 0.8, '🌟': 0.8, '🔥': 0.8, '🌈': 0.8, '🌞': 0.8, '💯': 0.8,
    '😁': 0.7, '😎': 0.7, '😇': 0.7, '👍': 0.7, '👏': 0.7, '💪': 0.7, '🤟': 0.7, '⭐': 0.7, '✨': 0.7,
    '🎁': 0.7, '💎': 0.7, '☀️': 0.7, '🤍': 0.7,
    '😆': 0.6, '😋': 0.6, '😜': 0.6, '😝': 0.6, '😛': 0.6, '😉': 0.6, '😌': 0.6, '👌': 0.6,
    '🤞': 0.6, '✌️': 0.6, '🤘': 0.6, '🎈': 0.6, '😗': 0.6, '😙': 0.6, '😚': 0.6,
    '🙂': 0.5, '👊': 0.5, '✊': 0.5,
    '🤤': 0.4, '🥺': 0.4, '🤭': 0.4, '😏': 0.3, '🤫': 0.3, '🤔': 0.2, '🙃': 0.2, '🤪': 0.3, '🤓': 0.3, '🧐': 0.1,
    '😐': 0.0, '😶': 0.0, '🤷': 0.0, '🤷‍♀️': 0.0, '🤷‍♂️': 0.0, '💭': 0.0, '👽': 0.0, '👾': 0.0, '🤖': 0.0,
    '😴': -0.2, '💤': -0.1, '🤐': -0.2, '🤨': -0.2, '😬': -0.3, '🙄': -0.4, '😒': -0.5, '😑': -0.3, '😷': -0.3, '🥲': -0.3,
    '😕': -0.4, '🙁': -0.5, '☹️': -0.5, '😞': -0.6, '😟': -0.5, '😔': -0.6, '😣': -0.5, '😖': -0.6, '😪': -0.4,
    '😓': -0.5, '🤧': -0.4, '🥵': -0.5, '🥶': -0.5,
    '😢': -0.7, '😥': -0.6, '😨': -0.7, '😰': -0.7, '😫': -0.7, '😩': -0.7, '😵': -0.7, '🤯': -0.6, '🤒': -0.6,
    '🤕': -0.6, '🤢': -0.7, '👎': -0.7,
    '😭': -0.8, '😤': -0.6, '😠': -0.8, '😈': -0.6, '👿': -0.8, '💀': -0.8, '☠️': -0.8, '🤮': -0.8, '💩': -0.8,
    '😡': -0.9, '🤬': -0.9, '💔': -0.9, '🖕': -0.9,
    '👻': -0.3, '❣️': 0.7, '💋': 0.6
}

# Emoji regex, normalization
EMOJI_REGEX = re.compile("[" 
    "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF" "\u2600-\u26FF" "\u2700-\u27BF"
    "\U0001F900-\U0001F9FF" "\U0001FA70-\U0001FAFF" "]+", flags=re.UNICODE
)
FITZPATRICK_MOD_RE = re.compile(r'[\U0001F3FB-\U0001F3FF]')
ZWJ = '\u200D'
VS16 = '\uFE0F'

def split_emoji_run(run: str):
    out, i = [], 0
    while i < len(run):
        ch = run[i]
        if i + 1 < len(run) and run[i + 1] == VS16:
            out.append(ch + VS16); i += 2
        else:
            out.append(ch); i += 1
    return out

def normalize_emoji(e: str):
    e = e.replace(VS16, '')
    e = FITZPATRICK_MOD_RE.sub('', e)
    e = e.replace(ZWJ, '')
    return e

def build_normalized_mapping(mapping: dict):
    norm = {}
    for k, v in mapping.items():
        nk = normalize_emoji(k)
        norm[nk] = v
    return norm

NORMALIZED_EMOJI_MAP = build_normalized_mapping(EMOJI_SENTIMENT_MAPPING)

def extract_emojis_display(text: str):
    if pd.isna(text) or text is None: return []
    runs = EMOJI_REGEX.findall(str(text))
    tokens = []
    for r in runs: tokens.extend(split_emoji_run(r))
    return tokens

def extract_emoji_tokens(text: str, normalize: bool = True):
    if pd.isna(text) or text is None: return []
    runs = EMOJI_REGEX.findall(str(text))
    tokens = []
    for r in runs: tokens.extend(split_emoji_run(r))
    if normalize: tokens = [normalize_emoji(t) for t in tokens if normalize_emoji(t)]
    return tokens

def analyze_emoji_sentiment(text):
    try:
        display_emojis = extract_emojis_display(text)
        norm_emojis = extract_emoji_tokens(text, normalize=True)
        if not norm_emojis: return 0.0, 0, "neutral", []
        scores = []
        pos_scores, neg_scores, neu_scores = [], [], []
        for e in norm_emojis:
            s = NORMALIZED_EMOJI_MAP.get(e, 0.0)
            scores.append(s)
            if s > 0.15: pos_scores.append(s)
            elif s < -0.15: neg_scores.append(s)
            else: neu_scores.append(s)
        emoji_count = len(norm_emojis)
        avg_score = float(np.mean(scores))
        max_score, min_score = max(scores), min(scores)
        pc, nc = len(pos_scores), len(neg_scores)
        if pc > nc and pc > 0:
            sentiment = "positive" if (avg_score > 0.05 or max_score > 0.3) else "neutral"
        elif nc > pc and nc > 0:
            sentiment = "negative" if (avg_score < -0.05 or min_score < -0.3) else "neutral"
        elif pc == nc and pc > 0:
            pos_int = np.mean(pos_scores) if pos_scores else 0
            neg_int = abs(np.mean(neg_scores)) if neg_scores else 0
            if pos_int > neg_int: sentiment = "positive"
            elif neg_int > pos_int: sentiment = "negative"
            else: sentiment = "neutral"
        else:
            if avg_score > 0.05: sentiment = "positive"
            elif avg_score < -0.05: sentiment = "negative"
            else: sentiment = "neutral"
        return avg_score, emoji_count, sentiment, display_emojis
    except Exception:
        return 0.0, 0, "neutral", []

def get_emoji_statistics(df):
    stats = {
        'total_emojis': 0, 'unique_emojis': set(), 'emoji_frequency': {},
        'avg_emojis_per_text': 0, 'texts_with_emojis': 0, 'most_common_emoji': None,
        'emoji_sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
    }
    all_emojis, tw = [], 0
    for text in df['original_text']:
        emos = extract_emoji_tokens(text, normalize=True)
        if emos:
            tw += 1
            all_emojis.extend(emos)
            stats['unique_emojis'].update(emos)
            for e in emos:
                stats['emoji_frequency'][e] = stats['emoji_frequency'].get(e, 0) + 1
    stats['total_emojis'] = len(all_emojis)
    stats['texts_with_emojis'] = tw
    stats['avg_emojis_per_text'] = len(all_emojis) / len(df) if len(df) > 0 else 0
    if stats['emoji_frequency']:
        stats['most_common_emoji'] = max(stats['emoji_frequency'].items(), key=lambda x: x[1])
    for emoji, count in stats['emoji_frequency'].items():
        sc = NORMALIZED_EMOJI_MAP.get(emoji, 0.0)
        if sc > 0.15: stats['emoji_sentiment_distribution']['positive'] += count
        elif sc < -0.15: stats['emoji_sentiment_distribution']['negative'] += count
        else: stats['emoji_sentiment_distribution']['neutral'] += count
    return stats

# --- Caching & Performance ---
@st.cache_data
def load_data_cache(uploaded_file):
    try:
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp1252')
            return df, "CSV"
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_name.endswith('.xlsx') else 'xlrd')
            return df, "Excel"
        else:
            return None, None
    except Exception as e:
        return None, None

# --- Advanced Text Processing ---
def apply_stemming(text):
    if not NLTK_AVAILABLE or not text: return text
    try:
        stemmer = PorterStemmer()
        tokens = word_tokenize(text.lower())
        return ' '.join([stemmer.stem(token) for token in tokens])
    except:
        return text

def apply_lemmatization(text):
    if not NLTK_AVAILABLE or not text: return text
    try:
        lemmatizer = WordNetLemmatizer()
        tokens = word_tokenize(text.lower())
        return ' '.join([lemmatizer.lemmatize(token) for token in tokens])
    except:
        return text

def detect_language(text):
    if not LANGDETECT_AVAILABLE or not text: return "Unknown"
    try:
        return detect(text)
    except:
        return "Unknown"

def get_text_statistics(text):
    if not text or not isinstance(text, str): 
        return {"chars": 0, "words": 0, "sentences": 0, "avg_word_len": 0}
    sentences = len(re.split(r'[.!?]+', text.strip()))
    words = len(text.split())
    chars = len(text)
    avg_word_len = chars / words if words > 0 else 0
    return {
        "chars": chars,
        "words": words,
        "sentences": sentences,
        "avg_word_len": round(avg_word_len, 2)
    }

# --- File Loading & Export ---
def load_data_file(uploaded_file):
    try:
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp1252')
            return df, "CSV"
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_name.endswith('.xlsx') else 'xlrd')
            return df, "Excel"
        else:
            st.error("❌ Unsupported file format. Please upload CSV or Excel files only.")
            return None, None
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        return None, None

def export_to_excel_formatted(df, filename="sentiment_data.xlsx"):
    """Export dataframe with formatting to Excel"""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sentiment Data', index=False)
            worksheet = writer.sheets['Sentiment Data']
            
            # Format headers
            header_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            
            for cell in worksheet[1]:
                if cell.value:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        st.error(f"Error exporting to Excel: {str(e)}")
        return None

def export_to_json(df, filename="sentiment_data.json"):
    """Export dataframe to JSON"""
    try:
        return df.to_json(orient='records', indent=2)
    except Exception as e:
        st.error(f"Error exporting to JSON: {str(e)}")
        return None

# --- Text Utilities ---
def simple_tokenize(text):
    if not text: return []
    return re.findall(r'\b\w+\b', text.lower())

def clean_text(text):
    if pd.isna(text) or text is None: return ""
    try:
        text = str(text)
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\b\d+\b', '', text)
        text = ' '.join(text.split())
        return text.strip()
    except Exception:
        return ""

def remove_stopwords(text, custom_stopwords):
    if not text or text.strip() == "": return ""
    try:
        tokens = simple_tokenize(text)
        filtered = [t for t in tokens if t not in custom_stopwords and len(t) > 2]
        return ' '.join(filtered)
    except Exception:
        return text

def analyze_textblob(text):
    try:
        if not text or text.strip() == "": return 0.0, 0.0, "neutral"
        blob = TextBlob(text)
        polarity = float(blob.polarity); subjectivity = float(blob.subjectivity)
        if polarity > 0.1: sentiment = "positive"
        elif polarity < -0.1: sentiment = "negative"
        else: sentiment = "neutral"
        return polarity, subjectivity, sentiment
    except Exception:
        return 0.0, 0.0, "neutral"

_VADER = SentimentIntensityAnalyzer()
def analyze_vader(text):
    try:
        if not text or text.strip() == "": return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}, "neutral"
        scores = _VADER.polarity_scores(text)
        c = scores['compound']
        if c >= 0.05: sent = "positive"
        elif c <= -0.05: sent = "negative"
        else: sent = "neutral"
        return scores, sent
    except Exception:
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}, "neutral"

def get_consensus_sentiment(tb, vd, em):
    votes = [tb, vd, em]
    pos = votes.count("positive"); neg = votes.count("negative"); neu = votes.count("neutral")
    if pos > neg and pos > neu: return "positive"
    if neg > pos and neg > neu: return "negative"
    if neu > pos and neu > neg: return "neutral"
    return "mixed"

def calculate_sentiment_confidence(tb_score, vd_score, em_score, consensus):
    """Calculate confidence score (0-100) for the consensus sentiment"""
    try:
        scores = [tb_score, vd_score, em_score]
        if consensus == "positive":
            pos_count = sum(1 for s in scores if s > 0)
            avg_pos = np.mean([s for s in scores if s > 0]) if pos_count > 0 else 0
            confidence = (pos_count / 3 * 50 + avg_pos * 50) if pos_count > 0 else 0
        elif consensus == "negative":
            neg_count = sum(1 for s in scores if s < 0)
            avg_neg = abs(np.mean([s for s in scores if s < 0])) if neg_count > 0 else 0
            confidence = (neg_count / 3 * 50 + avg_neg * 50) if neg_count > 0 else 0
        else:
            confidence = 50
        return min(100, max(0, confidence))
    except:
        return 50

def generate_wordcloud_image(text_series, width=800, height=400, colormap='viridis'):
    """Generate word cloud visualization"""
    if not WORDCLOUD_AVAILABLE:
        return None
    try:
        text = ' '.join(text_series.dropna().astype(str))
        if not text.strip():
            return None
        wordcloud = WordCloud(width=width, height=height, 
                            colormap=colormap, 
                            background_color='white',
                            max_words=100).generate(text)
        return wordcloud
    except:
        return None

def wordcloud_plotly(text_series, title="Word Cloud"):
    """Create plotly-based word frequency chart (alternative to word cloud)"""
    try:
        text = ' '.join(text_series.dropna().astype(str))
        if not text.strip():
            return None
        words = text.lower().split()
        word_freq = Counter(words)
        top_words = dict(word_freq.most_common(30))
        
        fig = go.Figure(go.Bar(
            y=list(top_words.keys()),
            x=list(top_words.values()),
            orientation='h',
            marker_color='#2196F3',
            marker_line=dict(color='#ffffff', width=1)
        ))
        fig.update_yaxes(autorange="reversed")
        return apply_powerbi_theme(fig, title, height=350, show_legend=False)
    except:
        return None

def load_stopwords(custom_content=None, use_default=True):
    s = set()
    if use_default: s.update(ENGLISH_STOPWORDS)
    if custom_content:
        try:
            parts = [w.strip().lower() for w in re.split(r'[,\n]+', custom_content) if w.strip()]
            s.update(parts)
        except Exception:
            pass
    return s

# --- KPI Card ---
def create_kpi_card(title, value, card_type="total", confidence=None):
    kpi_class = f"kpi-card kpi-{card_type}"
    if isinstance(value, (int, float, np.integer, np.floating)):
        value_display = f"{value:,}" if float(value).is_integer() else f"{value:,.2f}"
    else:
        value_display = str(value)
    
    confidence_html = ""
    if confidence is not None:
        conf_color = "#4CAF50" if confidence > 70 else "#ff9800" if confidence > 40 else "#f44336"
        confidence_html = f"<p style='font-size: 0.85rem; opacity: 0.8; margin-top: 0.5rem;'>Confidence: <span style='color: {conf_color}; font-weight: 600;'>{confidence:.0f}%</span></p>"
    
    return f"""
    <div class="{kpi_class}">
        <p class="kpi-number">{value_display}</p>
        <p class="kpi-label">{title}</p>
        {confidence_html}
    </div>
    """

# --- Advanced Visualizations ---
def sentiment_gauge_chart(positive_count, negative_count, neutral_count, title="Sentiment Gauge"):
    """Create gauge chart for sentiment distribution"""
    total = positive_count + negative_count + neutral_count
    if total == 0:
        return None
    
    pos_pct = (positive_count / total) * 100
    neg_pct = (negative_count / total) * 100
    neu_pct = (neutral_count / total) * 100
    
    sentiment_score = ((pos_pct - neg_pct) / 100) * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sentiment_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        delta={'reference': 0, 'suffix': " pts"},
        gauge={
            'axis': {'range': [-100, 100]},
            'bar': {'color': "#2196F3"},
            'steps': [
                {'range': [-100, -50], 'color': "#ffebee"},
                {'range': [-50, 0], 'color': "#ffcccc"},
                {'range': [0, 50], 'color': "#f1f8e9"},
                {'range': [50, 100], 'color': "#c8e6c9"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    return apply_powerbi_theme(fig, title, height=300, show_legend=False)

def sentiment_over_time_advanced(df, date_col, title, freq="D"):
    """Advanced time series with multiple metrics"""
    try:
        d = df.copy()
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
        d = d.dropna(subset=[date_col])
        d["_date"] = d[date_col].dt.to_period(freq).dt.to_timestamp()
        
        grp = d.groupby("_date").agg({
            'consensus_sentiment': lambda x: (x == 'positive').sum(),
            'vader_compound': 'mean',
            'emoji_score': 'mean'
        }).rename(columns={'consensus_sentiment': 'positive_count'})
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=grp.index, y=grp['positive_count'], name="Positive Count",
                      line=dict(color="#4CAF50", width=2.5), fill='tozeroy'),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(x=grp.index, y=grp['vader_compound'], name="VADER Score",
                      line=dict(color="#ff9800", width=2, dash="dash")),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Positive Count", secondary_y=False)
        fig.update_yaxes(title_text="Avg VADER Score", secondary_y=True)
        
        return apply_powerbi_theme(fig, title, height=300, show_legend=True)
    except:
        return None

# --- Power BI-like Charts ---
def donut_chart_with_center(values_map: dict, title: str, height=320):
    labels = list(values_map.keys()); values = list(values_map.values())
    colors = [SENTIMENT_COLORS.get(l, "#ccc") for l in labels]
    total = sum(values)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="percent", hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
    ))
    fig.add_annotation(text=f"{total:,}<br><span style='font-size:12px;color:#6b7280'>Total</span>",
                       x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#111827"))
    return apply_powerbi_theme(fig, title, height, show_legend=False)

def trend_area_100(df, date_col, title, freq="D", show_smoother=False, window=3, height=300):
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    d["_date"] = d[date_col].dt.to_period(freq).dt.to_timestamp()
    grp = d.groupby(["_date", "consensus_sentiment"]).size().reset_index(name="count")
    # Pivot to 100%
    pivot = grp.pivot(index="_date", columns="consensus_sentiment", values="count").fillna(0)
    pivot = pivot.reindex(columns=["positive","negative","neutral","mixed"], fill_value=0)
    pct = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100
    if show_smoother:
        pct = pct.rolling(window=window, min_periods=1).mean()
    fig = go.Figure()
    for col in pct.columns:
        fig.add_trace(go.Scatter(
            x=pct.index, y=pct[col], mode="lines", stackgroup="one", name=col.title(),
            line=dict(width=0.8, color=SENTIMENT_COLORS.get(col, "#ccc")),
            hovertemplate=f"<b>{col.title()}</b><br>%{{y:.1f}}% on %{{x|%Y-%m-%d}}<extra></extra>"
        ))
    fig.update_yaxes(ticksuffix="%", range=[0,100])
    fig = apply_powerbi_theme(fig, title, height, show_legend=True)
    return fig

def method_comparison_100(df, methods, names, title, height=300, show_values=False):
    data = []
    for method, name in zip(methods, names):
        counts = df[method].value_counts()
        total = counts.sum() if counts.sum() else 1
        for s in ["positive","negative","neutral"]:
            data.append({"Method": name, "Sentiment": s, "Percent": counts.get(s,0)*100/total, "Count": counts.get(s,0)})
    dd = pd.DataFrame(data)
    fig = px.bar(dd, x="Method", y="Percent", color="Sentiment",
                 color_discrete_map=SENTIMENT_COLORS, barmode="stack", text="Percent" if show_values else None)
    fig.update_traces(marker_line=dict(color="#ffffff", width=1),
                      texttemplate="%{text:.0f}%", textposition="inside")
    fig.update_yaxes(ticksuffix="%", range=[0,100])
    fig = apply_powerbi_theme(fig, title, height, show_legend=True)
    return fig

def category_breakdown_100(df, category_col, title, top_n=12, height=380, horizontal=True, show_values=False):
    counts = df[category_col].value_counts().head(top_n).index.tolist()
    sub = df[df[category_col].isin(counts)]
    cross = pd.crosstab(sub[category_col], sub["consensus_sentiment"], normalize="index")*100
    cross = cross[["positive","negative","neutral","mixed"]].fillna(0)
    cross = cross.sort_values(by="positive", ascending=True)
    cross = cross.reset_index().melt(id_vars=category_col, var_name="Sentiment", value_name="Percent")
    if horizontal:
        fig = px.bar(cross, y=category_col, x="Percent", color="Sentiment",
                     color_discrete_map=SENTIMENT_COLORS, orientation="h", text="Percent" if show_values else None)
        fig.update_xaxes(ticksuffix="%")
    else:
        fig = px.bar(cross, x=category_col, y="Percent", color="Sentiment",
                     color_discrete_map=SENTIMENT_COLORS, text="Percent" if show_values else None)
        fig.update_yaxes(ticksuffix="%")
    fig.update_traces(marker_line=dict(color="#ffffff", width=1),
                      texttemplate="%{text:.0f}%", textposition="inside")
    return apply_powerbi_theme(fig, title, height, show_legend=True)

def polarity_vs_emoji_scatter(df, title, height=300):
    df2 = df[df["emoji_count"] > 0].copy()
    if df2.empty:
        return None
    fig = px.scatter(
        df2, x="emoji_score", y="textblob_polarity",
        color="consensus_sentiment", color_discrete_map=SENTIMENT_COLORS,
        size=df2["emoji_count"].clip(upper=6), size_max=24,
        hover_data={"original_text": True, "emoji_count": True, "emoji_score": ":.2f", "textblob_polarity": ":.2f"},
        labels={"emoji_score":"Emoji Score", "textblob_polarity":"Text Polarity"}
    )
    fig.update_traces(marker=dict(line=dict(color="#ffffff", width=1)))
    return apply_powerbi_theme(fig, title, height, show_legend=True)

def polarity_distribution_combo(df, title, height=300, show_violin=True):
    fig = make_subplots(rows=1, cols=2, subplot_titles=("TextBlob Polarity", "VADER Compound"))
    fig.add_trace(go.Histogram(
        x=df['textblob_polarity'], nbinsx=30, name="TextBlob", marker_color="#2196F3",
        opacity=0.8, hovertemplate="TextBlob: %{x:.2f}<br>Count: %{y}<extra></extra>"
    ), row=1, col=1)
    fig.add_trace(go.Histogram(
        x=df['vader_compound'], nbinsx=30, name="VADER", marker_color="#ff9800",
        opacity=0.8, hovertemplate="VADER: %{x:.2f}<br>Count: %{y}<extra></extra>"
    ), row=1, col=2)
    if show_violin:
        fig.add_trace(go.Violin(
            y=df['textblob_polarity'], name="TB Violin", line_color="#1565c0", meanline_visible=True, side="positive",
            points=False, hovertemplate="TextBlob: %{y:.2f}<extra></extra>"
        ), row=1, col=1)
        fig.add_trace(go.Violin(
            y=df['vader_compound'], name="VADER Violin", line_color="#ef6c00", meanline_visible=True, side="positive",
            points=False, hovertemplate="VADER: %{y:.2f}<extra></extra>"
        ), row=1, col=2)
    fig.update_layout(barmode="overlay")
    fig.update_traces(marker_line_color="#ffffff", marker_line_width=1)
    fig = apply_powerbi_theme(fig, title, height, show_legend=False)
    return fig

def top_emojis_bar(emoji_stats, title, top_n=15, height=350):
    if not emoji_stats or not emoji_stats["emoji_frequency"]:
        return None
    items = sorted(emoji_stats["emoji_frequency"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    emojis, counts = zip(*items)
    sentiments = [("Positive" if NORMALIZED_EMOJI_MAP.get(e,0)>0.15 else "Negative" if NORMALIZED_EMOJI_MAP.get(e,0)<-0.15 else "Neutral") for e in emojis]
    colors = [SENTIMENT_COLORS.get(s.lower(), "#ccc") for s in sentiments]
    fig = go.Figure(go.Bar(
        x=list(counts), y=list(emojis), orientation="h", marker_color=colors,
        marker_line=dict(color="#ffffff", width=1),
        text=[f"{c}" for c in counts], textposition="auto",
        hovertemplate="Emoji: %{y}<br>Count: %{x}<br>Sentiment: %{customdata}<extra></extra>",
        customdata=sentiments
    ))
    fig.update_yaxes(autorange="reversed")
    return apply_powerbi_theme(fig, title, height, show_legend=False)

# --- Main Dashboard ---
def main():
    st.markdown('''
    <div class="dashboard-header">
        <h1 class="dashboard-title">📊 Sentiment Analytics</h1>
        <p class="dashboard-subtitle">Power BI–style analytics with TextBlob, VADER & Emoji Intelligence</p>
    </div>
    ''', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration Panel")
        
        # File upload
        uploaded_file = st.file_uploader("📄 Upload Data File", type=['csv', 'xlsx', 'xls'])
        st.markdown("""
        <div class="file-upload-info">
            <strong>📋 Supported Formats:</strong><br>
            • CSV (.csv) • Excel (.xlsx, .xls) • UTF-8, Latin-1, CP1252
        </div>
        """, unsafe_allow_html=True)
        
        # Stopwords
        stopwords_file = st.file_uploader("📝 Custom Stopwords (Optional)", type=['txt'])
        use_default_stopwords = st.checkbox("✅ Use Built-in Stopwords", value=True)
        
        st.markdown("---")
        st.markdown("### 🧹 Text Processing")
        with st.expander("Advanced Options", expanded=False):
            apply_stemming_opt = st.checkbox("Apply Stemming", value=False, help="Reduce words to root form")
            apply_lemma_opt = st.checkbox("Apply Lemmatization", value=False, help="Lemmatize words to base form")
            detect_lang = st.checkbox("Detect Language", value=False, help="Detect text language (requires langdetect)")
        
        st.markdown("---")
        st.markdown("### 🎛️ Chart Controls")
        show_values = st.checkbox("Show Values on Bars", value=True)
        percent_vs_count = st.radio("Category Charts Mode", ["Percent (100% Stacked)", "Counts"], index=0)
        time_granularity = st.selectbox("Time Granularity", ["Daily (D)", "Weekly (W)", "Monthly (M)"], index=0)
        smooth_trend = st.checkbox("Smooth Trend (Rolling Mean)", value=True)
        smooth_window = st.slider("Smoother Window", 2, 12, 3) if smooth_trend else 0
        
        st.markdown("---")
        st.markdown("### 📎 Notes")
        st.caption("💡 Hover over charts for interactive tooltips. Use filters to refine insights.")

    if uploaded_file is not None:
        try:
            df, file_type = load_data_file(uploaded_file)
            if df is not None:
                # Info
                c1, c2, c3 = st.columns(3)
                with c1: st.success(f"✅ {file_type} file loaded")
                with c2: st.info(f"📊 {len(df)} rows × {len(df.columns)} columns")
                with c3: st.info(f"📁 {uploaded_file.name}")
                with st.expander("👀 Data Preview", expanded=False):
                    st.dataframe(df.head(), use_container_width=True)
                    st.caption(", ".join(df.columns))

                # Config
                st.markdown("## 🔧 Analysis Configuration")
                col1, col2, col3 = st.columns(3)
                with col1: text_column = st.selectbox("📝 Text Column", df.columns)
                with col2:
                    category_options = ["None"] + list(df.columns)
                    category_column = st.selectbox("📊 Category Column", category_options)
                with col3:
                    date_candidates = ["None"] + [c for c in df.columns if re.search(r"(date|time)", c, re.IGNORECASE)]
                    date_column = st.selectbox("📅 Date Column (Optional)", date_candidates)
                    if date_column == "None": date_column = None

                custom_stopwords_content = stopwords_file.read().decode('utf-8') if stopwords_file else None
                stopwords_set = load_stopwords(custom_stopwords_content, use_default_stopwords)

                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    progress_container = st.container()
                    with progress_container:
                        pb = st.progress(0); status = st.empty()
                    try:
                        status.text("🧹 Preprocessing text data...")
                        pb.progress(15)
                        df['original_text'] = df[text_column].astype(str)
                        df['cleaned_text'] = df['original_text'].apply(clean_text)

                        status.text("🛑 Removing stopwords...")
                        pb.progress(30)
                        df['processed_text'] = df['cleaned_text'].apply(lambda x: remove_stopwords(x, stopwords_set))
                        
                        if 'apply_stemming_opt' in st.session_state or apply_stemming_opt:
                            status.text("🌿 Applying stemming...")
                            pb.progress(38)
                            df['processed_text'] = df['processed_text'].apply(apply_stemming)
                        
                        if 'apply_lemma_opt' in st.session_state or apply_lemma_opt:
                            status.text("📚 Applying lemmatization...")
                            pb.progress(42)
                            df['processed_text'] = df['processed_text'].apply(apply_lemmatization)

                        status.text("🎭 Analyzing emojis...")
                        pb.progress(45)
                        emoji_results = df['original_text'].apply(analyze_emoji_sentiment)
                        df['emoji_score']   = [r[0] for r in emoji_results]
                        df['emoji_count']   = [r[1] for r in emoji_results]
                        df['emoji_sentiment']= [r[2] for r in emoji_results]
                        df['emojis_found']  = [r[3] for r in emoji_results]

                        status.text("🔍 Running TextBlob analysis...")
                        pb.progress(65)
                        tb = df['processed_text'].apply(analyze_textblob)
                        df['textblob_polarity']     = [r[0] for r in tb]
                        df['textblob_subjectivity'] = [r[1] for r in tb]
                        df['textblob_sentiment']    = [r[2] for r in tb]

                        status.text("⚡ Running VADER analysis...")
                        pb.progress(80)
                        vd = df['processed_text'].apply(analyze_vader)
                        df['vader_compound'] = [r[0]['compound'] for r in vd]
                        df['vader_positive'] = [r[0]['pos'] for r in vd]
                        df['vader_neutral']  = [r[0]['neu'] for r in vd]
                        df['vader_negative'] = [r[0]['neg'] for r in vd]
                        df['vader_sentiment']= [r[1] for r in vd]

                        status.text("🤝 Calculating consensus...")
                        pb.progress(92)
                        df['consensus_sentiment'] = df.apply(
                            lambda row: get_consensus_sentiment(row['textblob_sentiment'], row['vader_sentiment'], row['emoji_sentiment']), axis=1
                        )
                        
                        status.text("🎯 Computing confidence scores...")
                        pb.progress(94)
                        df['sentiment_confidence'] = df.apply(
                            lambda row: calculate_sentiment_confidence(
                                row['textblob_polarity'], 
                                row['vader_compound'], 
                                row['emoji_score'],
                                row['consensus_sentiment']
                            ), axis=1
                        )

                        status.text("📊 Computing emoji statistics...")
                        pb.progress(96)
                        emoji_stats = get_emoji_statistics(df)
                        
                        status.text("📝 Computing text statistics...")
                        pb.progress(98)
                        text_stats = df['original_text'].apply(get_text_statistics)
                        df['text_length'] = text_stats.apply(lambda x: x['words'])
                        df['text_complexity'] = text_stats.apply(lambda x: x['avg_word_len'])

                        pb.progress(100); status.text("✅ Analysis completed!")
                        st.session_state['dashboard_data'] = df
                        st.session_state['text_column'] = text_column
                        st.session_state['category_column'] = category_column
                        st.session_state['date_column'] = date_column
                        st.session_state['file_type'] = file_type
                        st.session_state['emoji_stats'] = emoji_stats
                        progress_container.empty()
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        return
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            return

    # Display Dashboard
    if 'dashboard_data' in st.session_state:
        df = st.session_state['dashboard_data']
        text_column = st.session_state['text_column']
        category_column = st.session_state['category_column']
        date_column = st.session_state['date_column']
        file_type = st.session_state.get('file_type', 'Unknown')
        emoji_stats = st.session_state.get('emoji_stats', None)

        # Filters (Compact)
        st.markdown("## 🔍 Filters & Controls")
        filter_expander = st.expander("Filter Options", expanded=False)
        with filter_expander:
            fc_row1 = st.columns(5)
            with fc_row1[0]:
                sentiment_filter = st.multiselect("Sentiment",
                    options=['positive','negative','neutral','mixed'],
                    default=['positive','negative','neutral','mixed'], key="sent_filter_main")
            with fc_row1[1]:
                if category_column != "None" and category_column in df.columns:
                    opts = list(df[category_column].dropna().unique())
                    category_filter = st.multiselect("Category", options=opts, default=opts[:5] if len(opts)>5 else opts, key="cat_filter_main")
                else:
                    category_filter = None
            with fc_row1[2]:
                polarity_range = st.slider("Polarity", -1.0, 1.0, (-1.0, 1.0), step=0.1, key="polarity_main")
            with fc_row1[3]:
                emoji_count_max = int(df['emoji_count'].max()) if 'emoji_count' in df.columns else 0
                emoji_count_range = st.slider("Emoji Count", 0, emoji_count_max if emoji_count_max>0 else 10,
                                              (0, emoji_count_max if emoji_count_max>0 else 10), step=1, key="emoji_main")
            with fc_row1[4]:
                top_n_records = st.selectbox("Records", [100, 500, 1000, 5000, len(df)], index=2, key="records_main")
            
            # Advanced filters
            fc_row2 = st.columns(3)
            with fc_row2[0]:
                confidence_filter = st.slider("Confidence (%)", 0, 100, (0, 100), step=5, key="conf_main")
            with fc_row2[1]:
                text_len_max = int(df['text_length'].max()) if 'text_length' in df.columns else 100
                text_len_range = st.slider("Text Length", 0, text_len_max, (0, text_len_max), step=10, key="text_len_main")
            with fc_row2[2]:
                if 'text_complexity' in df.columns:
                    complexity_range = st.slider("Complexity", 0.0, float(df['text_complexity'].max()), 
                                                 (0.0, float(df['text_complexity'].max())), step=0.1, key="complex_main")
                else:
                    complexity_range = (0.0, 10.0)

        filtered_df = df[
            (df['consensus_sentiment'].isin(sentiment_filter)) &
            (df['textblob_polarity'] >= polarity_range[0]) &
            (df['textblob_polarity'] <= polarity_range[1]) &
            (df['emoji_count'] >= emoji_count_range[0]) &
            (df['emoji_count'] <= emoji_count_range[1]) &
            (df['sentiment_confidence'] >= confidence_filter[0]) &
            (df['sentiment_confidence'] <= confidence_filter[1]) &
            (df['text_length'] >= text_len_range[0]) &
            (df['text_length'] <= text_len_range[1]) &
            (df['text_complexity'] >= complexity_range[0]) &
            (df['text_complexity'] <= complexity_range[1])
        ].head(top_n_records)
        if category_filter and category_column != "None":
            filtered_df = filtered_df[filtered_df[category_column].isin(category_filter)]

        # KPIs (Compact)
        st.markdown("## 📊 KPIs")
        sentiment_counts = filtered_df['consensus_sentiment'].value_counts()
        k = st.columns(6)
        with k[0]: st.markdown(create_kpi_card("Total", len(filtered_df), "total"), unsafe_allow_html=True)
        with k[1]: 
            pos_conf = filtered_df[filtered_df['consensus_sentiment']=='positive']['sentiment_confidence'].mean() if len(filtered_df[filtered_df['consensus_sentiment']=='positive']) > 0 else 50
            st.markdown(create_kpi_card("Positive", sentiment_counts.get('positive', 0), "positive", pos_conf), unsafe_allow_html=True)
        with k[2]: 
            neg_conf = filtered_df[filtered_df['consensus_sentiment']=='negative']['sentiment_confidence'].mean() if len(filtered_df[filtered_df['consensus_sentiment']=='negative']) > 0 else 50
            st.markdown(create_kpi_card("Negative", sentiment_counts.get('negative', 0), "negative", neg_conf), unsafe_allow_html=True)
        with k[3]:
            neutral_mixed = sentiment_counts.get('neutral',0)+sentiment_counts.get('mixed',0)
            neu_conf = filtered_df[filtered_df['consensus_sentiment'].isin(['neutral','mixed'])]['sentiment_confidence'].mean() if len(filtered_df[filtered_df['consensus_sentiment'].isin(['neutral','mixed'])]) > 0 else 50
            st.markdown(create_kpi_card("N/M", neutral_mixed, "neutral", neu_conf), unsafe_allow_html=True)
        with k[4]:
            avg_emoji_score = filtered_df['emoji_score'].mean() if 'emoji_score' in filtered_df.columns else 0.0
            st.markdown(create_kpi_card("Emoji Avg", f"{avg_emoji_score:.2f}", "total"), unsafe_allow_html=True)
        with k[5]:
            avg_confidence = filtered_df['sentiment_confidence'].mean() if 'sentiment_confidence' in filtered_df.columns else 50.0
            st.markdown(create_kpi_card("Confidence", f"{avg_confidence:.0f}%", "total"), unsafe_allow_html=True)

        # Initialize active tab in session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 0
        
        # Tabs for Power BI-like sections
        tab_overview, tab_trends, tab_breakdown, tab_emojis, tab_advanced, tab_details = st.tabs(
            ["Overview", "Trends", "Breakdowns", "Emoji Insights", "Advanced Analysis", "Details"]
        )
        
        # Track tab interaction - this helps preserve tab state across reruns
        st.session_state.last_tab_active = True

        with tab_overview:
            # Row 1: Donut + Distribution
            ov_c1, ov_c2 = st.columns([1.2, 1])
            with ov_c1:
                fig_donut = donut_chart_with_center(sentiment_counts.to_dict(), "Sentiment Distribution")
                st.plotly_chart(fig_donut, use_container_width=True)
            with ov_c2:
                fig_pd = polarity_distribution_combo(filtered_df, "Polarity Distributions", show_violin=False)
                st.plotly_chart(fig_pd, use_container_width=True)

            # Row 2: Method Comparison
            fig_methods = method_comparison_100(
                filtered_df,
                methods=['textblob_sentiment', 'vader_sentiment', 'emoji_sentiment', 'consensus_sentiment'],
                names=['TextBlob', 'VADER', 'Emoji', 'Consensus'],
                title="Methods Comparison (100% Stacked)", show_values=show_values
            )
            st.plotly_chart(fig_methods, use_container_width=True)

        with tab_trends:
            if date_column:
                freq = {"Daily (D)": "D", "Weekly (W)": "W", "Monthly (M)": "M"}[time_granularity]
                fig_trend = trend_area_100(filtered_df, date_column, f"📆 Sentiment Trend ({time_granularity})",
                                           freq=freq, show_smoother=smooth_trend, window=smooth_window)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("ℹ️ No date column selected. Choose one in configuration to view trends.")

        with tab_breakdown:
            if category_column != "None" and category_column in filtered_df.columns:
                if percent_vs_count.startswith("Percent"):
                    fig_cat = category_breakdown_100(filtered_df, category_column, "📊 Category vs Sentiment (100%)",
                                                     top_n=12, horizontal=True, show_values=show_values)
                    st.plotly_chart(fig_cat, use_container_width=True)
                else:
                    # Counts grouped
                    counts = pd.crosstab(filtered_df[category_column], filtered_df['consensus_sentiment']).reset_index()
                    counts = counts.rename(columns={"positive":"Positive","negative":"Negative","neutral":"Neutral","mixed":"Mixed"})
                    counts = counts.sort_values(by="Positive", ascending=False).head(15)
                    counts_melt = counts.melt(id_vars=category_column, var_name="Sentiment", value_name="Count")
                    fig = px.bar(counts_melt, y=category_column, x="Count", color="Sentiment",
                                 color_discrete_map=SENTIMENT_COLORS, orientation="h",
                                 text="Count" if show_values else None)
                    fig.update_traces(marker_line=dict(color="#ffffff", width=1), textposition="auto")
                    fig = apply_powerbi_theme(fig, "📊 Category vs Sentiment (Counts)", 520, True)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No category column selected. Choose one in configuration to view breakdowns.")

        with tab_emojis:
            # Row 1: Top Emojis + Scatter
            em_c1, em_c2 = st.columns([1, 1])
            with em_c1:
                if emoji_stats:
                    fig_top_e = top_emojis_bar(emoji_stats, "Top Emojis", top_n=12)
                    if fig_top_e:
                        st.plotly_chart(fig_top_e, use_container_width=True)
                    else:
                        st.info("No emojis found")
                else:
                    st.info("No emojis found")
            with em_c2:
                fig_scatter = polarity_vs_emoji_scatter(filtered_df, "Emoji Score vs Polarity")
                if fig_scatter:
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("Not enough emoji data")

            # Row 2: Metrics
            if emoji_stats:
                m = st.columns(4)
                with m[0]: st.metric("Total Emojis", emoji_stats['total_emojis'])
                with m[1]: st.metric("Unique Emojis", len(emoji_stats['unique_emojis']))
                with m[2]: st.metric("Texts with Emojis", emoji_stats['texts_with_emojis'])
                with m[3]: st.metric("Avg Emojis/Text", f"{emoji_stats['avg_emojis_per_text']:.2f}")

        with tab_advanced:
            st.markdown("### Advanced Analytics")
            
            # Row 1: Gauge + Confidence Distribution
            adv_r1_c1, adv_r1_c2 = st.columns([1, 1])
            with adv_r1_c1:
                fig_gauge = sentiment_gauge_chart(
                    sentiment_counts.get('positive', 0),
                    sentiment_counts.get('negative', 0),
                    sentiment_counts.get('neutral', 0),
                    "Sentiment Gauge"
                )
                if fig_gauge:
                    st.plotly_chart(fig_gauge, use_container_width=True)
            with adv_r1_c2:
                fig_conf_dist = px.histogram(
                    filtered_df, x='sentiment_confidence', nbins=20,
                    title="Confidence Distribution",
                    labels={'sentiment_confidence': 'Confidence (%)'},
                    color_discrete_sequence=['#2196F3']
                )
                fig_conf_dist.update_traces(marker_line=dict(color='white', width=1))
                fig_conf_dist = apply_powerbi_theme(fig_conf_dist, "", 300)
                st.plotly_chart(fig_conf_dist, use_container_width=True)
            
            # Row 2: Word Cloud
            st.markdown("### Word Frequency")
            wc_type = st.radio("Style", ["Bar Chart", "Cloud (if available)"], horizontal=True, key="wc_type")
            
            if wc_type == "Cloud (if available)" and WORDCLOUD_AVAILABLE:
                wc_img = generate_wordcloud_image(filtered_df['processed_text'], width=600, height=300)
                if wc_img:
                    st.image(wc_img.to_array(), use_container_width=True)
                else:
                    st.info("Not enough text data for word cloud")
            else:
                fig_wc = wordcloud_plotly(filtered_df['processed_text'], "Most Frequent Words")
                if fig_wc:
                    st.plotly_chart(fig_wc, use_container_width=True)
            
            # Row 3: Confidence by Sentiment + Text Length Impact
            adv_r3_c1, adv_r3_c2 = st.columns([1, 1])
            with adv_r3_c1:
                fig_conf_sentiment = px.box(
                    filtered_df, x='consensus_sentiment', y='sentiment_confidence',
                    color='consensus_sentiment', color_discrete_map=SENTIMENT_COLORS,
                    title="Confidence by Sentiment",
                    labels={'sentiment_confidence': 'Confidence (%)', 'consensus_sentiment': 'Sentiment'}
                )
                fig_conf_sentiment.update_traces(marker_line=dict(color='white', width=1))
                fig_conf_sentiment = apply_powerbi_theme(fig_conf_sentiment, "", 300)
                st.plotly_chart(fig_conf_sentiment, use_container_width=True)
            
            with adv_r3_c2:
                fig_len_sentiment = px.scatter(
                    filtered_df, x='text_length', y='vader_compound',
                    color='consensus_sentiment', color_discrete_map=SENTIMENT_COLORS,
                    size='emoji_count', size_max=15,
                    title="Text Length vs Sentiment",
                    labels={'text_length': 'Word Count', 'vader_compound': 'VADER Score'}
                )
                fig_len_sentiment.update_traces(marker=dict(line=dict(color='white', width=0.5)))
                fig_len_sentiment = apply_powerbi_theme(fig_len_sentiment, "", 300)
                st.plotly_chart(fig_len_sentiment, use_container_width=True)

        with tab_details:
            st.markdown("### Detailed Data View")
            display_columns = [text_column, 'consensus_sentiment', 'textblob_polarity', 'vader_compound',
                               'emoji_score', 'emoji_count']
            if category_column != "None":
                display_columns.insert(1, category_column)
            if 'emojis_found' in filtered_df.columns:
                filtered_df = filtered_df.copy()
                filtered_df['emojis_display'] = filtered_df['emojis_found'].apply(lambda x: ' '.join(x) if x else '')
                display_columns.append('emojis_display')
            st.dataframe(filtered_df[display_columns].head(50), use_container_width=True, height=250)

            st.markdown("#### Export Options")
            ec = st.columns(4)
            with ec[0]:
                csv_full = filtered_df.to_csv(index=False)
                st.download_button("📊 CSV", csv_full, "sentiment_data.csv", "text/csv", use_container_width=True, key="csv_export")
            with ec[1]:
                excel_bytes = export_to_excel_formatted(filtered_df)
                if excel_bytes:
                    st.download_button("📈 Excel", excel_bytes, "sentiment_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="excel_export")
            with ec[2]:
                json_str = export_to_json(filtered_df)
                if json_str:
                    st.download_button("📄 JSON", json_str, "sentiment_data.json", "application/json", use_container_width=True, key="json_export")
            with ec[3]:
                summary_stats = pd.DataFrame({
                    'Metric': ['Total','Positive','Negative','Neutral','Mixed','Avg Polarity','Avg VADER','Avg Confidence'],
                    'Value': [len(filtered_df), sentiment_counts.get('positive',0), sentiment_counts.get('negative',0),
                              sentiment_counts.get('neutral',0), sentiment_counts.get('mixed',0),
                              f"{filtered_df['textblob_polarity'].mean():.3f}",
                              f"{filtered_df['vader_compound'].mean():.3f}",
                              f"{filtered_df['sentiment_confidence'].mean():.1f}%"]
                })
                st.download_button("📋 Stats", summary_stats.to_csv(index=False), "summary_stats.csv", "text/csv", use_container_width=True, key="stats_export")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1.25rem;'>
        <p>📊 Power BI–style Sentiment Analytics | Streamlit + Plotly</p>
        <p>Built with ❤️ for data-driven insights • Emoji-aware sentiment • Interactive visuals</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
