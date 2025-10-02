# Created by Marcio Maia
# Purpose is to create a custom sample dashboard for a supply chain using some sample test data.

import pandas as pd
import plotly.express as px
import pulp
import os

from dash import Dash, dcc, html
from datetime import datetime

# Sample supply chain inventory data 
try:
    df = pd.read_csv('data/input/inventory_data.csv')
except FileNotFoundError:
    print("Error: 'data/inventory_data.csv' not found. Please create the file.")
    exit(1)
# df = pd.DataFrame(data)

# Calculate reorder points (basic: demand_rate * lead_time)
df['reorder_point'] = df['demand_rate'] * df['lead_time']

# Optimization: Minimize reorder costs using PuLP
prob = pulp.LpProblem("Inventory_Optimization", pulp.LpMinimize)

# Define binary variables for reordering (1 if reorder, 0 if not)
reorder = pulp.LpVariable.dicts("Reorder", df['product_id'], cat='Binary')

# Objective: Minimize total reorder cost
prob += pulp.lpSum([reorder[pid] * df.loc[df['product_id'] == pid, 'reorder_cost'].iloc[0] for pid in df['product_id']])

# Constraints: Reorder if stock is below or equal to reorder point
M = 10000  # Large constant for constraint formulation
for pid in df['product_id']:
    stock = df.loc[df['product_id'] == pid, 'stock'].iloc[0]
    reorder_point = df.loc[df['product_id'] == pid, 'reorder_point'].iloc[0]
    # Ensure reorder[pid] = 1 if stock <= reorder_point
    # Changed: Use numeric values on the right side of the constraint
    prob += reorder[pid] >= (reorder_point - stock) / M
    prob += reorder[pid] <= 1 - (stock - reorder_point - 1) / M

# Solve the optimization problem
prob.solve()

# Add reorder decisions to dataframe
df['should_reorder'] = [reorder[pid].varValue for pid in df['product_id']]

# Visualize inventory levels
fig = px.bar(df, x='product_id', y='stock', color='should_reorder',
             title='Inventory Levels and Reorder Decisions (20 Products)',
             labels={'stock': 'Stock (000s units)', 'product_id': 'Product ID'},
             color_continuous_scale='Viridis')
fig.add_hline(y=df['reorder_point'].mean(), line_dash="dash", line_color="red", annotation_text="Avg Reorder Point", annotation_font_size=20,
              annotation_font_color="red")
fig.update_traces(hovertemplate='Product: %{x}<br>Name: %{customdata[0]}<br>Description: %{customdata[1]}<br>Purpose: %{customdata[2]}<br>Stock: %{y}k units<br>Demand: %{customdata[3]}k/day<br>Lead Time: %{customdata[4]} days<br>Safety Stock: %{customdata[5]}k units',
                  customdata=df[['product_name', 'description', 'purpose', 'demand_rate', 'lead_time', 'safety_stock']])

# Get today's date in YYYY-MM-DD format
today = datetime.now().strftime('%Y-%m-%d')

# Create the output folder path
# TODO ensure folders are created if they don't exist. 
output_folder = f'data/images/outputdashboards/{today}'

# Create the directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Create dashboard.png
fig.write_image(f'{output_folder}/inventory_dashboard.png')

# Visualize cost to reorder each product
fig2 = px.bar(df, x='product_id', y='reorder_cost', title='Reorder Costs by Product',
              labels={'reorder_cost': 'Cost (000s USD)'})
fig2.write_image(f'{output_folder}/cost-to-reorder.png')

# Save to CSV for documentation
df.to_csv('data/output/inventory_dashboard.csv', index=False)

# Dash interface for web-based dashboard
if __name__ == '__main__':
    try:
        app = Dash(__name__)
        app.layout = html.Div([
            html.H1("Supply Chain Inventory Dashboard"),
            dcc.Graph(id='stock-graph', figure=fig),
            html.H2("Reorder Costs"),
            dcc.Graph(id='cost-graph', figure=fig2)
        ])
        app.run(debug=True)
    except Exception as e:
        print(f"Error running Dash server: {e}")
        print("Check if port 8050 is free or try: app.run(debug=True, port=8051)")