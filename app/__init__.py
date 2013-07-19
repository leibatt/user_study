from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter

app = Flask(__name__,static_folder='static')
#add app configurations
app.config.from_object('config')

# needs to be done at the end of the file
__all__ = ['forms','scalar','bootstrap','models','views','database']

#initialize database
import app.database as db
db.configure_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_db()

from app.views import mod as homeModule
from app.forms.views import mod as formsModule
from app.scalar.views import mod as scalarModule
app.register_blueprint(homeModule)
app.register_blueprint(formsModule)
app.register_blueprint(scalarModule)

