"""
Génère un dataset synthétique complet pour tester Eleva.
Crée 3 CSV : customers, orders, campaigns.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# ----- Config -----
OUTPUT_DIR = Path("data/uploads")
COMPANY_ID = "company_synthetic"
NUM_CUSTOMERS = 500
NUM_ORDERS = 2000
NUM_CAMPAIGNS = 10

random.seed(42)  # reproductible

# ----- Génération des clients -----
print(f"Génération de {NUM_CUSTOMERS} clients...")
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    cid = f"C{i:04d}"
    
    # Distribution réaliste
    r = random.random()
    if r < 0.15:  # Champions
        total_orders = random.randint(8, 20)
        total_spent = round(random.uniform(800, 3000), 2)
        days_since = random.randint(1, 20)
        churn = round(random.uniform(0.0, 0.2), 2)
        segment = "Champions"
    elif r < 0.35:  # Loyal
        total_orders = random.randint(4, 10)
        total_spent = round(random.uniform(300, 1000), 2)
        days_since = random.randint(10, 40)
        churn = round(random.uniform(0.1, 0.3), 2)
        segment = "Loyal"
    elif r < 0.55:  # At Risk
        total_orders = random.randint(2, 6)
        total_spent = round(random.uniform(100, 500), 2)
        days_since = random.randint(60, 150)
        churn = round(random.uniform(0.6, 0.8), 2)
        segment = "At Risk"
    elif r < 0.70:  # Lost / Churned
        total_orders = random.randint(1, 3)
        total_spent = round(random.uniform(50, 200), 2)
        days_since = random.randint(150, 365)
        churn = round(random.uniform(0.8, 1.0), 2)
        segment = "Lost / Churned"
    elif r < 0.85:  # New / Promising
        total_orders = random.randint(1, 2)
        total_spent = round(random.uniform(50, 300), 2)
        days_since = random.randint(5, 30)
        churn = round(random.uniform(0.2, 0.5), 2)
        segment = "New / Promising"
    else:  # Hibernating
        total_orders = random.randint(1, 4)
        total_spent = round(random.uniform(200, 800), 2)
        days_since = random.randint(90, 200)
        churn = round(random.uniform(0.5, 0.7), 2)
        segment = "Hibernating"
    
    customers.append({
        "customer_id": cid,
        "total_orders": total_orders,
        "total_spent": total_spent,
        "days_since_last_order": days_since,
        "churn_risk_score": churn,
        "email": f"client{i}@example.com",
        "segment": segment,
        # Colonnes extra (iront dans extra_json)
        "age": random.randint(18, 70),
        "city": random.choice(["Paris", "Lyon", "Marseille", "Casablanca", "Rabat"]),
        "signup_date": (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime("%Y-%m-%d"),
        "loyalty_points": random.randint(0, 5000),
    })

# ----- Génération des commandes -----
print(f"Génération de {NUM_ORDERS} commandes...")
orders = []
for i in range(1, NUM_ORDERS + 1):
    oid = f"O{i:05d}"
    cid = random.choice(customers)["customer_id"]
    
    # Statuts réalistes
    status = random.choices(
        ["completed", "abandoned", "cancelled", "refunded"],
        weights=[70, 15, 10, 5]
    )[0]
    
    total = round(random.uniform(20, 500), 2)
    days_ago = random.randint(1, 365)
    order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    orders.append({
        "order_id": oid,
        "customer_id": cid,
        "status": status,
        "total": total,
        "order_date": order_date,
    })

# ----- Génération des campagnes -----
print(f"Génération de {NUM_CAMPAIGNS} campagnes...")
campaigns = []
campaign_types = ["email", "ads", "sms", "social", "influencer"]
for i in range(1, NUM_CAMPAIGNS + 1):
    cid = f"CAMP{i:03d}"
    name = f"Campagne {i}"
    type_ = random.choice(campaign_types)
    conversion = round(random.uniform(0.005, 0.10), 4)
    roi = round(random.uniform(0.5, 5.0), 2)
    
    campaigns.append({
        "campaign_id": cid,
        "name": name,
        "type": type_,
        "conversion_rate": conversion,
        "roi": roi,
    })

# ----- Écriture des CSV -----
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Customers
with open(OUTPUT_DIR / f"{COMPANY_ID}_customers.csv", "w", encoding="utf-8", newline="") as f:
    fieldnames = [
        "customer_id", "total_orders", "total_spent",
        "days_since_last_order", "churn_risk_score",
        "email", "segment",
        # Colonnes extra
        "age", "city", "signup_date", "loyalty_points",
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(customers)

# Orders
with open(OUTPUT_DIR / f"{COMPANY_ID}_orders.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["order_id", "customer_id", "status", "total", "order_date"])
    writer.writeheader()
    writer.writerows(orders)

# Campaigns
with open(OUTPUT_DIR / f"{COMPANY_ID}_campaigns.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["campaign_id", "name", "type", "conversion_rate", "roi"])
    writer.writeheader()
    writer.writerows(campaigns)

print(f"\n✅ Dataset généré dans {OUTPUT_DIR}")
print(f"   - {COMPANY_ID}_customers.csv ({len(customers)} clients)")
print(f"   - {COMPANY_ID}_orders.csv ({len(orders)} commandes)")
print(f"   - {COMPANY_ID}_campaigns.csv ({len(campaigns)} campagnes)")