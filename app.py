# Created by Marcio Maia
# Purpose is to create a custom sample dashboard for a supply chain using some sample test data.

import pandas as pd
from flask import Flask, render_template, redirect, url_for, session, request
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from forms import LoginForm, InventoryForm, SettingsForm
from optimizer import load_and_optimize
from utils import load_data, load_settings, save_settings
import plotly.express as px

# Flask app
server = Flask(__name__)
server.secret_key = 'supersecretkey'  # Use a secure key in production
server.config['WTF_CSRF_ENABLED'] = True

# Dash app integrated with Flask
app = Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Initial load
df, fig, fig2 = load_and_optimize()

# Flask routes
@server.route('/')
def index():
    return render_template("index.html")

@server.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'password':  # TODO: Replace with secure auth
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', form=form, error='Invalid username or password')
    return render_template('login.html', form=form)

@server.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@server.route('/edit_inventory', methods=['GET', 'POST'])
def edit_inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    df = load_data()
    if df is None:
        return "Error loading data", 500

    form = InventoryForm()
    if request.method == 'GET':
        form.inventory.entries = []
        for _, row in df.iterrows():
            item_form = form.inventory.form_class()
            item_form.product_id = row['product_id']
            item_form.product_name = row['product_name']
            item_form.description = row['description']
            item_form.purpose = row['purpose']
            item_form.stock = row['stock']
            item_form.demand_rate = row['demand_rate']
            item_form.lead_time = row['lead_time']
            item_form.reorder_cost = row['reorder_cost']
            item_form.safety_stock = row['safety_stock']
            form.inventory.append_entry(item_form)

    if form.validate_on_submit():
        updated_data = []
        for item_form in form.inventory:
            row = {
                'product_id': item_form.product_id.data,
                'product_name': item_form.product_name.data,
                'description': item_form.description.data,
                'purpose': item_form.purpose.data,
                'stock': float(item_form.stock.data),
                'demand_rate': float(item_form.demand_rate.data),
                'lead_time': float(item_form.lead_time.data),
                'reorder_cost': float(item_form.reorder_cost.data),
                'safety_stock': float(item_form.safety_stock.data)
            }
            updated_data.append(row)
        new_df = pd.DataFrame(updated_data)
        new_df.to_csv('data/input/inventory_data.csv', index=False)
        return redirect(url_for('admin'))

    return render_template('edit_inventory.html', form=form)

@server.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    form = SettingsForm()
    current_settings = load_settings()
    if request.method == 'GET':
        form.budget.data = current_settings['budget']
        form.warehouse_capacity.data = current_settings['warehouse_capacity']

    if form.validate_on_submit():
        settings = {
            'budget': float(form.budget.data),
            'warehouse_capacity': float(form.warehouse_capacity.data)
        }
        save_settings(settings)
        return redirect(url_for('admin'))

    return render_template('settings.html', form=form)

@server.route('/dashboard/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return app.index()  # Render the Dash app

@server.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Dash layout with dropdown filter
if df is not None:
    app.layout = html.Div([
        html.H1("Supply Chain Inventory Dashboard"),
        dcc.Dropdown(
            id='product-filter',
            options=[{'label': pid, 'value': pid} for pid in df['product_id']],
            multi=True,
            placeholder="Select products"
        ),
        dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),
        dcc.Graph(id='stock-graph'),
        html.H2("Reorder Costs"),
        dcc.Graph(id='cost-graph'),
        html.A("Admin Dashboard", href="/admin")
    ])

    @app.callback(
        [Output('stock-graph', 'figure'),
         Output('cost-graph', 'figure')],
        [Input('interval-component', 'n_intervals'),
         Input('product-filter', 'value')]
    )
    def update_graphs(n_intervals, selected_products):
        df, fig, fig2 = load_and_optimize()
        if df is None:
            return px.bar(title="Error: Data not loaded"), px.bar(title="Error: Data not loaded")
        if selected_products:
            df = df[df['product_id'].isin(selected_products)]
            fig = px.bar(df, x='product_id', y='stock', color='should_reorder',
                         title='Filtered Inventory Levels', labels={'stock': 'Stock (000s units)'},
                         color_continuous_scale='Viridis')
            fig.add_hline(y=df['reorder_point'].mean(), line_dash="dash", annotation_text="Avg Reorder Point")
            fig.update_traces(hovertemplate='Product: %{x}<br>Name: %{customdata[0]}<br>Description: %{customdata[1]}<br>Purpose: %{customdata[2]}<br>Stock: %{y}k units<br>Demand: %{customdata[3]}k/day<br>Lead Time: %{customdata[4]} days<br>Safety Stock: %{customdata[5]}k units',
                              customdata=df[['product_name', 'description', 'purpose', 'demand_rate', 'lead_time', 'safety_stock']])
            fig2 = px.bar(df, x='product_id', y='reorder_cost', title='Filtered Reorder Costs',
                          labels={'reorder_cost': 'Cost (000s USD)'}, color_continuous_scale='Plasma')
        return fig, fig2

# Run the Flask server
if __name__ == '__main__':
    try:
        server.run(debug=True, port=8050)
    except Exception as e:
        print(f"Error running server: {e}")
        print("Check if port 8050 is free or try: server.run(debug=True, port=8051)")