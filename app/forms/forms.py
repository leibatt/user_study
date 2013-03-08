from wtforms import Form, BooleanField, TextField, TextAreaField, validators
from app.bootstrap.fields import BootstrapRadioField as BRadioField, BootstrapCheckBoxField as BCheckBoxField
from app.database import db_session
import app.forms.models as models

QUESTION_PREFIX = "q_"

class BaseSurveyForm(Form):
	pass

def generate_survey_instance_form(survey_name,request_form=None):
	survey_questions = get_survey_questions(survey_name) #list of model question objects

	class SurveyInstanceForm(BaseSurveyForm):
		pass

	question_ids = []
	for question in survey_questions:
		question_id = QUESTION_PREFIX+str(question.id)
		question_ids.append(question_id)
		setattr(SurveyInstanceForm,question_id, generate_field_for_question(question))

	setattr(SurveyInstanceForm,"question_ids",question_ids)

	if request_form is None:
		form = SurveyInstanceForm()
	else:
		form = SurveyInstanceForm(request_form)
		print form[question_id]()	

	return form

#used to load responses back into database
def submit_user_responses(user_id,form):
	user = db_session.query(models.User).filter_by(flask_session_id=user_id).one()
	u_id = user.id
	for question_id in form.question_ids:
		q_id = int(question_id[len(QUESTION_PREFIX):])
		data = form[question_id].data
		print "here's the data:",data,",length:",len(data)
		if len(data) > 0:
			question = db_session.query(models.SurveyQuestion).filter_by(id=q_id).one() #get the question answered
			response_id = None
			if question.input_type == "select":
				if data == 'None': # no data
					continue
				else:
					response_id = int(data)
				# delete user's previous response
				db_session.query(models.UserResponse).filter_by(user_id=u_id,question_id=q_id).delete()
				#assume no comments for now
				user_response = models.UserResponse(data,None,u_id,q_id,response_id)
				db_session.add(user_response)
				print user_response
			elif question.input_type == "multiple":
				# delete user's previous response
				db_session.query(models.UserResponse).filter_by(user_id=u_id,question_id=q_id).delete()
				for d in data: #already know we have valid answers
					response_id = int(d)
			#assume no comments for now
					user_response = models.UserResponse(d,None,u_id,q_id,response_id)
					db_session.add(user_response)
	
	db_session.commit()

def get_survey_questions(survey_name):
	survey = db_session.query(models.Survey).filter_by(name=survey_name).one()
	print "survey id:",survey.id
	survey_id = survey.id # better be a number
	questions = db_session.query(models.SurveyQuestion).filter_by(survey_id=survey_id).order_by(models.SurveyQuestion.id).all()
	return questions

def generate_field_for_question(question):
	if question.input_type in ["select","multiple"]: # get selections
		if question.parent_question is not None:
			print "parent question:",question.parent_question
			responses = db_session.query(models.SurveyQuestion).filter_by(id=question.parent_question).one().responses
		else:
			responses = question.responses
		selections = [0] * len(responses)
		for i,response in enumerate(responses):
			selections[i] = (response.id,response.value)
		if question.input_type == "select":
			return BRadioField(question.question_text,choices=selections)
		else:
			return BCheckBoxField(question.question_text,choices=selections)
	elif question.input_type in ["textbox"]:
		return TextAreaField(question.question_text)
	else:
		return TextField(question.question_text)
