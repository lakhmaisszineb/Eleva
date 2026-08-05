"""Thème Eleva – fond blanc, mauve / bleu, B2B."""

MAUVE = "#7C3AED"
MAUVE_DARK = "#5B21B6"
MAUVE_SOFT = "#F5F3FF"
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
HEADER_BG = "#FAFAFA"

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

    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 0.5rem 1rem 0.5rem;
        border-bottom: 1px solid {BORDER};
        margin-bottom: 1.25rem;
        background: {HEADER_BG};
    }}
    .brand {{
        font-weight: 700;
        font-size: 1.35rem;
        letter-spacing: -0.03em;
    }}
    .brand .name {{
        background: linear-gradient(135deg, {MAUVE}, {BLUE});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .brand .sub {{
        display: block;
        font-size: 0.7rem;
        font-weight: 500;
        color: {TEXT_MUTED};
        margin-top: 2px;
    }}
    .status-dot {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        font-weight: 500;
    }}
    .dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }}
    .dot-on {{ background: {SUCCESS}; box-shadow: 0 0 0 3px rgba(22,163,74,0.25); }}
    .dot-off {{ background: {DANGER}; box-shadow: 0 0 0 3px rgba(220,38,38,0.2); }}

    .eleva-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04);
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

    div[data-testid="stHorizontalBlock"] button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
</style>
"""

# Libellés FR pour les KPIs
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