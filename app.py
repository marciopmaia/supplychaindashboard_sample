# Created by Marcio Maia
# Purpose: Custom sample dashboard for a supply chain using sample data

import pandas as pd
from flask import Flask, render_template, redirect, url_for, session, request, flash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from forms import LoginForm, InventoryForm, SettingsForm
from optimizer import load_and_optimize
from utils import load_data, load_settings, save_settings
import plotly.express as px
import os

# ------------------ Flask app ------------------
server = Flask(__name__, static_folder='static', static_url_path='/static')
server.secret_key = 'supersecretkey'
server.config['WTF_CSRF_ENABLED'] = True

# ------------------ Dash app ------------------
app = Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    assets_folder='static'
)

# ------------------ Login protection ------------------
@server.before_request
def restrict_dash():
    if request.path.startswith('/dashboard'):
        if not session.get('logged_in'):
            flash("You must be logged in to access the dashboard.", "warning")
            return redirect(url_for('error'))  

# ------------------ Flask routes ------------------
@server.route('/')
def index():
    return render_template('index.html')

@server.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'password':  # TODO: secure auth
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

@server.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@server.route('/edit_inventory', methods=['GET', 'POST'])
def edit_inventory():
    if not session.get('logged_in'):
        flash("Please log in to edit inventory.", "warning")
        return redirect(url_for('login'))

    df = load_data()
    if df is None or df.empty:
        flash("Error loading inventory data.", "danger")
        return redirect(url_for('admin'))

    form = InventoryForm()

    # ---------- Populate form fields on GET ----------
    if request.method == 'GET':
        form.inventory.entries.clear()  # Properly clear existing entries (fixes str delegation)
        for _, row in df.iterrows():
            form.inventory.append_entry()  # Append a new subform
            sub = form.inventory[-1]       # Get the last (new) subform
            # Set data on each field (now safe, as sub is fully initialized)
            sub.product_id.data = str(row['product_id'])     # Ensure str for StringField
            sub.product_name.data = str(row['product_name'])
            sub.description.data = str(row['description'])
            sub.purpose.data = str(row['purpose'])
            sub.stock.data = float(row['stock']) if pd.notna(row['stock']) else 0.0
            sub.demand_rate.data = float(row['demand_rate']) if pd.notna(row['demand_rate']) else 0.0
            sub.lead_time.data = float(row['lead_time']) if pd.notna(row['lead_time']) else 0.0
            sub.reorder_cost.data = float(row['reorder_cost']) if pd.notna(row['reorder_cost']) else 0.0
            sub.safety_stock.data = float(row['safety_stock']) if pd.notna(row['safety_stock']) else 0.0

        return render_template('edit_inventory.html', form=form)

    # ---------- Handle POST: Update CSV ---------- (unchanged from your original)
    if form.validate_on_submit():
        updated_data = []
        for sub in form.inventory:
            updated_data.append({
                'product_id': sub.product_id.data,
                'product_name': sub.product_name.data,
                'description': sub.description.data,
                'purpose': sub.purpose.data,
                'stock': float(sub.stock.data or 0),
                'demand_rate': float(sub.demand_rate.data or 0),
                'lead_time': float(sub.lead_time.data or 0),
                'reorder_cost': float(sub.reorder_cost.data or 0),
                'safety_stock': float(sub.safety_stock.data or 0)
            })

        new_df = pd.DataFrame(updated_data)
        os.makedirs('data/input', exist_ok=True)
        new_df.to_csv('data/input/inventory_data.csv', index=False)

        flash("Inventory updated successfully!", "success")
        return redirect(url_for('admin'))

    # If POST but validation failed
    if request.method == 'POST' and not form.validate_on_submit():
        flash("There was a problem validating the form. Please check inputs.", "danger")

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

@server.route('/error')
def error():
    message = request.args.get('message', 'An error occurred.')
    return render_template('error.html', message=message)

# ------------------ Dash layout ------------------
df, fig, fig2 = load_and_optimize()
if df is None or df.empty:
    df = pd.DataFrame(columns=['product_id','stock','reorder_cost','should_reorder'])
    fig = px.bar(title="No Data Available")
    fig2 = px.bar(title="No Data Available")

app.layout = html.Div([
    html.H1("Supply Chain Inventory Dashboard"),
    dcc.Dropdown(
        id='product-filter',
        options=[{'label': pid, 'value': pid} for pid in df.get('product_id', [])],
        multi=True,
        placeholder="Select products"
    ),
    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),
    dcc.Graph(id='stock-graph', figure=fig),
    html.H2("Reorder Costs"),
    dcc.Graph(id='cost-graph', figure=fig2),
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
    if df is None or df.empty:
        empty_fig = px.bar(title="No Data Available")
        return empty_fig, empty_fig

    if selected_products:
        df = df[df['product_id'].isin(selected_products)]
        fig = px.bar(df, x='product_id', y='stock', color='should_reorder',
                     title='Filtered Inventory Levels', color_continuous_scale='Viridis')
        fig2 = px.bar(df, x='product_id', y='reorder_cost',
                      title='Filtered Reorder Costs', color_continuous_scale='Plasma')
    return fig, fig2

# ------------------ Run server ------------------
if __name__ == '__main__':
    try:
        server.run(debug=True, port=8050, use_reloader=False)
    except Exception as e:
        print(f"Error running server: {e}")
