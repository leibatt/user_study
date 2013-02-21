import wtforms
from wtforms import Form, BooleanField, TextField, RadioField, SelectMultipleField, validators 
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString

class BootstrapRadioField(RadioField):
	field_type = 'radio'

	def __call__(self,**kwargs):
		return render_list(self,**kwargs)

	def tempfunc(self, **kwargs):
		kwargs.setdefault('type',self.field_type)
		field_id = kwargs.pop('id',self.id)
		html = [u'<ul %s>'% html_params(id=field_id)]
		for value, label, checked in self.iter_choices():
			choice_id = u'%s-%s' % (field_id, value)
			options = dict(kwargs, name=self.name, value=value, id=choice_id)
			if checked:
				 options['checked'] = 'checked'
			html.append(u'<li><label %s>' % html_params(class_="radio"))
			html.append(u'<input %s />'% html_params(**options))
			html.append(u'%s</label></li>' % label)
		html.append(u'</ul>')
		return HTMLString(u''.join(html))

class BootstrapCheckBoxField(SelectMultipleField):
	field_type = 'checkbox'

	def __call__(self, **kwargs):
		return render_list(self,**kwargs)

def render_list(field,**kwargs):
		kwargs.setdefault('type',field.field_type)
		field_id = kwargs.pop('id',field.id)
		html = [u'<ul %s>'% html_params(id=field_id)]
		for value, label, checked in field.iter_choices():
			choice_id = u'%s-%s' % (field_id, value)
			options = dict(kwargs, name=field.name, value=value, id=choice_id)
			if checked:
				 options['checked'] = 'checked'
			html.append(u'<li><label %s>' % html_params(class_="radio"))
			html.append(u'<input %s />'% html_params(**options))
			html.append(u'%s</label></li>' % label)
		html.append(u'</ul>')
		return HTMLString(u''.join(html))

