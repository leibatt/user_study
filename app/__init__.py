from flask import Flask
import app.database as db

app = Flask(__name__)
#add app configurations
app.config.from_object('config')

#initialize database
db.configure_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_db()

#setup logger
if not app.debug:
        file_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

# needs to be done at the end of the file
from app.views import mod as homeModule
from app.forms.views import mod as formsModule
from app.scalar.views import mod as scalarModule
app.register_blueprint(homeModule)
app.register_blueprint(formsModule)
app.register_blueprint(scalarModule)

