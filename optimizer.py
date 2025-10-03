import pandas as pd
import plotly.express as px
import pulp
from utils import load_data, load_settings
from datetime import datetime
import os

def load_and_optimize():
    df = load_data()
    if df is None:
        return None, None, None

    df['reorder_point'] = df['demand_rate'] * df['lead_time'] + df['safety_stock']
    settings = load_settings()
    prob = pulp.LpProblem("Inventory_Optimization", pulp.LpMinimize)
    reorder = pulp.LpVariable.dicts("Reorder", df['product_id'], cat='Binary')
    prob += pulp.lpSum([reorder[pid] * df.loc[df['product_id'] == pid, 'reorder_cost'].iloc[0] for pid in df['product_id']])
    M = 10000
    for pid in df['product_id']:
        stock = df.loc[df['product_id'] == pid, 'stock'].iloc[0]
        reorder_point = df.loc[df['product_id'] == pid, 'reorder_point'].iloc[0]
        prob += reorder[pid] >= (reorder_point - stock) / M
        prob += reorder[pid] <= 1 - (stock - reorder_point - 1) / M
    prob += pulp.lpSum([reorder[pid] * df.loc[df['product_id'] == pid, 'reorder_cost'].iloc[0] for pid in df['product_id']]) <= settings['budget']
    prob += pulp.lpSum([reorder[pid] * 50 for pid in df['product_id']]) <= settings['warehouse_capacity']
    status = prob.solve()
    if status == pulp.LpStatusOptimal:
        df['should_reorder'] = [reorder[pid].varValue for pid in df['product_id']]
    else:
        print(f"Optimization failed with status: {pulp.LpStatus[status]}")
        return None, None, None

    fig = px.bar(df, x='product_id', y='stock', color='should_reorder',
                 title='Inventory Levels and Reorder Decisions (20 Products)',
                 labels={'stock': 'Stock (000s units)', 'product_id': 'Product ID'},
                 color_continuous_scale='Viridis')
    fig.add_hline(y=df['reorder_point'].mean(), line_dash="dash", line_color="red", annotation_text="Avg Reorder Point", annotation_font_size=20, annotation_font_color="red")
    fig.update_traces(hovertemplate='Product: %{x}<br>Name: %{customdata[0]}<br>Description: %{customdata[1]}<br>Purpose: %{customdata[2]}<br>Stock: %{y}k units<br>Demand: %{customdata[3]}k/day<br>Lead Time: %{customdata[4]} days<br>Safety Stock: %{customdata[5]}k units',
                      customdata=df[['product_name', 'description', 'purpose', 'demand_rate', 'lead_time', 'safety_stock']])
    
    today = datetime.now().strftime('%Y-%m-%d')
    output_folder = f'data/images/outputdashboards/{today}'
    os.makedirs(output_folder, exist_ok=True)
    fig.write_image(f'{output_folder}/inventory_dashboard.png')

    fig2 = px.bar(df, x='product_id', y='reorder_cost', title='Reorder Costs by Product',
                  labels={'reorder_cost': 'Cost (000s USD)', 'product_id': 'Product ID'},
                  color_continuous_scale='Plasma')
    fig2.write_image(f'{output_folder}/cost-to-reorder.png')

    df.to_csv('data/output/inventory_dashboard.csv', index=False)
    return df, fig, fig2