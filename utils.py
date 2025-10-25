# utils.py
import pandas as pd, json, os

DATA_PATH = 'data/input/inventory_data.csv'
SETTINGS_PATH = 'data/settings.json'

def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    return pd.read_csv(DATA_PATH)

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        default = {"budget": 1000, "warehouse_capacity": 1000}
        save_settings(default)
        return default
    with open(SETTINGS_PATH) as f:
        s = json.load(f)
    s.setdefault('budget', 1000)
    s.setdefault('warehouse_capacity', 1000)
    return s

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=2)