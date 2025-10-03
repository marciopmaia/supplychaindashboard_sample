# Non Production
This is a non production sample using dashboards with Flask and other Python libraries

# Supply Chain Dashboard
A sample and simple Python-based tool to display a sample for Supply Chain, including admin logins, and other enhancements
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

## Sample Output
![Stock Dashboard](data/images/outputdashboards/2025-10-02/inventory_dashboard.png)
![Reorder Costs](data/images/outputdashboards/2025-10-02/cost-to-reorder.png)
