import pandas as pd
import os
import json

def load_data():
    filepath = 'data/input/inventory_data.csv'
    if not os.path.exists(filepath):
        print("Inventory CSV not found")
        return None
    return pd.read_csv(filepath)

def load_settings():
    settings_file = 'data/settings.json'
    if not os.path.exists(settings_file):
        default_settings = {"budget": 1000, "warehouse_capacity": 1000}
        save_settings(default_settings)
        return default_settings
    with open(settings_file,'r') as f:
        settings = json.load(f)
    settings.setdefault('budget',1000)
    settings.setdefault('warehouse_capacity',1000)
    return settings

def save_settings(settings):
    settings_file = 'data/settings.json'
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    with open(settings_file,'w') as f:
        json.dump(settings,f)
