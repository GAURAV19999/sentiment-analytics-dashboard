# ===============================================
# AUTOMATED LIBRARY INSTALLATION
# ===============================================

import subprocess
import sys
import importlib
import os

def install_and_import_package(package_name, import_name=None, pip_name=None):
    """Install and import a package with error handling"""
    if import_name is None:
        import_name = package_name
    if pip_name is None:
        pip_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is already installed")
    except ImportError:
        print(f"📦 Installing {package_name}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pip_name, 
                "--quiet", "--disable-pip-version-check"
            ])
            print(f"✅ {package_name} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package_name}: {e}")
            return False
    return True

def setup_environment():
    """Setup the complete environment with all required packages"""
    print("🚀 Setting up environment...")
    
    required_packages = [
        ('streamlit', 'streamlit', 'streamlit>=1.28.0'),
        ('pandas', 'pandas', 'pandas>=1.5.0'),
        ('numpy', 'numpy', 'numpy>=1.24.0'),
        ('textblob', 'textblob', 'textblob>=0.17.1'),
        ('vaderSentiment', 'vaderSentiment', 'vaderSentiment>=3.3.2'),
        ('wordcloud', 'wordcloud', 'wordcloud>=1.9.2'),
        ('matplotlib', 'matplotlib', 'matplotlib>=3.7.0'),
        ('plotly', 'plotly', 'plotly>=5.15.0'),
        ('seaborn', 'seaborn', 'seaborn>=0.12.0'),
        ('PIL', 'PIL', 'Pillow>=9.0.0')
    ]
    
    success_count = 0
    total_packages = len(required_packages)
    
    for package_name, import_name, pip_name in required_packages:
        if install_and_import_package(package_name, import_name, pip_name):
            success_count += 1
    
    try:
        import textblob
        print("📚 Downloading TextBlob corpora...")
        try:
            subprocess.run([
                sys.executable, "-m", "textblob.download_corpora"
            ], capture_output=True, text=True, timeout=60)
            print("✅ TextBlob corpora downloaded")
        except:
            print("⚠️ TextBlob corpora download skipped (may already exist)")
    except ImportError:
        pass
    
    print(f"🎉 Setup complete! {success_count}/{total_packages} packages ready")
    
    if success_count < total_packages:
        print("⚠️ Some packages failed to install. The app may not work properly.")
    
    return success_count == total_packages

# Run environment setup
if __name__ == "__main__" or "streamlit" in sys.modules:
    setup_success = setup_environment()
    if not setup_success:
        print("❌ Environment setup failed. Please install packages manually.")

# ===============================================
# MAIN APPLICATION IMPORTS
# ===============================================

import streamlit as st
import pandas as pd
import numpy as np
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from textwrap import dedent
import warnings
warnings.filterwarnings('ignore')

# ===============================================
# PAGE CONFIGURATION
# ===============================================

