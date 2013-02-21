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

@mod.route('/done/',methods=["POST","GET"])
@consent_required
def done():
    if 'user_id' in session:
        session.pop('user_id') #don't let user modify selections at this point
    if 'consent' in session:
        session.pop('consent')
    return render_template('done.html')

@mod.before_request
def before_request(exception=None):
    g.consent = None
    if 'consent' in session:
        g.consent = session['consent']
    g.user = None
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    try:
        g.user = db_session.query(User).filter_by(flask_session_id=session['user_id']).one()
    except NoResultFound: # user not found
        g.user = User(session['user_id'])
        db_session.add(g.user)
        db_session.commit()

@mod.teardown_request
def teardown_request(exception=None):
    db_session.remove()


