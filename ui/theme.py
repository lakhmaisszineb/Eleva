"""
Thème Eleva – Design System professionnel (FR).
Indigo / Slate / White.
"""

# Palette de couleurs professionnelle (inspirée de Tailwind / Modern SaaS)
PRIMARY = "#4F46E5"        # Indigo 600
PRIMARY_DARK = "#3730A3"   # Indigo 800
PRIMARY_LIGHT = "#EEF2FF"  # Indigo 50
SECONDARY = "#64748B"      # Slate 500
BG_MAIN = "#F8FAFC"        # Slate 50
BG_CARD = "#FFFFFF"        # White
TEXT_MAIN = "#0F172A"      # Slate 900
TEXT_MUTED = "#64748B"     # Slate 500
BORDER = "#E2E8F0"         # Slate 200
SUCCESS = "#10B981"        # Emerald 500
WARNING = "#F59E0B"        # Amber 500
DANGER = "#EF4444"         # Red 500

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Reset & Base */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {TEXT_MAIN};
    }}

    .stApp {{
        background-color: {BG_MAIN};
    }}

    /* Masquer les éléments Streamlit par défaut pour un look "App" */
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none;}}
    [data-testid="stHeader"] {{display: none;}}

    /* Conteneur principal */
    .main-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }}

    /* ----- Barre de navigation supérieure ----- */
    .nav-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid {BORDER};
    }}

    .logo-text {{
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: {PRIMARY};
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .status-indicator {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        font-weight: 500;
    }}

    .dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }}
    .dot-online {{ background-color: {SUCCESS}; box-shadow: 0 0 8px {SUCCESS}80; }}
    .dot-offline {{ background-color: {DANGER}; box-shadow: 0 0 8px {DANGER}80; }}

    /* ----- Cartes & Conteneurs ----- */
    .card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }}

    .kpi-card {{
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }}

    .kpi-label {{
        font-size: 0.75rem;
        font-weight: 600;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}

    .kpi-value {{
        font-size: 1.875rem;
        font-weight: 700;
        color: {TEXT_MAIN};
    }}

    .kpi-unit {{
        font-size: 0.875rem;
        font-weight: 500;
        color: {TEXT_MUTED};
        margin-left: 0.25rem;
    }}

    /* ----- Titres ----- */
    .h1 {{ font-size: 1.875rem; font-weight: 700; margin-bottom: 0.5rem; color: {TEXT_MAIN}; }}
    .h2 {{ font-size: 1.5rem; font-weight: 700; margin-top: 2rem; margin-bottom: 1rem; color: {TEXT_MAIN}; }}
    .h3 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem; color: {TEXT_MAIN}; }}
    .subtitle {{ font-size: 1rem; color: {TEXT_MUTED}; margin-bottom: 2rem; }}

    /* ----- Badges ----- */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge-primary {{ background-color: {PRIMARY_LIGHT}; color: {PRIMARY}; }}
    .badge-success {{ background-color: #ECFDF5; color: {SUCCESS}; }}
    .badge-warning {{ background-color: #FFFBEB; color: {WARNING}; }}
    .badge-danger {{ background-color: #FEF2F2; color: {DANGER}; }}
    .badge-slate {{ background-color: #F1F5F9; color: {SECONDARY}; }}

    /* ----- Étapes de l'analyse ----- */
    .step-container {{
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding-left: 1.5rem;
        border-left: 2px solid {BORDER};
        margin: 1.5rem 0;
    }}

    .step-item {{
        position: relative;
    }}

    .step-dot {{
        position: absolute;
        left: -1.95rem;
        top: 0.25rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: {BG_CARD};
        border: 2px solid {PRIMARY};
    }}

    .step-active .step-dot {{
        background-color: {PRIMARY};
        box-shadow: 0 0 0 4px {PRIMARY_LIGHT};
    }}

    .step-title {{
        font-size: 0.9375rem;
        font-weight: 600;
        color: {TEXT_MAIN};
    }}

    .step-desc {{
        font-size: 0.8125rem;
        color: {TEXT_MUTED};
    }}

    /* ----- Recommandations ----- */
    .reco-card {{
        border-left: 4px solid {PRIMARY};
    }}
    .reco-critical {{ border-left-color: {DANGER}; }}
    .reco-high {{ border-left-color: {WARNING}; }}
    .reco-medium {{ border-left-color: {PRIMARY}; }}
    .reco-low {{ border-left-color: {SECONDARY}; }}

    /* ----- Boutons Streamlit ----- */
    div.stButton > button {{
        background-color: {PRIMARY} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }}
    div.stButton > button:hover {{
        background-color: {PRIMARY_DARK} !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2) !important;
    }}

    /* Boutons secondaires */
    div.stButton > button[kind="secondary"] {{
        background-color: white !important;
        color: {TEXT_MAIN} !important;
        border: 1px solid {BORDER} !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: {BG_MAIN} !important;
        border-color: {SECONDARY} !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 3rem;
        padding-top: 0;
        padding-bottom: 0;
        background-color: transparent !important;
        border: none !important;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {PRIMARY} !important;
        border-bottom: 2px solid {PRIMARY} !important;
    }}
</style>
"""

# Traductions des KPIs pour l'interface
KPI_LABELS_FR = {
    "total_customers": "Total Clients",
    "total_orders": "Total Commandes",
    "completed_orders": "Commandes Terminées",
    "abandoned_orders": "Paniers Abandonnés",
    "cart_abandonment_rate": "Taux d'Abandon",
    "average_order_value": "Panier Moyen",
    "repeat_purchase_rate": "Taux de Réachat",
    "approx_clv": "Valeur Vie Client (CLV)",
    "high_churn_risk_count": "Clients à Risque",
    "total_revenue": "Chiffre d'Affaires",
}

# Mapping des priorités
PRIORITY_MAP = {
    "critical": {"label": "CRITIQUE", "class": "badge-danger"},
    "high": {"label": "HAUTE", "class": "badge-warning"},
    "medium": {"label": "MOYENNE", "class": "badge-primary"},
    "low": {"label": "BASSE", "class": "badge-slate"},
}

# Mapping des types d'issues
ISSUE_TYPE_MAP = {
    "problem": {"label": "PROBLÈME", "icon": "⚠️"},
    "opportunity": {"label": "OPPORTUNITÉ", "icon": "🚀"},
}
