from functools import wraps
from flask import g, request, redirect, url_for

def consent_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if g.consent is None:
            return redirect(url_for('forms.get_consent'))
        return f(*args,**kwargs)
    return decorated_function
