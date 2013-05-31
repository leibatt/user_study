from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.database import Base
from app.models import User, DataSet
import datetime

# user movement history
class UserTrace(Base):
	__tablename__ = "user_traces"
	id = Column(Integer,primary_key=True)
	tile_id = Column(Text,nullable=False)
        zoom_level = Column(Integer,nullable=False)
	timestamp = Column(DateTime(timezone=True),nullable=False)
	query = Column(Text,nullable=False) # must know what query was run
	user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
	dataset_id = Column(Integer,ForeignKey("data_sets.id")) # dataset used? may be null, but hopefully isn't

	user = relationship("User",backref=backref("traces"))
	dataset = relationship("DataSet",backref=backref("traces"))

	def __init__(self,tile_id,zoom_level,query,user_id,dataset_id):
		self.user_id = user_id
		self.tile_id = tile_id
		self.zoom_level = zoom_level
		self.timestamp = datetime.datetime.now()
		self.query = query
		self.dataset_id = dataset_id

	def __repr__():
		return "UserTrace(%r, %r, %r, %r, %r, %r)" % (self.user_id,self.tile_id,self.query,self.dataset_id,self.timestamp)

class UserTileSelection(Base):
	__tablename__ = "user_tile_selections"
	id = Column(Integer,primary_key=True)
	tile_id = Column(Text,nullable=False)
        zoom_level = Column(Integer,nullable=False)
	timestamp = Column(DateTime(timezone=True),nullable=False)
	query = Column(Text,nullable=False) # must know what query was run
	image = Column(Text) # image of the tile in base64 encoded string
        x_label = Column(String)
        y_label = Column(String)
        z_label = Column(String)
        x_inv = Column(Boolean)
        y_inv = Column(Boolean)
        z_inv = Column(Boolean)
        color = Column(String(100))
        width = Column(Integer)
        height = Column(Integer)
	user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
	dataset_id = Column(Integer,ForeignKey("data_sets.id")) # dataset used? may be null, but hopefully isn't

	user = relationship("User",backref=backref("tile_selections"))
	dataset = relationship("DataSet",backref=backref("tile_selections"))

	__table_args__ = (UniqueConstraint('tile_id','zoom_level','query','user_id', name='uix_3'),)

	def __init__(self,tile_id,zoom_level,query,user_id,dataset_id,image):
		self.user_id = user_id
		self.tile_id = tile_id
		self.zoom_level = zoom_level
		self.timestamp = datetime.datetime.now()
		self.query = query
		self.dataset_id = dataset_id
		self.image = image
               
	def __repr__(self):
		return "UserTileSelection(%r, %r, %r, %r, %r, %r)" % (self.user_id,self.tile_id,self.query,self.dataset_id,self.timestamp)

class UserTileUpdate(Base):
	__tablename__ = "user_tile_updates"
	id = Column(Integer,primary_key=True)
	tile_id = Column(Text,nullable=False)
        zoom_level = Column(Integer,nullable=False)
	timestamp = Column(DateTime(timezone=True),nullable=False)
	query = Column(Text,nullable=False) # must know what query was run
        x_label = Column(String)
        y_label = Column(String)
        z_label = Column(String)
        x_inv = Column(Boolean)
        y_inv = Column(Boolean)
        z_inv = Column(Boolean)
        color = Column(String(100))
        width = Column(Integer)
        height = Column(Integer)
	user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
	dataset_id = Column(Integer,ForeignKey("data_sets.id")) # dataset used? may be null, but hopefully isn't

	user = relationship("User",backref=backref("tile_updates"))
	dataset = relationship("DataSet",backref=backref("tile_updates"))

	#__table_args__ = (UniqueConstraint('tile_id','zoom_level','query','user_id', name='uix_4'),)

	def __init__(self,tile_id,zoom_level,query,user_id,dataset_id):
		self.user_id = user_id
		self.tile_id = tile_id
		self.zoom_level = zoom_level
		self.timestamp = datetime.datetime.now()
		self.query = query
		self.dataset_id = dataset_id
               
	def __repr__(self):
		return "UserTileUpdate(%r, %r, %r, %r, %r)" % (self.user_id,self.tile_id,self.query,self.dataset_id,self.timestamp)

