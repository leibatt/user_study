from flask import Flask
from app.util.database.database_config import initialize_database
from datetime import timedelta

app = Flask(__name__,static_folder='static')
#add app configurations
app.config.from_object('config')
app.permanent = True
app.permanent_session_lifetime = timedelta(minutes=20)

# needs to be done at the end of the file
__all__ = ['forms','scalar','home','util']

#intialize database
initialize_database(app)

#must happen last
from app.home.views import mod as homeModule
from app.forms.views import mod as formsModule
from app.scalar.views import mod as scalarModule
app.register_blueprint(homeModule)
app.register_blueprint(formsModule)
app.register_blueprint(scalarModule)

