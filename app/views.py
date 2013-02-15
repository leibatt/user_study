from flask import Flask, Blueprint,flash, session, request, render_template, g, redirect, send_file, url_for
import app.forms.forms as forms
from app.models import User
from app.database import db_session
from sqlalchemy.orm.exc import NoResultFound
from app.forms.decorators import consent_required
import uuid

mod = Blueprint('home',__name__)

@mod.route('/home/',methods=["POST","GET"])
def welcome():
    return render_template('welcome.html')

@mod.route('/',methods=["POST","GET"])
def home():
    return redirect(url_for('home.welcome'))
