from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, FormField
from wtforms.fields import FieldList
from wtforms.validators import DataRequired, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class InventoryItemForm(FlaskForm):
    product_id = StringField('Product ID', render_kw={'readonly': True})
    product_name = StringField('Product Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    purpose = StringField('Purpose', validators=[DataRequired()])
    stock = FloatField('Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])
    demand_rate = FloatField('Demand Rate (000s/day)', validators=[DataRequired(), NumberRange(min=0)])
    lead_time = FloatField('Lead Time (days)', validators=[DataRequired(), NumberRange(min=0)])
    reorder_cost = FloatField('Reorder Cost (000s USD)', validators=[DataRequired(), NumberRange(min=0)])
    safety_stock = FloatField('Safety Stock (000s)', validators=[DataRequired(), NumberRange(min=0)])

class InventoryForm(FlaskForm):
    inventory = FieldList(FormField(InventoryItemForm), min_entries=0)
    submit = SubmitField('Update Inventory')

class SettingsForm(FlaskForm):
    budget = FloatField('Budget (000s USD)', validators=[DataRequired(), NumberRange(min=0)])
    warehouse_capacity = FloatField('Warehouse Capacity (000s units)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Update Settings')