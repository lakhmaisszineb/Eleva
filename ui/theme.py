"""Thème Eleva – fond blanc, mauve / bleu, B2B."""

MAUVE = "#7C3AED"
MAUVE_DARK = "#5B21B6"
MAUVE_SOFT = "#F5F3FF"
MAUVE_LIGHT = "#EDE9FE"
BLUE = "#2563EB"
BLUE_SOFT = "#EFF6FF"
BG = "#FFFFFF"
CARD_BG = "#FFFFFF"
TEXT = "#0F172A"
TEXT_MUTED = "#64748B"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
BORDER = "#E2E8F0"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', system-ui, sans-serif;
        color: {TEXT};
    }}

    .stApp {{
        background: {BG};
    }}

    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none;}}

    /* ----- Top bar ----- */
    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.25rem 0.75rem 0.25rem;
        margin-bottom: 0.75rem;
        background: transparent;
        border: none;
        border-bottom: none;
    }}
    .brand {{
        font-weight: 700;
        font-size: 1.35rem;
        letter-spacing: -0.03em;
        cursor: default;
        background: none;
    }}
    .brand .name {{
        background: linear-gradient(135deg, {MAUVE}, {BLUE});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    /* Status: dot only */
    .status-dot {{
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        cursor: default;
    }}
    .dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }}
    .dot-on {{
        background: {SUCCESS};
        box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.25);
    }}
    .dot-off {{
        background: {DANGER};
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.2);
    }}

    /* Cards */
    .eleva-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}
    .kpi-label {{
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {TEXT_MUTED};
        font-weight: 600;
    }}
    .kpi-value {{
        font-size: 1.55rem;
        font-weight: 700;
        color: {MAUVE_DARK};
        margin-top: 0.25rem;
    }}
    .section-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {TEXT};
        margin: 1rem 0 0.75rem 0;
    }}
    .badge {{
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 0.35rem;
    }}
    .badge-high {{ background: #FEE2E2; color: {DANGER}; }}
    .badge-medium {{ background: #FEF3C7; color: {WARNING}; }}
    .badge-low {{ background: #DCFCE7; color: {SUCCESS}; }}
    .badge-problem {{ background: {MAUVE_SOFT}; color: {MAUVE_DARK}; }}
    .badge-opportunity {{ background: {BLUE_SOFT}; color: {BLUE}; }}

    .reco-card {{
        background: #fff;
        border: 1px solid {BORDER};
        border-left: 4px solid {MAUVE};
        border-radius: 12px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 0.85rem;
    }}
    .reco-card.high {{ border-left-color: {DANGER}; }}
    .reco-card.medium {{ border-left-color: {WARNING}; }}
    .reco-card.low {{ border-left-color: {SUCCESS}; }}

    /* Boutons : couleur principale = mauve (plus de rouge Streamlit) */
    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid {BORDER} !important;
        background: {BG} !important;
        color: {TEXT} !important;
    }}
    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {{
        border-color: {MAUVE} !important;
        color: {MAUVE_DARK} !important;
        background: {MAUVE_SOFT} !important;
    }}
    /* Actif / primary = mauve clair, pas rouge */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"] {{
        background: {MAUVE_LIGHT} !important;
        color: {MAUVE_DARK} !important;
        border-color: {MAUVE} !important;
        box-shadow: none !important;
    }}
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
        background: {MAUVE_SOFT} !important;
        color: {MAUVE_DARK} !important;
    }}
</style>
"""

KPI_LABELS_FR = {
    "total_customers": "Clients",
    "total_orders": "Commandes",
    "completed_orders": "Commandes abouties",
    "abandoned_orders": "Paniers abandonnés",
    "cart_abandonment_rate": "Taux d'abandon",
    "average_order_value": "Panier moyen",
    "repeat_purchase_rate": "Taux de réachat",
    "approx_clv": "CLV approx.",
    "high_churn_risk_count": "Clients risque churn",
}