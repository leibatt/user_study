import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from contextlib import contextmanager 

engine = None
Session = sqlalchemy.orm.sessionmaker(autocommit=False,autoflush=False)

Base = sqlalchemy.ext.declarative.declarative_base()

def configure_engine(uri):
  global Session, engine
  engine = sqlalchemy.create_engine(uri,echo=False,convert_unicode=True)
  Session.configure(bind=engine)

def init_db():
  import queue.models
  Base.metadata.create_all(bind=engine)

def initialize_database(uri):
    #initialize database
    configure_engine(uri)
    init_db()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""                   
    session = Session()
    try:
        yield session
        #session.commit()                                                                
    except:                                                                              
        session.rollback()
        raise                                                                            
    finally:
        session.close()  
