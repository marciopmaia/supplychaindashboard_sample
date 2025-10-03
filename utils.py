import pandas as pd
import json
import os

def load_data():
    try:
        df = pd.read_csv('data/input/inventory_data.csv')
        required_columns = ['product_id', 'product_name', 'description', 'purpose', 'stock', 'demand_rate', 'lead_time', 'reorder_cost', 'safety_stock']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: CSV must contain {required_columns}")
            return None
        return df
    except FileNotFoundError:
        print("Error: 'data/input/inventory_data.csv' not found.")
        return None

def load_settings():
    try:
        with open('data/settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'budget': 1500, 'warehouse_capacity': 1000}

def save_settings(settings):
    with open('data/settings.json', 'w') as f:
        json.dump(settings, f)