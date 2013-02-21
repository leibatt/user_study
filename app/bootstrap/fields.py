from wtforms import Form, BooleanField, TextField, RadioField, validators 
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString

class BootstrapRadioField(RadioField):
	def __call__(self, **kwargs):
		kwargs.setdefault('type','radio')
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
