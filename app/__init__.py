from flask import Flask
from app.util.database.database_config import initialize_database
from app.util.celery.celery_config import initialize_celery

app = Flask(__name__,static_folder='static')
#add app configurations
app.config.from_object('config')

# needs to be done at the end of the file
__all__ = ['forms','scalar','bootstrap','models','views','database']

#intialize database
initialize_database(app)

#initialize celery
initialize_celery(app)

#must happen last
from app.home.views import mod as homeModule
from app.forms.views import mod as formsModule
from app.scalar.views import mod as scalarModule
app.register_blueprint(homeModule)
app.register_blueprint(formsModule)
app.register_blueprint(scalarModule)

