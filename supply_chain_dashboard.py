# --------------------------------------------------------------
# supply_chain_dashboard.py
# --------------------------------------------------------------
import os
import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.datastructures import MultiDict
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, FloatField,
                     SubmitField, FormField)
from wtforms.fields import FieldList
from wtforms.validators import DataRequired, NumberRange
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import pulp
from utils import load_data, load_settings, save_settings

# ------------------ Flask ------------------
server = Flask(__name__, static_folder='static', static_url_path='/static')
server.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# ------------------ Dash (shared) ------------------
dash_app = Dash(__name__,
                server=server,
                url_base_pathname='/dash/',
                assets_folder='static')

# ------------------ Forms ------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')

class InventoryItemForm(FlaskForm):
    product_id      = StringField('Product ID', render_kw={'readonly': True})
    product_name    = StringField('Product Name', validators=[DataRequired()])
    item_description= StringField('Description', validators=[DataRequired()])
    purpose         = StringField('Purpose', validators=[DataRequired()])
    stock           = FloatField('Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])
    demand_rate     = FloatField('Demand Rate (000s/day)', validators=[DataRequired(), NumberRange(min=0)])
    lead_time       = FloatField('Lead Time (days)', validators=[DataRequired(), NumberRange(min=0)])
    reorder_cost    = FloatField('Reorder Cost (000s USD)', validators=[DataRequired(), NumberRange(min=0)])
    safety_stock    = FloatField('Safety Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])

class InventoryForm(FlaskForm):
    inventory = FieldList(FormField(InventoryItemForm), min_entries=0)
    submit    = SubmitField('Update Inventory')

class SettingsForm(FlaskForm):
    budget            = FloatField('Budget (000s USD)', validators=[DataRequired(), NumberRange(min=0)])
    warehouse_capacity= FloatField('Warehouse Capacity (000s units)', validators=[DataRequired(), NumberRange(min=0)])
    submit            = SubmitField('Update Settings')

# ------------------ Helpers ------------------
def require_login(fn):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

def require_role(role):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if session.get('role') != role:
                flash('You do not have permission for this page.', 'danger')
                return redirect(url_for('dashboard'))
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

# ------------------ Routes ------------------
@server.route('/')
def index(): return redirect(url_for('login'))

@server.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u, p = form.username.data, form.password.data
        if u == 'admin' and p == 'password':
            session['logged_in'] = True
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
        if u == 'user' and p == 'password':
            session['logged_in'] = True
            session['role'] = 'user'
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@server.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- ADMIN ONLY ----------
@server.route('/edit_inventory', methods=['GET', 'POST'])
@require_login
@require_role('admin')
def edit_inventory():
    df = load_data() or pd.DataFrame(columns=[
        'product_id','product_name','description','purpose',
        'stock','demand_rate','lead_time','reorder_cost','safety_stock'
    ])

    # ---- pre-fill form ----
    form_data = MultiDict()
    for idx, row in df.iterrows():
        prefix = f'inventory-{idx}'
        for col in df.columns:
            form_data.add(f'{prefix}-{col}', str(row[col]))
    # add one blank row if empty
    if df.empty:
        prefix = 'inventory-0'
        form_data.add(f'{prefix}-product_id', 'P001')
        form_data.add(f'{prefix}-product_name', 'Sample Widget')
        form_data.add(f'{prefix}-item_description', 'Example')
        form_data.add(f'{prefix}-purpose', 'Demo')
        form_data.add(f'{prefix}-stock', '100')
        form_data.add(f'{prefix}-demand_rate', '10')
        form_data.add(f'{prefix}-lead_time', '5')
        form_data.add(f'{prefix}-reorder_cost', '50')
        form_data.add(f'{prefix}-safety_stock', '20')

    form = InventoryForm(formdata=form_data)

    if request.method == 'POST' and form.validate_on_submit():
        rows = []
        for sub in form.inventory:
            rows.append({
                'product_id'      : sub.product_id.data,
                'product_name'    : sub.product_name.data,
                'description'     : sub.item_description.data,
                'purpose'         : sub.purpose.data,
                'stock'           : sub.stock.data,
                'demand_rate'     : sub.demand_rate.data,
                'lead_time'       : sub.lead_time.data,
                'reorder_cost'    : sub.reorder_cost.data,
                'safety_stock'    : sub.safety_stock.data,
            })
        pd.DataFrame(rows).to_csv('data/input/inventory_data.csv', index=False)
        flash('Inventory saved!', 'success')
        return redirect(url_for('edit_inventory'))

    return render_template('edit_inventory.html', form=form)

@server.route('/settings', methods=['GET', 'POST'])
@require_login
@require_role('admin')
def settings():
    cur = load_settings()
    form = SettingsForm(data=cur)

    if form.validate_on_submit():
        save_settings({'budget': form.budget.data,
                       'warehouse_capacity': form.warehouse_capacity.data})
        flash('Settings updated!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', form=form)

# ---------- COMMON DASHBOARD ----------
@server.route('/dashboard')
@require_login
def dashboard():
    # Choose template according to role
    tmpl = 'dashboard_admin.html' if session.get('role') == 'admin' else 'dashboard_user.html'
    # Embed the Dash app (the same layout for both roles)
    dash_html = dash_app.index_string.replace(
        '</head>', '<link rel="stylesheet" href="/static/style.css"></head>')
    # A tiny trick – inject the whole Dash HTML into the Flask template
    return render_template(tmpl, dash_embed=dash_html)

# ------------------ DASH LAYOUT & CALLBACKS ------------------
def build_figures():
    df = load_data()
    if df is None or df.empty:
        empty = px.bar(title='No inventory data')
        return empty, empty, pd.DataFrame()

    # ---- Reorder point ----
    df['reorder_point'] = df['demand_rate'] * df['lead_time'] + df['safety_stock']

    # ---- Settings ----
    settings = load_settings()

    # ---- PuLP optimisation ----
    prob = pulp.LpProblem("Reorder_Opt", pulp.LpMinimize)
    reorder = pulp.LpVariable.dicts("reorder", df['product_id'], cat='Binary')

    # objective = total reorder cost
    prob += pulp.lpSum([reorder[p] * df.loc[df['product_id']==p, 'reorder_cost'].iloc[0]
                        for p in df['product_id']])

    # budget constraint
    prob += pulp.lpSum([reorder[p] * df.loc[df['product_id']==p, 'reorder_cost'].iloc[0]
                        for p in df['product_id']]) <= settings['budget']

    # warehouse capacity (assume each reorder adds 50k units – change if you like)
    prob += pulp.lpSum([reorder[p] * 50 for p in df['product_id']]) <= settings['warehouse_capacity']

    # force reorder when stock < reorder_point
    M = 1_000_000
    for p in df['product_id']:
        stock = df.loc[df['product_id']==p, 'stock'].iloc[0]
        rp    = df.loc[df['product_id']==p, 'reorder_point'].iloc[0]
        prob += reorder[p] >= (rp - stock) / M
        prob += reorder[p] <= 1

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if status == 1:
        df['should_reorder'] = [int(reorder[p].value()) for p in df['product_id']]
    else:
        df['should_reorder'] = 0

    # ---- Figures ----
    fig1 = px.bar(df, x='product_id', y='stock',
                  color='should_reorder',
                  title='Stock Levels (red = reorder recommended)',
                  color_continuous_scale='Viridis')
    fig1.add_hline(y=df['reorder_point'].mean(),
                   line_dash="dash", line_color="red",
                   annotation_text="Avg Reorder Point")

    fig1.update_traces(
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Name: %{customdata[0]}<br>'
            'Desc: %{customdata[1]}<br>'
            'Purpose: %{customdata[2]}<br>'
            'Stock: %{y}k<br>'
            'Demand: %{customdata[3]}k/day<br>'
            'Lead: %{customdata[4]} days<br>'
            'Safety: %{customdata[5]}k'
        ),
        customdata=df[['product_name','description','purpose',
                       'demand_rate','lead_time','safety_stock']]
    )

    fig2 = px.bar(df, x='product_id', y='reorder_cost',
                  title='Reorder Cost per Product',
                  color='should_reorder',
                  color_continuous_scale='Plasma')

    # ---- Save static images (optional) ----
    today = datetime.now().strftime('%Y-%m-%d')
    out = f'data/images/outputdashboards/{today}'
    os.makedirs(out, exist_ok=True)
    fig1.write_image(f'{out}/inventory_dashboard.png')
    fig2.write_image(f'{out}/cost-to-reorder.png')
    df.to_csv('data/output/inventory_dashboard.csv', index=False)

    return fig1, fig2, df

# Dash layout (same for admin & user)
dash_app.layout = html.Div([
    html.H2('Supply-Chain Overview', style={'textAlign':'center'}),
    dcc.Graph(id='graph-stock'),
    dcc.Graph(id='graph-cost'),
    dcc.Interval(id='interval', interval=30*1000, n_intervals=0)  # refresh every 30s
])

@dash_app.callback(
    [Output('graph-stock', 'figure'),
     Output('graph-cost', 'figure')],
    Input('interval', 'n_intervals')
)
def refresh_graphs(_):
    f1, f2, _ = build_figures()
    return f1, f2

# --------------------------------------------------------------
if __name__ == '__main__':
    # Flask debug + Dash auto-reload
    server.run(host='0.0.0.0', port=8050, debug=True, use_reloader=True)