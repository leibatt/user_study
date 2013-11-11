from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from database import Base
import datetime

# for assessing job status
class QueuedJobStatus():
  WAITING = 0
  STARTED = 1
  SUCCESS = 2
  FAIL = -1
  pass

class JobRecord(Base):
  __tablename__ = "job_records"
  id = Column(Integer, primary_key=True)
  function_id = Column(Integer,nullable=False)
  function_inputs = Column(Text) # can be null
  job_status = Column(Integer,nullable=False)
  job_result = Column(Text) # can be null
  timestamp = Column(DateTime) # when the success/fail status was recorded

  # create a new job
  def __init__(self,function_id,function_inputs=None):
    self.function_id = function_id
    self.function_inputs = function_inputs
    self.job_status = QueuedJobStatus.WAITING
    self.job_result = None # make output null for now
    self.timestamp = None # only use for success/fail status

  def __repr__(self):
    return "JobRecord(%r, %r, %r, %r, %r, %r)" % (self.id, self.function_id,
      self.function_inputs, self.job_status, self.job_result, self.timestamp)

class QueuedJob(Base):
  __tablename__ = "queued_jobs"
  id = Column(Integer, primary_key=True)
  job_id = Column(Integer, ForeignKey("job_records.id"), nullable = False)
  # each job should only be in the queue once!
  __table_args__ = (UniqueConstraint('job_id', name='queue_unique'),)

  # add an existing job record to the queue for execution
  def __init__(self, job_id):
    self.job_id = job_id

  def __repr__(self):
    return "QueuedJob(%r)" % (self.job_id)

