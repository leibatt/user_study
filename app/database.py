import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from flask import current_app

engine = None
sessionmaker = sqlalchemy.orm.sessionmaker(autocommit=False,autoflush=False)
#engine = sqlalchemy.create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'],echo=True,convert_unicode=True)
#engine = sqlalchemy.create_engine('sqlite:///data/sqlite/temp.db',echo=True,convert_unicode=True)
#engine = sqlalchemy.create_engine('sqlite:///:memory:',echo=True,convert_unicode=True)

#should only be called once globally or at module level
db_session = sqlalchemy.orm.scoped_session(sessionmaker)

Base = sqlalchemy.ext.declarative.declarative_base()
Base.query = db_session.query_property()

def configure_engine(uri):
	global sessionmaker, db_session, engine
	engine = sqlalchemy.create_engine(uri,echo=True,convert_unicode=True)
	sessionmaker.configure(bind=engine)
	db_session.remove()

def init_db():
	import app.models #base models
	import app.forms.models
	import app.scalar.models
	Base.metadata.create_all(bind=engine)
