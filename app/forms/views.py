from flask import Flask, Blueprint,flash, session, request, render_template, g, redirect, send_file, url_for
import app.forms.forms as forms
from app.models import User
from app.database import db_session
from sqlalchemy.orm.exc import NoResultFound
import uuid

mod = Blueprint('forms',__name__,url_prefix='/forms')

@mod.route('/pretest/show/', methods=["POST", "GET"])
def get_pretest():
    form = forms.generate_survey_instance_form("pre") #basic_form.RegistrationForm()
    return render_template('forms/pretest_survey.html',form=form)

@mod.route('/pretest/submit/', methods=["POST"])
def submit_pretest():
    form = forms.generate_survey_instance_form("pre",request.form)
    forms.submit_user_responses(session['user_id'],form)
    return redirect(url_for('scalar.get_data2_canvas'))

@mod.route('/posttest/show/', methods=["POST", "GET"])
def get_posttest():
    form = forms.generate_survey_instance_form("post") #basic_form.RegistrationForm()
    return render_template('forms/posttest_survey.html',form=form)

@mod.route('/posttest/submit/', methods=["POST"])
def submit_posttest():
    form = forms.generate_survey_instance_form("post",request.form)
    forms.submit_user_responses(session['user_id'],form)
    return redirect(url_for('forms.done'))

@mod.route('/done/',methods=["POST","GET"])
def done():
    return render_template('forms/done.html')

@mod.before_request
def before_request(exception=None):
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


