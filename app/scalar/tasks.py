from app.util.queue.queue_obj import JobsQueue
import json

fmap = {
  'fft':0,
  'ft':1
}

class JobWrapper(object):
  def __init__(self,func_str,db_session):
    self.fid = fmap[func_str]
    self.db_session = db_session
    self.job_record = None
    self.FINISHED = False
    self.FAILED = False
    self.jid = None

  def run(self,input_dict):
    q = JobsQueue(self.db_session)
    self.jid = q.addJobRecord(self.fid,input_dict)

  def peek(self,jid):
    q = JobsQueue(self.db_session)
    # peek at the job record, but don't make any changes
    self.FINISHED = q.checkJobFinished(jid)
    if self.FINISHED:
      self.FAILED = q.checkJobFail(jid) # see if the job failed
      self.job_record = q.getJobRecord(jid)

  def job_id(self):
    return self.jid

  def finished(self):
    return self.FINISHED

  def failed(self):
    return self.FAILED

  # get the job result
  # we know that after at this point that the job record is no longer needed
  def result(self):
    if self.job_record is None:
      return None
    raw_results_string = self.job_record.job_result
    return json.loads(raw_results_string)

class Fft(JobWrapper):
  def __init__(self,db_session):
    super(Fft,self).__init__('fft',db_session)

  def run(self,query,options):
    input_dict = {'query':query,'options':options}
    super(Fft,self).run(input_dict)

class Ft(JobWrapper):
  def __init__(self,db_session):
    super(Ft,self).__init__('ft',db_session)

  def run(self,tile_id,level,options):
    input_dict = {
      'tile_id':tile_id,
      'level':level,
      'options':options
    }
    super(Ft,self).run(input_dict)

# wrapper for storing metadata on the user
class TileMetadata(object):
  #def __init__(self,user_id,queryresultarr,threshold,query,dataset_id):
  def __init__(self):
    self.user_id = None
    self.saved_qpresults = None
    self.current_tile_id = [0,0]
    self.current_zoom_level = 0
    self.total_zoom_levels = 0
    self.threshold = -1
    self.original_query = None
    #self.dataset_id = None
    self.image = None

  def get_dict(self):
    return {
      'user_id': self.user_id,
      'saved_qpresults': self.saved_qpresults,
      'current_tile_id': self.current_tile_id,
      'current_zoom_level': self.current_zoom_level,
      'total_zoom_levels': self.total_zoom_levels,
      'threshold': self.threshold,
      'original_query': self.original_query,
      #'dataset_id': self.dataset_id,
      'image': self.image
    }

  def load_dict(self,d):
    self.user_id = d['user_id']
    self.saved_qpresults = d['saved_qpresults']
    self.total_zoom_levels = d['total_zoom_levels']
    self.threshold = d['threshold']
    self.original_query = d['original_query']
    self.current_tile_id = d['current_tile_id']
    self.current_zoom_level = d['current_zoom_level']
    #self.dataset_id = d['dataset_id']
    self.image = d['image']

