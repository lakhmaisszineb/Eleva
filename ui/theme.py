"""
Visual identity for the Eleva Streamlit interface.

Palette: warm off-white background, deep navy for structure/text,
muted terracotta as the single accent color, sage green for positive /
opportunity signals, brick red for high-priority problems.
No emojis anywhere in the UI, by design choice.
"""

import streamlit as st

COLORS = {
    "bg": "#FAF8F5",
    "surface": "#FFFFFF",
    "surface_alt": "#F3F0EA",
    "border": "#E6E1D8",
    "text": "#22262B",
    "text_muted": "#6B6F76",
    "navy": "#1F2A44",
    "navy_light": "#334368",
    "accent": "#B5793B",
    "accent_light": "#E7D3B7",
    "sage": "#15221B",
    "sage_light": "#DCE9E2",
    "amber": "#C48A3A",
    "amber_light": "#F2E2C8",
    "brick": "#B5484B",
    "brick_light": "#F3DADA",
    "gray": "#8A8D93",
    "gray_light": "#EAE8E4",
}

PRIORITY_COLOR = {
    "low": (COLORS["gray"], COLORS["gray_light"]),
    "medium": (COLORS["amber"], COLORS["amber_light"]),
    "high": (COLORS["brick"], COLORS["brick_light"]),
    "critical": ("#7A2528", "#EBC9C9"),
}

ISSUE_TYPE_COLOR = {
    "problem": (COLORS["brick"], COLORS["brick_light"]),
    "opportunity": (COLORS["sage"], COLORS["sage_light"]),
}


def configure_page(title: str = "Eleva"):
    st.set_page_config(
        page_title=f"{title} — Agent de décision marketing",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()


def _inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLORS['bg']};
        }}
        [data-testid="stSidebar"] {{
            background-color: {COLORS['surface_alt']};
            border-right: 1px solid {COLORS['border']};
        }}
        [data-testid="stSidebar"] * {{
            color: {COLORS['navy']} !important;
        }}
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stTextArea label {{
            color: {COLORS['text_muted']} !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: {COLORS['border']};
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: {COLORS['surface']};
            border-color: {COLORS['border']};
        }}
        h1, h2, h3, h4 {{
            color: {COLORS['navy']};
            font-weight: 650;
            letter-spacing: -0.01em;
        }}
        p, li, span, label, div {{
            color: {COLORS['text']};
        }}
        .eleva-caption {{
            color: {COLORS['text_muted']};
            font-size: 0.92rem;
        }}
        .eleva-card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.9rem;
        }}
        .eleva-kpi {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 0.95rem 1.1rem;
        }}
        .eleva-kpi-label {{
            color: {COLORS['text_muted']};
            font-size: 0.80rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.15rem;
        }}
        .eleva-kpi-value {{
            color: {COLORS['navy']};
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.2;
        }}
        .eleva-badge {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
        .eleva-section-title {{
            color: {COLORS['navy']};
            font-size: 1.15rem;
            font-weight: 700;
            margin: 1.1rem 0 0.4rem 0;
            border-bottom: 2px solid {COLORS['accent_light']};
            padding-bottom: 0.35rem;
        }}
        .eleva-stepper {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.6rem 0 1rem 0;
        }}
        .eleva-step {{
            background-color: {COLORS['sage_light']};
            color: {COLORS['sage']};
            border-radius: 999px;
            padding: 0.3rem 0.85rem;
            font-size: 0.82rem;
            font-weight: 600;
        }}
        .eleva-step-arrow {{
            color: {COLORS['gray']};
            font-size: 0.82rem;
            align-self: center;
        }}
        .eleva-quote {{
            border-left: 3px solid {COLORS['accent']};
            padding: 0.7rem 1rem;
            background-color: {COLORS['surface_alt']};
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: {COLORS['text']};
        }}
        .eleva-empty {{
            text-align: center;
            padding: 2.2rem 1rem;
            color: {COLORS['text_muted']};
            background-color: {COLORS['surface_alt']};
            border: 1px dashed {COLORS['border']};
            border-radius: 12px;
        }}
        div[data-testid="stMetricValue"] {{
            color: {COLORS['navy']};
        }}
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
        }}
        .stButton > button[kind="primary"] {{
            background-color: {COLORS['navy']};
            border-color: {COLORS['navy']};
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {COLORS['navy_light']};
            border-color: {COLORS['navy_light']};
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
