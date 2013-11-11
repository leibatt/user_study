from database import Session, session_scope
from queue.models import QueuedJobStatus, JobRecord, QueuedJob
import os
from time import sleep
import json
import datetime


# class holding functions for interacting with the queue.
# note that this code assumes the db_session scope is managed 
# elsewhere (i.e. database is initialized and sessions setup/scoped
# somewhere else globally)
class JobsQueue(object):
  def __init__(self):
    pass

  def __len__(self):
    with session_scope() as db_session:
      all_jobs = db_session.query(QueuedJob).all()
      return len(all_jobs)

  # creates a new job record, and adds the new job to the queue.
  # returns the id assigned to the new job
  def addJobRecord(self, function_id, function_inputs_dict):
    with session_scope() as db_session:
      jid = None
      try:
        new_job = JobRecord(function_id,json.dumps(function_inputs_dict))
        db_session.add(new_job)
        db_session.commit()
      except:
        jid= -1
      try:
        new_queued_job = QueuedJob(new_job.id)
        db_session.add(new_queued_job)
        db_session.commit()
        jid = new_job.id
      except:
        db_session.delete(new_job)
        db_session.commit()
        jid = -1
      return jid

  # outward facing function for getting job record
  def getJobRecord(self,job_id):
    return self.__get_job_record(job_id)

  def removeJobRecord(self,job_id):
    job_record = self.__get_job_record(job_id)
    with session_scope() as db_session:
      db_session.delete(job_record)
      db_session.commit()
      return job_record

  def setJobRecordFail(self, job_id, error):
    self.__set_job_record_status(job_id, QueuedJobStatus.FAIL, error)
  
  def setJobRecordStarted(self, job_id):
    self.__set_job_record_status(job_id, QueuedJobStatus.STARTED)

  def setJobRecordSuccess(self, job_id, result):
    self.__set_job_record_status(job_id, QueuedJobStatus.SUCCESS, result)
   
  # returns record associated with next job in the queue
  # and removes this job from the queue.
  def popNextQueuedJob(self):
    if self.__len__() == 0:
      return None
    try:
      queued_job = self.__get_next_queued_job()
      queued_job_record = self.__get_job_record(queued_job.job_id)
      with session_scope() as db_session:
        db_session.delete(queued_job) # remove this job from the queue
        db_session.commit()
        return queued_job_record
    except:
      return None

  def checkJobFinished(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status in [QueuedJobStatus.FAIL, QueuedJobStatus.SUCCESS]

  def checkJobSuccess(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status == QueuedJobStatus.SUCCESS

  def checkJobFail(self, job_id):
    job_status =  self.__check_job_status(job_id)
    return job_status == QueuedJobStatus.FAIL

  ######## helper functions ########
  # helper functions should only be used inside
  # decorated class functions

  def __get_job_record(self,job_id):
    with session_scope() as db_session:
      return db_session.query(JobRecord).filter_by(id=job_id).one()

  def __get_next_queued_job(self):
    with session_scope() as db_session:
      return db_session.query(QueuedJob).order_by(QueuedJob.id).first()

  def __set_job_record_status(self, job_id, status, result = None):
    job_record = self.__get_job_record(job_id)
    job_record.job_status = status
    if status in [QueuedJobStatus.FAIL, QueuedJobStatus.SUCCESS]:
      job_record.job_result = json.dumps(result)
      job_record.timestamp = datetime.datetime.now()
    with session_scope() as db_session:
      db_session.add(job_record)
      db_session.commit()

  # returns integer representing the status of this job.
  # see model file for status definitions.
  def __check_job_status(self, job_id):
    job = self.__get_job_record(job_id)
    return job.job_status