st.set_page_config(
    page_title="📊 Sentiment Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================
# BRAND SETTINGS (Customize)
# ===============================================

BRAND = {
    "name": "InsightPulse",
    "logo_url": "",   # Add your logo URL to show it in the header
    "primary": "#6C63FF",
    "secondary": "#00D1C1",
    "accent_green": "#4CAF50",
    "accent_red": "#EF4444",
    "accent_orange": "#F59E0B",
    "accent_purple": "#9C27B0"
}

# ===============================================
# GLOBAL PLOTLY THEME (Power BI-like)
# ===============================================

PX_FONT = "Inter, Segoe UI, Roboto, Arial, sans-serif"
PX_PALETTE = [BRAND["accent_green"], BRAND["accent_red"], BRAND["accent_orange"], BRAND["accent_purple"], "#2196F3", "#00BCD4", "#8BC34A", "#FF5722"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PX_PALETTE
CURRENT_TEMPLATE = "plotly_white"

SENTIMENT_COLORS = {
    "positive": BRAND["accent_green"],
    "negative": BRAND["accent_red"],
    "neutral": BRAND["accent_orange"],
    "mixed": BRAND["accent_purple"]
}

def apply_powerbi_theme(fig: go.Figure, title: str = "", height: int = 420, show_legend: bool = True):
    fig.update_layout(template=CURRENT_TEMPLATE)
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(family=PX_FONT, size=20)),
        font=dict(family=PX_FONT, size=12),
        height=height,
        margin=dict(t=70, b=50, l=60, r=30),
        paper_bgcolor="white" if CURRENT_TEMPLATE == "plotly_white" else None,
        plot_bgcolor="white" if CURRENT_TEMPLATE == "plotly_white" else None,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=PX_FONT, bordercolor="#e6e9ef"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        showlegend=show_legend
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f2f6", zeroline=False, linecolor="#e6e9ef", ticks="outside")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f2f6", zeroline=False, linecolor="#e6e9ef", ticks="outside")
    return fig

def apply_runtime_theme(theme_choice: str):
    """Apply theme at runtime (Plotly + CSS)."""
    global CURRENT_TEMPLATE
    CURRENT_TEMPLATE = "plotly_white" if theme_choice == "Light" else "plotly_dark"
    px.defaults.template = CURRENT_TEMPLATE
    if CURRENT_TEMPLATE == "plotly_dark":
        st.markdown(dedent("""
        <style>
            body, .main > div { background-color: #0f172a; }
            .dashboard-header {
                background: linear-gradient(90deg, #0b1220 0%, #0f172a 100%) !important;
                border-color: rgba(255,255,255,0.12) !important;
            }
            .chart-container, .metric-card, .file-upload-info, .filter-section {
                background: #111827 !important;
                border: 1px solid #1f2937 !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.35) !important;
                color: #e5e7eb !important;
            }
            .kpi-card {
                border-color: rgba(255,255,255,0.15) !important;
                box-shadow: 0 10px 22px rgba(0,0,0,0.35), 0 4px 10px rgba(0,0,0,0.25) !important;
            }
            .kpi-number, .kpi-label { color: #f3f4f6 !important; }
            [data-testid="stMetric"] {
                background: #111827 !important;
                border: 1px solid #1f2937 !important;
                color: #e5e7eb !important;
            }
        </style>
        """), unsafe_allow_html=True)

# ===============================================
# CSS (Power BI look for cards/containers)
# ===============================================

st.markdown(dedent(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .main > div {{ padding: 1rem 2rem; }}
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .kpi-card {{
        position: relative;
        background: linear-gradient(135deg, {BRAND["primary"]} 0%, {BRAND["secondary"]} 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.12);
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.15), 0 4px 10px rgba(0, 0, 0, 0.10);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
        overflow: hidden;
    }}
    .kpi-card::after {{
        content: "";
        position: absolute; inset: 0; border-radius: inherit;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.25);
        pointer-events: none;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18), 0 8px 12px rgba(0, 0, 0, 0.12);
        border-color: rgba(0,0,0,0.18);
    }}
    .kpi-positive {{ background: linear-gradient(135deg, {BRAND["accent_green"]} 0%, #2e7d32 100%); border-color: rgba(46,125,50,0.45); }}
    .kpi-negative {{ background: linear-gradient(135deg, {BRAND["accent_red"]} 0%, #b71c1c 100%); border-color: rgba(183,28,28,0.45); }}
    .kpi-neutral  {{ background: linear-gradient(135deg, {BRAND["accent_orange"]} 0%, #ef6c00 100%); border-color: rgba(239,108,0,0.45); }}
    .kpi-total    {{ background: linear-gradient(135deg, #2196F3 0%, #1565c0 100%); border-color: rgba(21,101,192,0.45); }}

    .kpi-number {{ font-size: 2.35rem; font-weight: 700; line-height: 1; margin: 0 0 0.35rem 0; text-shadow: 0 1px 1px rgba(0,0,0,0.25); }}
    .kpi-label  {{ font-size: 0.95rem; opacity: 0.95; margin: 0; letter-spacing: 0.2px; }}

    .dashboard-header {{
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.12);
        display: flex; align-items: center; gap: 1rem;
    }}
    .brand-logo {{ width: 40px; height: 40px; border-radius: 8px; background: white; display: inline-flex;
                  align-items: center; justify-content: center; overflow: hidden; }}
    .brand-title {{ font-size: 1.1rem; font-weight: 600; opacity: 0.95; margin: 0; }}
    .dashboard-title {{ font-size: 1.6rem; font-weight: 700; margin: 0; text-shadow: 0 1px 1px rgba(0,0,0,0.25); }}
    .dashboard-subtitle {{ font-size: 0.95rem; opacity: 0.95; margin: 0.25rem 0 0 0; }}

    .metric-card, .chart-container {{
        background: white; padding: 1.25rem; border-radius: 12px; box-shadow: 0 6px 16px rgba(0,0,0,0.10);
        border: 1px solid #e6e9ef; margin-bottom: 1rem;
    }}

    .filter-section {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #e6e9ef; }}
    .install-status {{ background: #e8f5e8; padding: 1rem; border-radius: 8px; border: 1px solid #c8e6c9; margin-bottom: 1rem; }}

    [data-testid="stMetric"] {{
        background: #ffffff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 0.85rem 1rem; box-shadow: 0 6px 16px rgba(0,0,0,0.10);
    }}
    [data-testid="stMetric"]:hover {{ box-shadow: 0 10px 22px rgba(0,0,0,0.12); }}

    .brand-line {{ display: flex; align-items: center; gap: .75rem; }}
</style>
"""), unsafe_allow_html=True)

# ===============================================
# STOPWORDS
# ===============================================

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

# ===============================================
# AUTHENTICATION
# ===============================================

def check_password():
    """Returns True if the user has correct credentials."""
    def password_entered():
        try:
            if (
                st.session_state.get("username") == st.secrets.get("auth", {}).get("username")
                and st.session_state.get("password") == st.secrets.get("auth", {}).get("password")
            ):
                st.session_state["password_correct"] = True
                if "password" in st.session_state: del st.session_state["password"]
                if "username" in st.session_state: del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
        except Exception:
            st.session_state["password_correct"] = True
            if "password" in st.session_state: del st.session_state["password"]
            if "username" in st.session_state: del st.session_state["username"]

    try:
        if "auth" not in st.secrets:
            return True
    except:
        return True

    if "password_correct" not in st.session_state:
        header_html = f'''
<div class="dashboard-header">
    <div class="brand-line">
        {f'<div class="brand-logo"><img src="{BRAND["logo_url"]}" style="width:100%;height:100%;object-fit:cover"/></div>' if BRAND["logo_url"] else ''}
        <div>
            <h1 class="dashboard-title">🔐 Secure Access Required</h1>
            <p class="dashboard-subtitle">Please enter your credentials to access {BRAND["name"]}</p>
        </div>
    </div>
</div>
'''
        st.markdown(dedent(header_html), unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Username", on_change=password_entered, key="username")
            st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        header_html = '''
<div class="dashboard-header">
    <div class="brand-line">
        <div>
            <h1 class="dashboard-title">🔐 Secure Access Required</h1>
            <p class="dashboard-subtitle">Invalid credentials. Try again.</p>
        </div>
    </div>
</div>
'''
        st.markdown(dedent(header_html), unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Username", on_change=password_entered, key="username")
            st.text_input("Password", type="password", on_change=password_entered, key="password")
            st.error("❌ Invalid credentials")
        return False
    else:
        return True

# ===============================================
# EMOJI SENTIMENT + STATS
# ===============================================

EMOJI_SENTIMENT_MAPPING = {
    # Positive/Negative mapping omitted here for brevity in this comment block; full mapping below:
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
    """Enhanced emoji sentiment analysis with proper multi-emoji handling."""
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

# ===============================================
# TEXT/ANALYSIS UTILITIES
# ===============================================

def simple_tokenize(text):
    if not text: return []
    return re.findall(r'\b\w+\b', str(text).lower())

def clean_text(text):
    if pd.isna(text) or text is None: return ""
    try:
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r"[^\w\s']", ' ', text)
        text = re.sub(r'\b\d+\b', '', text)
        text = ' '.join(text.split())
        return text.strip()
    except Exception:
        return ""

def remove_stopwords(text, custom_stopwords):
    if not text or text.strip() == "": return ""
    try:
        tokens = simple_tokenize(text)
        filtered_tokens = [t for t in tokens if t not in custom_stopwords and len(t) > 2]
        return ' '.join(filtered_tokens)
    except Exception:
        return text

def analyze_textblob(text):
    try:
        if not text or text.strip() == "": return 0.0, 0.0, "neutral"
        blob = TextBlob(text)
        polarity = float(blob.polarity)
        subjectivity = float(blob.subjectivity)
        if polarity > 0.1: sentiment = "positive"
        elif polarity < -0.1: sentiment = "negative"
        else: sentiment = "neutral"
        return polarity, subjectivity, sentiment
    except Exception:
        return 0.0, 0.0, "neutral"

def analyze_vader(text):
    try:
        if not text or text.strip() == "": return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}, "neutral"
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        c = scores['compound']
        if c >= 0.05: sent = "positive"
        elif c <= -0.05: sent = "negative"
        else: sent = "neutral"
        return scores, sent
    except Exception:
        return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}, "neutral"

def get_consensus_sentiment(textblob_sent, vader_sent, emoji_sent):
    sentiments = [textblob_sent, vader_sent, emoji_sent]
    pos = sentiments.count("positive"); neg = sentiments.count("negative"); neu = sentiments.count("neutral")
    if pos > neg and pos > neu: return "positive"
    if neg > pos and neg > neu: return "negative"
    if neu > pos and neu > neg: return "neutral"
    return "mixed"

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

# ===============================================
# VISUALS
# ===============================================

def create_kpi_card(title, value, card_type="total"):
    kpi_class = f"kpi-card kpi-{card_type}"
    try:
        value_display = f"{value:,}"
    except:
        value_display = str(value)
    return f"""
    <div class="{kpi_class}">
        <p class="kpi-number">{value_display}</p>
        <p class="kpi-label">{title}</p>
    </div>
    """

def donut_chart_with_center(values_map: dict, title: str, height=420):
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

def trend_area_100(df, date_col, title, freq="D", show_smoother=False, window=3, height=420):
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    d["_date"] = d[date_col].dt.to_period(freq).dt.to_timestamp()
    grp = d.groupby(["_date", "consensus_sentiment"]).size().reset_index(name="count")
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
    return apply_powerbi_theme(fig, title, height, show_legend=True)

def method_comparison_100(df, methods, names, title, height=420, show_values=False):
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
    return apply_powerbi_theme(fig, title, height, show_legend=True)

def category_breakdown_100(df, category_col, title, top_n=12, height=520, horizontal=True, show_values=False):
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

def polarity_vs_emoji_scatter(df, title, height=420):
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

def polarity_distribution_combo(df, title, height=420, show_violin=True):
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
    return apply_powerbi_theme(fig, title, height, show_legend=False)

def top_emojis_bar(emoji_stats, title, top_n=15, height=520):
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

def positive_rate_gauge(positive_rate: float, title="Positive Rate", height=240):
    val = max(0, min(100, positive_rate))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'suffix': '%', 'font': {'size': 28}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#9aa0a6"},
            'bar': {'color': SENTIMENT_COLORS['positive']},
            'steps': [
                {'range': [0, 33],  'color': "#fee2e2"},
                {'range': [33, 66], 'color': "#fff7ed"},
                {'range': [66, 100],'color': "#dcfce7"}
            ],
            'threshold': {'line': {'color': "#111827", 'width': 3}, 'thickness': 0.75, 'value': val}
        },
        title={'text': title, 'font': {'size': 16}}
    ))
    return apply_powerbi_theme(fig, "", height, show_legend=False)

# ===============================================
# MAIN DASHBOARD
# ===============================================

def main():
    global CURRENT_TEMPLATE
    if not check_password():
        st.stop()

    # Header (dedented so HTML renders, not as code)
    header_html = f'''
<div class="dashboard-header">
    <div class="brand-line">
        {f'<div class="brand-logo"><img src="{BRAND["logo_url"]}" style="width:100%;height:100%;object-fit:cover"/></div>' if BRAND["logo_url"] else ''}
        <div>
            <div class="brand-title">{BRAND["name"]}</div>
            <h1 class="dashboard-title">📊 Sentiment Analytics Dashboard</h1>
            <p class="dashboard-subtitle">Market-ready, Power BI–style analytics with TextBlob, VADER, and Emoji Intelligence</p>
        </div>
    </div>
</div>
'''
    st.markdown(dedent(header_html), unsafe_allow_html=True)

    if 'setup_success' in globals() and setup_success:
        st.markdown(dedent('<div class="install-status">✅ All required libraries are installed and ready!</div>'), unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration Panel")
        st.markdown("### 🎨 Theme & Chart Settings")
        theme_choice = st.radio("Theme", ["Light", "Dark"], index=0, horizontal=True)
        apply_runtime_theme(theme_choice)
        base_height = st.slider("Default Chart Height", 360, 700, 420, step=10)

        st.markdown("### 📁 Data Upload")
        uploaded_file = st.file_uploader("📄 Upload CSV File", type=['csv'])

        st.markdown("### 🛑 Stopwords Configuration")
        stopwords_file = st.file_uploader("📝 Custom Stopwords File (Optional)", type=['txt'])
        custom_stopwords_input = st.text_area("Manual Stopwords Entry", placeholder="word1, word2, word3...")
        use_default_stopwords = st.checkbox("✅ Use Built-in English Stopwords", value=True)

        st.markdown("---")
        st.markdown("### 🔍 Text Search")
        search_text = st.text_input("Contains (case-insensitive)", value="")

        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.info(f"Python: {sys.version.split()[0]}")
        st.info(f"Streamlit: {st.__version__}")

    if uploaded_file is not None:
        try:
            with st.spinner("📂 Loading data..."):
                df = pd.read_csv(uploaded_file)
            st.success(f"✅ Data loaded successfully! Shape: {df.shape}")

            with st.expander("👀 Data Preview", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Total Rows", df.shape[0])
                with col2: st.metric("Total Columns", df.shape[1])
                with col3: st.metric("Missing Values", df.isnull().sum().sum())

            st.markdown("## 🔧 Analysis Configuration")
            config_cols = st.columns(4)
            with config_cols[0]:
                text_column = st.selectbox("📝 Text Column", df.columns)
            with config_cols[1]:
                category_options = ["None"] + list(df.columns)
                category_column = st.selectbox("📊 Category Column (Optional)", category_options)
            with config_cols[2]:
                date_options = ["None"] + [col for col in df.columns if any(k in col.lower() for k in ['date','time','created','timestamp'])]
                date_column = st.selectbox("📅 Date Column (Optional)", date_options)
                if date_column == "None": date_column = None
            with config_cols[3]:
                analysis_sample = st.selectbox("📊 Analysis Sample Size", [1000, 5000, 10000, 25000, len(df)], index=1)

            custom_stopwords_content = None
            if stopwords_file is not None:
                custom_stopwords_content = stopwords_file.read().decode('utf-8')
            elif custom_stopwords_input.strip():
                custom_stopwords_content = custom_stopwords_input
            stopwords_set = load_stopwords(custom_stopwords_content, use_default_stopwords)

            with st.expander("🔍 Stopwords Preview", expanded=False):
                st.info(f"Total stopwords loaded: {len(stopwords_set)}")
                st.caption(", ".join(list(stopwords_set)[:30]) + ("..." if len(stopwords_set) > 30 else ""))

            st.markdown("---")

            chip_cols = st.columns(5)
            b_all = chip_cols[0].button("All", use_container_width=True)
            b_pos = chip_cols[1].button("Positive", use_container_width=True)
            b_neg = chip_cols[2].button("Negative", use_container_width=True)
            b_neu = chip_cols[3].button("Neutral", use_container_width=True)
            b_mix = chip_cols[4].button("Mixed", use_container_width=True)
            if b_all: st.session_state["quick_filter"] = "All"
            if b_pos: st.session_state["quick_filter"] = "Positive"
            if b_neg: st.session_state["quick_filter"] = "Negative"
            if b_neu: st.session_state["quick_filter"] = "Neutral"
            if b_mix: st.session_state["quick_filter"] = "Mixed"
            if "quick_filter" not in st.session_state:
                st.session_state["quick_filter"] = "All"
            st.caption(f"Active Quick Filter: {st.session_state['quick_filter']}")

            if st.button("🚀 Start Sentiment Analysis", type="primary", use_container_width=True):
                if len(df) > analysis_sample:
                    df_analysis = df.head(analysis_sample)
                    st.warning(f"⚠️ Analyzing first {analysis_sample:,} rows out of {len(df):,} total rows.")
                else:
                    df_analysis = df.copy()

                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                try:
                    status_text.text("🧹 Step 1/6: Preprocessing text data...")
                    progress_bar.progress(10)
                    df_analysis['original_text'] = df_analysis[text_column].astype(str)
                    df_analysis['cleaned_text'] = df_analysis['original_text'].apply(clean_text)
                    df_analysis['processed_text'] = df_analysis['cleaned_text'].apply(lambda x: remove_stopwords(x, stopwords_set))

                    status_text.text("🎭 Step 2/6: Analyzing emojis...")
                    progress_bar.progress(30)
                    emoji_results = df_analysis['original_text'].apply(analyze_emoji_sentiment)
                    df_analysis['emoji_score']    = [r[0] for r in emoji_results]
                    df_analysis['emoji_count']    = [r[1] for r in emoji_results]
                    df_analysis['emoji_sentiment']= [r[2] for r in emoji_results]
                    df_analysis['emojis_found']   = [r[3] for r in emoji_results]

                    status_text.text("🔍 Step 3/6: Running TextBlob sentiment analysis...")
                    progress_bar.progress(50)
                    textblob_results = df_analysis['processed_text'].apply(analyze_textblob)
                    df_analysis['textblob_polarity'] = [r[0] for r in textblob_results]
                    df_analysis['textblob_subjectivity'] = [r[1] for r in textblob_results]
                    df_analysis['textblob_sentiment'] = [r[2] for r in textblob_results]

                    status_text.text("⚡ Step 4/6: Running VADER sentiment analysis...")
                    progress_bar.progress(65)
                    vader_results = df_analysis['processed_text'].apply(analyze_vader)
                    df_analysis['vader_compound'] = [r[0]['compound'] for r in vader_results]
                    df_analysis['vader_positive'] = [r[0]['pos'] for r in vader_results]
                    df_analysis['vader_neutral']  = [r[0]['neu'] for r in vader_results]
                    df_analysis['vader_negative'] = [r[0]['neg'] for r in vader_results]
                    df_analysis['vader_sentiment']= [r[1] for r in vader_results]

                    status_text.text("🤝 Step 5/6: Calculating consensus sentiment...")
                    progress_bar.progress(80)
                    df_analysis['consensus_sentiment'] = df_analysis.apply(
                        lambda row: get_consensus_sentiment(row['textblob_sentiment'], row['vader_sentiment'], row['emoji_sentiment']),
                        axis=1
                    )

                    status_text.text("📊 Step 6/6: Computing emoji statistics...")
                    progress_bar.progress(95)
                    emoji_stats = get_emoji_statistics(df_analysis)

                    progress_bar.progress(100)
                    status_text.text("✅ Analysis completed successfully!")

                    st.session_state['dashboard_data'] = df_analysis
                    st.session_state['text_column'] = text_column
                    st.session_state['category_column'] = category_column
                    st.session_state['date_column'] = date_column
                    st.session_state['stopwords_count'] = len(stopwords_set)
                    st.session_state['emoji_stats'] = emoji_stats

                    import time; time.sleep(0.5)
                    progress_container.empty()
                    st.success("🎉 Ready! Explore insights below.")
                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    st.error("Please check your data format and try again.")
                    return

        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            st.error("Please make sure your file is a valid CSV format.")
            return

    # Display
    if 'dashboard_data' in st.session_state:
        df = st.session_state['dashboard_data']
        text_column = st.session_state['text_column']
        category_column = st.session_state['category_column']
        date_column = st.session_state['date_column']
        emoji_stats = st.session_state.get('emoji_stats', None)

        st.markdown("---")
        st.markdown("## 🔍 Advanced Filters")

        fc1 = st.columns(6)
        with fc1[0]:
            sentiment_filter = st.multiselect("Consensus Sentiment", options=['positive','negative','neutral','mixed'],
                                              default=['positive','negative','neutral','mixed'])
            quick = st.session_state.get("quick_filter", "All")
            if quick != "All":
                mapq = {"Positive":["positive"],"Negative":["negative"],"Neutral":["neutral"],"Mixed":["mixed"]}
                sentiment_filter = mapq.get(quick, sentiment_filter)
        with fc1[1]:
            if category_column != "None" and category_column in df.columns:
                opts = list(df[category_column].dropna().unique())
                category_filter = st.multiselect("Category Filter", options=opts, default=opts[:10] if len(opts)>10 else opts)
            else:
                category_filter = None
                st.selectbox("Category Filter", ["No category column selected"], disabled=True)
        with fc1[2]:
            polarity_range = st.slider("TextBlob Polarity Range", -1.0, 1.0, (-1.0, 1.0), step=0.1)
        with fc1[3]:
            vader_range = st.slider("VADER Compound Range", -1.0, 1.0, (-1.0, 1.0), step=0.1)
        with fc1[4]:
            emoji_count_max = int(df['emoji_count'].max()) if 'emoji_count' in df.columns else 0
            emoji_count_range = st.slider("Emoji Count", 0, emoji_count_max if emoji_count_max>0 else 10,
                                          (0, emoji_count_max if emoji_count_max>0 else 10), step=1)
        with fc1[5]:
            if st.button("♻️ Reset Filters", use_container_width=True):
                st.session_state["quick_filter"] = "All"
                st.experimental_rerun()

        fc2 = st.columns(4)
        with fc2[0]:
            subjectivity_range = st.slider("Subjectivity Range", 0.0, 1.0, (0.0, 1.0), step=0.1)
        with fc2[1]:
            if date_column:
                try:
                    df[date_column] = pd.to_datetime(df[date_column])
                    min_date = df[date_column].min().date()
                    max_date = df[date_column].max().date()
                    date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                except:
                    date_range = None
                    st.selectbox("Date Range", ["Invalid date format"], disabled=True)
            else:
                date_range = None
                st.selectbox("Date Range", ["No date column selected"], disabled=True)
        with fc2[2]:
            top_n_records = st.selectbox("Records to Display", [100, 500, 1000, 5000, 10000, len(df)], index=2)
        with fc2[3]:
            text_length_filter = st.slider("Text Length Filter", 0,
                                           int(df[text_column].str.len().max()) if not df[text_column].str.len().isna().all() else 1000,
                                           value=(0, int(df[text_column].str.len().max()) if not df[text_column].str.len().isna().all() else 1000))

        # Apply filters
        filtered_df = df.copy()
        if 'original_text' in filtered_df.columns and st.session_state.get('stopwords_count', 0) is None:
            st.session_state['stopwords_count'] = 0
        if 'original_text' in filtered_df.columns and search_text:
            filtered_df = filtered_df[filtered_df['original_text'].str.contains(search_text, case=False, na=False)]

        if sentiment_filter:
            filtered_df = filtered_df[filtered_df['consensus_sentiment'].isin(sentiment_filter)]
        if category_filter and category_column != "None":
            filtered_df = filtered_df[filtered_df[category_column].isin(category_filter)]
        filtered_df = filtered_df[
            (filtered_df['textblob_polarity'] >= polarity_range[0]) &
            (filtered_df['textblob_polarity'] <= polarity_range[1]) &
            (filtered_df['vader_compound'] >= vader_range[0]) &
            (filtered_df['vader_compound'] <= vader_range[1]) &
            (filtered_df['textblob_subjectivity'] >= subjectivity_range[0]) &
            (filtered_df['textblob_subjectivity'] <= subjectivity_range[1])
        ]
        if date_range and date_column and len(date_range) == 2:
            try:
                filtered_df = filtered_df[
                    (filtered_df[date_column].dt.date >= date_range[0]) &
                    (filtered_df[date_column].dt.date <= date_range[1])
                ]
            except:
                pass
        text_lengths = filtered_df[text_column].str.len()
        filtered_df = filtered_df[(text_lengths >= text_length_filter[0]) & (text_lengths <= text_length_filter[1])]
        if 'emoji_count' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['emoji_count'] >= emoji_count_range[0]) &
                (filtered_df['emoji_count'] <= emoji_count_range[1])
            ]

        if len(filtered_df) > top_n_records:
            filtered_df = filtered_df.head(top_n_records)
            st.info(f"📊 Displaying first {top_n_records:,} records out of {len(df):,} total filtered records")

        # Summary & KPIs
        st.markdown("### 📈 Filter Summary")
        fcs = st.columns(5)
        with fcs[0]: st.metric("Total Records", f"{len(df):,}")
        with fcs[1]: st.metric("Filtered Records", f"{len(filtered_df):,}")
        with fcs[2]:
            filter_percentage = (len(filtered_df) / len(df) * 100) if len(df) > 0 else 0
            st.metric("Filter Efficiency", f"{filter_percentage:.1f}%")
        with fcs[3]: st.metric("Stopwords Used", f"{st.session_state.get('stopwords_count', 0):,}")
        with fcs[4]:
            pos_rate = (filtered_df['consensus_sentiment'].eq('positive').mean()*100) if len(filtered_df)>0 else 0
            st.metric("Positive Rate", f"{pos_rate:.1f}%")

        st.markdown("## 📊 Key Performance Indicators")
        if len(filtered_df) > 0:
            sentiment_counts = filtered_df['consensus_sentiment'].value_counts()
            kpi = st.columns(6)
            with kpi[0]: st.markdown(create_kpi_card("Total Records", len(filtered_df), "total"), unsafe_allow_html=True)
            with kpi[1]: st.markdown(create_kpi_card("Positive", sentiment_counts.get('positive', 0), "positive"), unsafe_allow_html=True)
            with kpi[2]: st.markdown(create_kpi_card("Negative", sentiment_counts.get('negative', 0), "negative"), unsafe_allow_html=True)
            with kpi[3]:
                neutral_mixed = sentiment_counts.get('neutral', 0) + sentiment_counts.get('mixed', 0)
                st.markdown(create_kpi_card("Neutral/Mixed", neutral_mixed, "neutral"), unsafe_allow_html=True)
            with kpi[4]:
                avg_emoji_score = filtered_df['emoji_score'].mean() if 'emoji_score' in filtered_df.columns else 0.0
                st.markdown(create_kpi_card("Avg Emoji Score", f"{avg_emoji_score:.3f}", "total"), unsafe_allow_html=True)
            with kpi[5]:
                fig_g = positive_rate_gauge(pos_rate, "Positive Rate", height=220)
                st.plotly_chart(fig_g, use_container_width=True)

            # Tabs
            tabs = st.tabs(["Overview", "Trends", "Breakdowns", "Emoji Insights", "Details"])

            with tabs[0]:
                c1, c2 = st.columns(2)
                with c1:
                    fig_donut = donut_chart_with_center(sentiment_counts.to_dict(), "📊 Consensus Sentiment Distribution", height=base_height)
                    st.plotly_chart(fig_donut, use_container_width=True)
                with c2:
                    fig_pd = polarity_distribution_combo(filtered_df, "📊 Polarity Distributions", height=base_height, show_violin=True)
                    st.plotly_chart(fig_pd, use_container_width=True)

                fig_methods = method_comparison_100(
                    filtered_df,
                    methods=['textblob_sentiment', 'vader_sentiment', 'emoji_sentiment', 'consensus_sentiment'],
                    names=['TextBlob', 'VADER', 'Emoji', 'Consensus'],
                    title="📈 Methods Comparison (100% Stacked)", show_values=True, height=base_height
                )
                st.plotly_chart(fig_methods, use_container_width=True)

            with tabs[1]:
                if date_column:
                    freq_choice = st.selectbox("Granularity", ["Daily (D)","Weekly (W)","Monthly (M)"], index=0)
                    smoothing = st.checkbox("Smooth Trend (Rolling Mean)", value=True)
                    window = st.slider("Smoother Window", 2, 12, 3) if smoothing else 0
                    freq = {"Daily (D)":"D", "Weekly (W)":"W", "Monthly (M)":"M"}[freq_choice]
                    fig_trend = trend_area_100(filtered_df, date_column, f"📆 Sentiment Trend ({freq_choice})",
                                               freq=freq, show_smoother=smoothing, window=window, height=base_height)
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("ℹ️ No date column selected. Choose one in configuration to view trends.")

            with tabs[2]:
                if category_column != "None" and category_column in filtered_df.columns:
                    mode = st.radio("Category Chart Mode", ["Percent (100% Stacked)","Counts"], horizontal=True)
                    if mode.startswith("Percent"):
                        fig_cat = category_breakdown_100(filtered_df, category_column, "📊 Category vs Sentiment (100%)",
                                                         top_n=12, horizontal=True, show_values=True, height=base_height+100)
                        st.plotly_chart(fig_cat, use_container_width=True)
                    else:
                        counts = pd.crosstab(filtered_df[category_column], filtered_df['consensus_sentiment']).reset_index()
                        counts = counts.rename(columns={"positive":"Positive","negative":"Negative","neutral":"Neutral","mixed":"Mixed"})
                        counts = counts.sort_values(by="Positive", ascending=False).head(15)
                        counts_melt = counts.melt(id_vars=category_column, var_name="Sentiment", value_name="Count")
                        fig = px.bar(counts_melt, y=category_column, x="Count", color="Sentiment",
                                     color_discrete_map=SENTIMENT_COLORS, orientation="h",
                                     text="Count")
                        fig.update_traces(marker_line=dict(color="#ffffff", width=1), textposition="auto")
                        fig = apply_powerbi_theme(fig, "📊 Category vs Sentiment (Counts)", base_height+100, True)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ No category column selected. Choose one in configuration to view breakdowns.")

            with tabs[3]:
                ec = st.columns(2)
                with ec[0]:
                    if emoji_stats:
                        fig_top_e = top_emojis_bar(emoji_stats, "🏆 Top Emojis Used", top_n=15, height=base_height+100)
                        if fig_top_e:
                            st.plotly_chart(fig_top_e, use_container_width=True)
                        else:
                            st.info("No emojis found.")
                    else:
                        st.info("No emojis found.")
                with ec[1]:
                    fig_scatter = polarity_vs_emoji_scatter(filtered_df, "🎯 Emoji Score vs Text Polarity", height=base_height)
                    if fig_scatter:
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.info("Not enough emoji data for scatter.")
                if emoji_stats:
                    m = st.columns(5)
                    with m[0]: st.metric("Total Emojis", emoji_stats['total_emojis'])
                    with m[1]: st.metric("Unique Emojis", len(emoji_stats['unique_emojis']))
                    with m[2]: st.metric("Texts with Emojis", emoji_stats['texts_with_emojis'])
                    with m[3]: st.metric("Avg Emojis/Text", f"{emoji_stats['avg_emojis_per_text']:.2f}")
                    with m[4]:
                        mc = emoji_stats['most_common_emoji'][0] if emoji_stats['most_common_emoji'] else "N/A"
                        st.metric("Most Used Emoji", mc)
                    if emoji_stats['emoji_frequency']:
                        emoji_df = pd.DataFrame([
                            {"Emoji": e, "Frequency": c, "Sentiment_Score": NORMALIZED_EMOJI_MAP.get(e, 0.0),
                             "Sentiment": "Positive" if NORMALIZED_EMOJI_MAP.get(e,0)>0.15 else
                                          "Negative" if NORMALIZED_EMOJI_MAP.get(e,0)<-0.15 else "Neutral"}
                            for e, c in emoji_stats['emoji_frequency'].items()
                        ]).sort_values("Frequency", ascending=False)
                        st.download_button("📥 Download Emoji Analysis", emoji_df.to_csv(index=False),
                                           "emoji_analysis.csv", "text/csv", use_container_width=True)

            with tabs[4]:
                st.markdown("### 📋 Filtered Data Preview")
                available_columns = list(filtered_df.columns)
                default_columns = [text_column, 'consensus_sentiment', 'textblob_polarity', 'vader_compound', 'emoji_score', 'emoji_count']
                if category_column != "None":
                    default_columns.insert(1, category_column)
                if date_column:
                    default_columns.insert(-1, date_column)
                display_columns = st.multiselect("Select columns to display:", available_columns,
                                                 default=[c for c in default_columns if c in available_columns])
                if display_columns:
                    show_rows = st.slider("Number of rows to display:", 10, min(500, len(filtered_df)), 50)
                    display_df = filtered_df[display_columns].head(show_rows).copy()
                    if 'emojis_found' in filtered_df.columns and 'emojis_display' not in display_df.columns:
                        display_df['emojis_display'] = filtered_df['emojis_found'].apply(lambda x: ' '.join(x) if x else '')
                    st.dataframe(display_df, use_container_width=True, height=400)
                    csv_data = filtered_df[display_columns].to_csv(index=False)
                    st.download_button("📥 Download Displayed Data", csv_data,
                                       f"sentiment_analysis_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                       "text/csv", use_container_width=True)
                else:
                    st.warning("Please select at least one column to display")

                st.markdown("### 📈 Statistical Summary")
                if len(filtered_df) > 0:
                    numerical_cols = ['textblob_polarity', 'textblob_subjectivity', 'vader_compound', 
                                      'vader_positive', 'vader_neutral', 'vader_negative', 'emoji_score']
                    summary_stats = filtered_df[[c for c in numerical_cols if c in filtered_df.columns]].describe()
                    st.dataframe(summary_stats, use_container_width=True)
                else:
                    st.warning("No data available for statistical analysis")

                st.markdown("### ⚖️ Model Comparison")
                if len(filtered_df) > 0:
                    agreement_data = (filtered_df['textblob_sentiment'] == filtered_df['vader_sentiment']).sum()
                    total_records = len(filtered_df)
                    agreement_rate = (agreement_data / total_records * 100) if total_records > 0 else 0
                    ac = st.columns(3)
                    with ac[0]: st.metric("Model Agreement", f"{agreement_data:,}")
                    with ac[1]: st.metric("Agreement Rate", f"{agreement_rate:.1f}%")
                    with ac[2]: st.metric("Disagreement", f"{total_records - agreement_data:,}")

                    fig_score_comparison = go.Figure()
                    fig_score_comparison.add_trace(go.Histogram(x=filtered_df['textblob_polarity'], name='TextBlob Polarity', opacity=0.7, nbinsx=30))
                    fig_score_comparison.add_trace(go.Histogram(x=filtered_df['vader_compound'], name='VADER Compound', opacity=0.7, nbinsx=30))
                    fig_score_comparison.update_layout(title="TextBlob vs VADER Score Distribution", xaxis_title="Score", yaxis_title="Frequency", barmode='overlay', height=400, font=dict(family="Inter"))
                    st.plotly_chart(fig_score_comparison, use_container_width=True)

                st.markdown("### 📥 Export")
                ec = st.columns(3)
                with ec[0]:
                    csv_full = filtered_df.to_csv(index=False)
                    st.download_button("📊 Download Full Dataset", csv_full,
                                       f"sentiment_analysis_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                       "text/csv", use_container_width=True)
                with ec[1]:
                    if len(filtered_df) > 0:
                        sentiment_counts = filtered_df['consensus_sentiment'].value_counts()
                        summary_data = {
                            'Metric': ['Total Records','Positive Count','Negative Count','Neutral Count','Mixed Count',
                                       'Positive Rate (%)','Negative Rate (%)','Neutral Rate (%)',
                                       'Average Polarity','Average Subjectivity','Average VADER Score'],
                            'Value': [len(filtered_df),
                                      sentiment_counts.get('positive',0),
                                      sentiment_counts.get('negative',0),
                                      sentiment_counts.get('neutral',0),
                                      sentiment_counts.get('mixed',0),
                                      round(sentiment_counts.get('positive',0)/len(filtered_df)*100,2) if len(filtered_df)>0 else 0,
                                      round(sentiment_counts.get('negative',0)/len(filtered_df)*100,2) if len(filtered_df)>0 else 0,
                                      round(sentiment_counts.get('neutral',0)/len(filtered_df)*100,2) if len(filtered_df)>0 else 0,
                                      round(filtered_df['textblob_polarity'].mean(),4),
                                      round(filtered_df['textblob_subjectivity'].mean(),4),
                                      round(filtered_df['vader_compound'].mean(),4)]
                        }
                        summary_df = pd.DataFrame(summary_data)
                        st.download_button("📈 Download Summary Statistics", summary_df.to_csv(index=False),
                                           f"sentiment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                           "text/csv", use_container_width=True)
                with ec[2]:
                    if category_column != "None" and category_column in filtered_df.columns:
                        cb = pd.crosstab(filtered_df[category_column], filtered_df['consensus_sentiment'])
                        st.download_button("📊 Download Category Breakdown", cb.to_csv(),
                                           f"category_breakdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                           "text/csv", use_container_width=True)
                    else:
                        st.caption("No category selected.")

    else:
        st.markdown(dedent(f"""
        ## 👋 Welcome to {BRAND["name"]}
        
        Upload your CSV, configure stopwords, select text/date/category columns, and start analysis.
        Features include TextBlob + VADER + Emoji sentiment, interactive Power BI–style visuals, and exports.
        """))
        st.markdown("### 📋 Sample Data Format")
        sample_data = pd.DataFrame({
            'text': [
                'I love this product! It works great. 😊',
                'This is terrible, worst purchase ever. 😡',
                'The service was okay, nothing special. 😐',
                'Amazing quality and fast delivery! ❤️🎉'
            ],
            'category': ['Electronics', 'Electronics', 'Service', 'Electronics'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'rating': [5, 1, 3, 5]
        })
        st.dataframe(sample_data, use_container_width=True)

    # Footer (dedented to render HTML)
    st.markdown("---")
    footer_html = f"""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <h3>📊 {BRAND["name"]} • Sentiment Analytics</h3>
    <p><strong>Powered by:</strong> Streamlit • Plotly • TextBlob • VADER • Emoji Intelligence</p>
    <p><strong>Features:</strong> Auto-Setup • Power BI–style Visuals • Emoji-aware Consensus • Advanced Filtering • Export</p>
    <p>Built with ❤️ for data-driven insights</p>
</div>
"""
    st.markdown(dedent(footer_html), unsafe_allow_html=True)

# ===============================================
# APPLICATION ENTRY POINT
# ===============================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.error("Please refresh the page and try again. If the error persists, check your data format.")
        if st.checkbox("🐛 Show Debug Information"):
            st.exception(e)
