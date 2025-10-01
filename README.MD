# Supply Chain Dashboard
A sample and simple Python-based tool to visualize inventory levels and optimize reorder points using `pandas`, `plotly`, and `pulp`.

## Setup
1. Install: `pip install -r requirements.txt`
2. Run: `python supply_chain_dashboard.py`
3. Outputs: Dashboard and `data/inventory_dashboard.csv`

## Features
- Calculates reorder points based on demand and lead time.
- Uses Pulp to maximize lead time
- Optimizes reorder decisions to minimize costs.
- Visualizes stock levels with Plotly.
