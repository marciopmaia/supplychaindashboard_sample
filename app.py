# Created by Marcio Maia
# Purpose: Simple Supply Chain Dashboard with Editable Inventory

import os
import pandas as pd
from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.datastructures import MultiDict
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, FormField
from wtforms.fields import FieldList
from wtforms.validators import DataRequired, NumberRange

# ------------------ Flask setup ------------------
server = Flask(__name__, static_folder='static', static_url_path='/static')
server.secret_key = 'supersecretkey'

# ------------------ Dash setup ------------------
app = Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    assets_folder='static'
)

# ------------------ Forms ------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class InventoryItemForm(FlaskForm):
    product_id = StringField('Product ID', render_kw={'readonly': True})
    product_name = StringField('Product Name', validators=[DataRequired()])
    item_description = StringField('Description', validators=[DataRequired()])
    purpose = StringField('Purpose', validators=[DataRequired()])
    stock = FloatField('Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])
    demand_rate = FloatField('Demand Rate (000s/day)', validators=[DataRequired(), NumberRange(min=0)])
    lead_time = FloatField('Lead Time (days)', validators=[DataRequired(), NumberRange(min=0)])
    reorder_cost = FloatField('Reorder Cost (000s USD)', validators=[DataRequired(), NumberRange(min=0)])
    safety_stock = FloatField('Safety Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])

class InventoryForm(FlaskForm):
    inventory = FieldList(FormField(InventoryItemForm), min_entries=0)
    submit = SubmitField('Update Inventory')

# ------------------ Data helpers ------------------
DATA_PATH = 'data/input/inventory_data.csv'

def load_data():
    os.makedirs('data/input', exist_ok=True)
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=[
            'product_id', 'product_name', 'description', 'purpose',
            'stock', 'demand_rate', 'lead_time', 'reorder_cost', 'safety_stock'
        ])
    return pd.read_csv(DATA_PATH)

# ------------------ Routes ------------------
@server.route('/')
def index():
    return redirect(url_for('login'))

@server.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'password':
            session['logged_in'] = True
            return redirect(url_for('edit_inventory'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html', form=form)

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
    form_data = MultiDict()

    # Pre-fill form with existing data
    if not df.empty:
        for idx, row in df.iterrows():
            form_data.add(f'inventory-{idx}-product_id', str(row.get('product_id', '')))
            form_data.add(f'inventory-{idx}-product_name', str(row.get('product_name', '')))
            form_data.add(f'inventory-{idx}-item_description', str(row.get('description', '')))
            form_data.add(f'inventory-{idx}-purpose', str(row.get('purpose', '')))
            form_data.add(f'inventory-{idx}-stock', str(row.get('stock', 0)))
            form_data.add(f'inventory-{idx}-demand_rate', str(row.get('demand_rate', 0)))
            form_data.add(f'inventory-{idx}-lead_time', str(row.get('lead_time', 0)))
            form_data.add(f'inventory-{idx}-reorder_cost', str(row.get('reorder_cost', 0)))
            form_data.add(f'inventory-{idx}-safety_stock', str(row.get('safety_stock', 0)))
    else:
        # Add one blank sample entry
        form_data.add('inventory-0-product_id', 'P001')
        form_data.add('inventory-0-product_name', 'Sample Widget')
        form_data.add('inventory-0-item_description', 'Example item')
        form_data.add('inventory-0-purpose', 'Demo')
        form_data.add('inventory-0-stock', '100')
        form_data.add('inventory-0-demand_rate', '10')
        form_data.add('inventory-0-lead_time', '5')
        form_data.add('inventory-0-reorder_cost', '50')
        form_data.add('inventory-0-safety_stock', '20')

    form = InventoryForm(formdata=form_data)

    if request.method == 'POST' and form.validate_on_submit():
        updated_data = []
        for sub in form.inventory:
            updated_data.append({
                'product_id': sub.product_id.data,
                'product_name': sub.product_name.data,
                'description': sub.item_description.data,  # map to CSV field
                'purpose': sub.purpose.data,
                'stock': sub.stock.data,
                'demand_rate': sub.demand_rate.data,
                'lead_time': sub.lead_time.data,
                'reorder_cost': sub.reorder_cost.data,
                'safety_stock': sub.safety_stock.data,
            })

        pd.DataFrame(updated_data).to_csv(DATA_PATH, index=False)
        flash("Inventory updated successfully!", "success")
        return redirect(url_for('edit_inventory'))

    return render_template('edit_inventory.html', form=form)

# ------------------ Dash dashboard ------------------
df = load_data()
if df.empty:
    df = pd.DataFrame({'product_id': [], 'stock': [], 'reorder_cost': []})

fig_stock = px.bar(df, x='product_id', y='stock', title="Inventory Stock Levels")
fig_cost = px.bar(df, x='product_id', y='reorder_cost', title="Reorder Costs")

app.layout = html.Div([
    html.H1("Supply Chain Dashboard"),
    dcc.Graph(id='stock-graph', figure=fig_stock),
    dcc.Graph(id='cost-graph', figure=fig_cost),
    html.A("Edit Inventory", href="/edit_inventory")
])

# ------------------ Run app ------------------
if __name__ == '__main__':
    server.run(debug=True, port=8050, use_reloader=False)
