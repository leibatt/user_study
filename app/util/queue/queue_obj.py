from app.util.database.database import db_session
from app.util.queue.models import QueuedJobStatus, JobRecord, QueuedJob
import os
from time import sleep
import json
import datetime
from functools import wraps

# class holding functions for interacting with the queue.
# note that this code assumes the db_session scope is managed 
# elsewhere (i.e. database is initialized and sessions setup/scoped
# somewhere else globally)
class JobsQueue(object):
  def __init__(self,db_session,manage_transactions=False):
    self.db_session = db_session
    self.manage_transactions = manage_transactions

  #decorator to handle db_session refresh if necessary
  def getNewSession(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
      self = args[0]
      result = f(*args,**kwargs)
      if(self.manage_transactions):
        self.db_session.remove()
      return result
    return decorated_function

  @getNewSession
  def __len__(self):
    all_jobs = self.db_session.query(QueuedJob).all()
    return len(all_jobs)

  # creates a new job record, and adds the new job to the queue.
  # returns the id assigned to the new job
  @getNewSession
  def addJobRecord(self, function_id, function_inputs_dict):
    try:
      new_job = JobRecord(function_id,json.dumps(function_inputs_dict))
      self.db_session.add(new_job)
      self.db_session.commit()
    except:
      return -1
    try:
      new_queued_job = QueuedJob(new_job.id)
      self.db_session.add(new_queued_job)
      self.db_session.commit()
      print new_job
      print new_queued_job
    except:
      self.db_session.delete(new_job)
      self.db_session.commit()
      return -1

    return new_job.id
  
  # outward facing function for getting job record
  @getNewSession
  def getJobRecord(self,job_id):
    return self.__get_job_record(job_id)

  @getNewSession
  def removeJobRecord(self,job_id):
    job_record = self.__get_job_record(job_id)
    self.db_session.delete(job_record)
    self.db_session.commit()
    return job_record

  @getNewSession
  def setJobRecordFail(self, job_id, error):
    self.__set_job_record_status(job_id, QueuedJobStatus.FAIL, error)
  
  @getNewSession
  def setJobRecordStarted(self, job_id):
    self.__set_job_record_status(job_id, QueuedJobStatus.STARTED)

  @getNewSession
  def setJobRecordSuccess(self, job_id, result):
    self.__set_job_record_status(job_id, QueuedJobStatus.SUCCESS, result)
   
  # returns record associated with next job in the queue
  # and removes this job from the queue.
  @getNewSession
  def popNextQueuedJob(self):
    try:
      if self.__len__() == 0:
        return None
      queued_job = self.__get_next_queued_job()
      queued_job_record = self.__get_job_record(queued_job.job_id)
      self.db_session.delete(queued_job) # remove this job from the queue
      self.db_session.commit()
      return queued_job_record
    except:
      return None

  @getNewSession
  def checkJobFinished(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status in [QueuedJobStatus.FAIL, QueuedJobStatus.SUCCESS]

  @getNewSession
  def checkJobSuccess(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status == QueuedJobStatus.SUCCESS

  @getNewSession
  def checkJobFail(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status == QueuedJobStatus.FAIL

  ######## helper functions ########
  # helper functions should only be used inside
  # decorated class functions

  def __get_job_record(self,job_id):
    return self.db_session.query(JobRecord).filter_by(id=job_id).one()

  def __get_next_queued_job(self):
    return self.db_session.query(QueuedJob).order_by(QueuedJob.id).first()

  def __set_job_record_status(self, job_id, status, result = None):
    job_record = self.__get_job_record(job_id)
    job_record.job_status = status
    if status in [QueuedJobStatus.FAIL, QueuedJobStatus.SUCCESS]:
      job_record.job_result = json.dumps(result)
      job_record.timestamp = datetime.datetime.now()
    self.db_session.commit()

  # returns integer representing the status of this job.
  # see model file for status definitions.
  def __check_job_status(self, job_id):
    job = self.__get_job_record(job_id)
    return job.job_status

