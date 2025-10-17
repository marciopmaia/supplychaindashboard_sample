#TODO feedback form
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from wtforms import Form, StringField, TextAreaField, validators
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  
from email.mime.base import MIMEBase
from email import encoders  
import logging
import pandas as pd
from datetime import datetime
import json
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask import current_app as app
from flask_wtf.csrf import CSRFProtect
from flask import current_app
from flask import send_file
from io import BytesIO
from flask import after_this_request
import zipfile


feedback_bp = Blueprint('feedback', __name__, template_folder='templates')
csrf = CSRFProtect()    

