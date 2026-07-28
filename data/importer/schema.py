"""
Internal Eleva schema for company data.

Only these fields are kept after import.
Column aliases help the LLM + act as fallback.
"""

from typing import Dict, List

# entity -> list of internal field names
SCHEMA: Dict[str, List[str]] = {
    "customers": [
        "customer_id",
        "total_orders",
        "total_spent",
        "days_since_last_order",
        "churn_risk_score",
        "email",
        "segment",  # optional, may be overwritten by RFM later
    ],
    "orders": [
        "order_id",
        "customer_id",
        "status",
        "total",
        "order_date",
    ],
    "campaigns": [
        "campaign_id",
        "name",
        "type",
        "conversion_rate",
        "roi",
    ],
}

# Required fields per entity (import fails if missing after mapping)
REQUIRED: Dict[str, List[str]] = {
    "customers": ["customer_id"],
    "orders": ["order_id", "customer_id"],
    "campaigns": ["name"],  # campaign_id optional if name present
}

# Common aliases (fallback if LLM fails or for documentation)
ALIASES: Dict[str, List[str]] = {
    "customer_id": [
        "customer_id", "customerid", "id_client", "client_id", "id",
        "customer id", "client id", "id client", "user_id", "userid",
    ],
    "order_id": [
        "order_id", "orderid", "id_commande", "commande_id", "order id",
        "numero_commande", "order_number", "id commande",
    ],
    "total": [
        "total", "amount", "montant", "order_total", "ttc", "total_ttc",
        "ca", "revenue", "prix_total",
    ],
    "status": [
        "status", "etat", "state", "order_status", "statut", "statut_commande",
    ],
    "order_date": [
        "order_date", "date", "created_at", "date_commande", "order date",
        "purchase_date", "date_achat",
    ],
    "total_orders": [
        "total_orders", "orders_count", "nb_commandes", "number_of_orders",
        "order_count", "commandes",
    ],
    "total_spent": [
        "total_spent", "lifetime_value", "ltv", "ca_client", "total_spend",
        "monetary", "depense_totale",
    ],
    "days_since_last_order": [
        "days_since_last_order", "recency", "jours_depuis_derniere_commande",
        "days_inactive", "inactivity_days",
    ],
    "churn_risk_score": [
        "churn_risk_score", "churn_score", "churn_risk", "risque_churn",
    ],
    "email": ["email", "e-mail", "mail", "customer_email"],
    "segment": ["segment", "customer_segment", "segment_client"],
    "campaign_id": ["campaign_id", "id_campagne", "campaignid"],
    "name": ["name", "nom", "campaign_name", "nom_campagne", "title"],
    "type": ["type", "campaign_type", "type_campagne"],
    "conversion_rate": ["conversion_rate", "cvr", "taux_conversion"],
    "roi": ["roi", "return_on_investment", "retour_investissement"],
}