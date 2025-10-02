# Supply Chain Dashboard
A sample and simple Python-based tool to 
1. Visualize inventory levels and optimize reorder points using `pandas`, `plotly`, and `pulp`.
2. Visualize the cost to reorder inventory per bulk and per unit

## Setup
1. Install: `pip install -r requirements.txt`
2. Run: `python supply_chain_dashboard.py`
3. Outputs: Dashboard based on input data (CSV) and writes it to `data/output/inventory_dashboard.csv`

## Features
- Reads inventory data from CSV, including product names, descriptions, purposes, and safety stock.
- Optimizes reorder decisions within a budget.
- Visualizes stock and reorder costs with interactive Plotly/Dash charts (names/descriptions in hover text).


# Supply Chain Dashboard
A Python tool to visualize inventory and optimize reorder points for 20 products using `pandas`, `plotly`, `pulp`, and `dash`.

## Setup
1. Install: `pip install -r requirements.txt`
2. Add `data/inventory_data.csv` (sample provided).
4. Run: `python supply_chain_dashboard.py`
5. Outputs: Dash web interface (http://127.0.0.1:8050), `data/inventory_dashboard.csv`, `output/dashboard.png`, `output/reorder_costs.png`

## Features


## Sample Output
![Stock Dashboard](output/images/outputdashboards/2025-10-01/inventory_dashboard.png)
![Reorder Costs](output/images/outputdashboards/2025-10-01/cost-to-reorder.png)