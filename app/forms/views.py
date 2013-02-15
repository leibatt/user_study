from flask import Flask, Blueprint,flash, session, request, render_template, g, redirect, send_file, url_for
import app.forms.forms as forms
from app.models import User
from app.database import db_session
from sqlalchemy.orm.exc import NoResultFound
from app.forms.decorators import consent_required
import uuid

mod = Blueprint('forms',__name__,url_prefix='/forms')

@mod.route('/consent/show/', methods=["POST", "GET"])
def get_consent():
    return render_template('forms/consent_form.html')

@mod.route('/consent/submit/', methods=["POST", "GET"])
def submit_consent():
    if 'consent-check' in request.form: # user checked consent box
        session['consent'] = True
        return redirect(url_for('forms.get_pretest'))
    else:
        return redirect(url_for('forms.get_consent'))

@mod.route('/pretest/show/', methods=["POST", "GET"])
@consent_required
def get_pretest():
    form = forms.generate_survey_instance_form("pre") #basic_form.RegistrationForm()
    return render_template('forms/pretest_survey.html',form=form)

@mod.route('/pretest/submit/', methods=["POST"])
@consent_required
def submit_pretest():
    form = forms.generate_survey_instance_form("pre",request.form)
    forms.submit_user_responses(session['user_id'],form)
    return redirect(url_for('scalar.tutorial'))

@mod.route('/posttest/show/', methods=["POST", "GET"])
@consent_required
def get_posttest():
    form = forms.generate_survey_instance_form("post") #basic_form.RegistrationForm()
    return render_template('forms/posttest_survey.html',form=form)

@mod.route('/posttest/submit/', methods=["POST"])
@consent_required
def submit_posttest():
    form = forms.generate_survey_instance_form("post",request.form)
    forms.submit_user_responses(session['user_id'],form)
    return redirect(url_for('forms.done'))

@mod.route('/done/',methods=["POST","GET"])
@consent_required
def done():
    session.pop('user_id') #don't let user modify selections at this point
    session.pop('consent')
    return render_template('forms/done.html')

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


