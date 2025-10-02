# Created by Marcio Maia
# Purpose is to create a custom sample dashboard for a supply chain using some sample test data.

import pandas as pd
import plotly.express as px
import pulp
import os

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
             title='Inventory Levels and Reorder Decisions',
             labels={'stock': 'Stock (000s units)', 'product_id': 'Product ID'})
fig.add_hline(y=df['reorder_point'].mean(), line_dash="dash", annotation_text="Avg Reorder Point")
fig.update_traces(hovertemplate='Product: %{x}<br>Stock: %{y}<br>Demand: %{customdata[0]}<br>Lead Time: %{customdata[1]}', 
                  customdata=df[['demand_rate', 'lead_time']])


# Get today's date in YYYY-MM-DD format
today = datetime.now().strftime('%Y-%m-%d')

# Create the output folder path
output_folder = f'outputdashboards/{today}'

# Create the directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Create dashboard.png
fig.write_image(f'{output_folder}/dashboard.png')
fig.show()

# Save to CSV for documentation
df.to_csv('data/inventory_dashboard.csv', index=False)