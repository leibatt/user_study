from functools import wraps
from flask import g, request, redirect, url_for

def consent_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if g.consent is None:
            return redirect(url_for('home.welcome'))
        return f(*args,**kwargs)
    return decorated_function
