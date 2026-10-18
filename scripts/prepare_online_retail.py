"""
Script de prétraitement pour transformer le dataset Online Retail II (transactionnel)
en format agrégé compatible avec Eleva (customers.csv et orders.csv).
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

def prepare_dataset(input_csv: str, output_dir: str):
    print("Chargement du dataset...")
    df = pd.read_csv(input_csv, encoding="unicode_escape")
    
    # Nettoyage : supprimer annulations et CustomerID manquants
    df = df[~df['Invoice'].astype(str).str.startswith('C')]
    df = df.dropna(subset=['Customer ID'])
    
    # Calcul du total par ligne
    if 'Total' not in df.columns:
        df['Total'] = df['Quantity'] * df['Price']

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Génération de orders.csv (agrégé par facture)
    print("Génération de orders.csv...")
    orders_df = df.groupby(['Invoice', 'Customer ID', 'InvoiceDate']).agg(
        total=('Total', 'sum')
    ).reset_index()
    orders_df.rename(columns={
        'Invoice': 'order_id',
        'Customer ID': 'customer_id',
        'InvoiceDate': 'order_date'
    }, inplace=True)
    orders_df['status'] = 'completed'
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date']).dt.strftime('%Y-%m-%d')
    orders_df['customer_id'] = orders_df['customer_id'].astype(int).astype(str)
    orders_df.to_csv(output_path / "orders.csv", index=False)

    # 2. Génération de customers.csv (agrégé par client)
    print("Génération de customers.csv...")
    today = datetime.now()
    customers_df = df.groupby('Customer ID').agg(
        total_orders=('Invoice', 'nunique'),
        total_spent=('Total', 'sum'),
        last_order_date=('InvoiceDate', 'max')
    ).reset_index()

    customers_df['last_order_date'] = pd.to_datetime(customers_df['last_order_date'])
    customers_df['days_since_last_order'] = (today - customers_df['last_order_date']).dt.days
    customers_df['churn_risk_score'] = (customers_df['days_since_last_order'] / 180.0).clip(0.0, 1.0).round(2)

    customers_df.rename(columns={'Customer ID': 'customer_id'}, inplace=True)
    customers_df['customer_id'] = customers_df['customer_id'].astype(int).astype(str)
    customers_df['total_orders'] = customers_df['total_orders'].astype(int)
    customers_df['total_spent'] = customers_df['total_spent'].round(2)
    customers_df['days_since_last_order'] = customers_df['days_since_last_order'].astype(int)
    
    # Champs requis par Eleva mais absents du dataset UCI
    customers_df['email'] = customers_df['customer_id'] + "@example.com"
    customers_df['segment'] = 'standard'

    customers_df.to_csv(output_path / "customers.csv", index=False)
    print(f" Données prêtes dans {output_dir}")

if __name__ == "__main__":
    prepare_dataset("data/raw/online_retail_II.csv", "data/sample_data")