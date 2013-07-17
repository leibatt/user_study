from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base
#import datetime

#table storing all users by flask session id,
#and whether they did the surveys
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    #has to have a valid session id
    flask_session_id = Column(String(50),unique=True, nullable=False)
    done = Column(Boolean)

    def __init__(self, flask_session_id):
        self.flask_session_id = flask_session_id
        self.done = False

    def __repr__(self):
        return "User(%r,%r)" % (self.flask_session_id,self.done)

# predetermined data sets
class DataSet(Base):
    __tablename__ = "data_sets"
    id = Column(Integer,primary_key=True)
    name = Column(String(50),unique=True,nullable=False)
    query = Column(Text,unique=True,nullable=False)

    def __init__(self,name,query):
        self.name = name
        self.query = query

    def __repr__():
        return "DataSet(%r, %r)" % (self.name,self.query)



