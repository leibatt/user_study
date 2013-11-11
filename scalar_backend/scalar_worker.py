from Queue import Empty as QueueEmptyException
from multiprocessing import Process, Queue
from scalar_worker_functions import fetch_first_tile as fft, fetch_tile as ft
from functools import wraps
import database as db
import json
from time import sleep

DEBUG = True

uri = 'postgresql+psycopg2://testuser:password@localhost:5432/test'
db.initialize_database(uri)
from queue.queue_obj import JobsQueue

# maps function id's to their proper functions
fmap = {
  0:fft,
  1:ft
}

# cache access: query, threshold, tile, zoom
result_cache = {}
result_cache_size = 0

def cache_insert(result):
  # only cache successful queries
  if 'error' not in result:
    query = result['query']
    threshold = result['threshold']
    zoom = result['current_zoom']
    tile_id = str(result['current_tile_id'])
    if query not in result_cache:
      result_cache[query] = {}
    if threshold not in result_cache[query]:
      result_cache[query][threshold] = {}
    if zoom not in result_cache[query][threshold]:
      result_cache[query][threshold][zoom] = {}
    if tile_id not in result_cache[query][threshold][zoom]:
      result_cache[query][threshold][zoom][tile_id] = {}
      # only save if it's not already in the cache
      result_cache[query][threshold][zoom][tile_id] = result['tile']
    tile = result['tile']
    if DEBUG: print "k:",tile['threshold'],",l:",tile['max_zoom']
  else: # it's an error object, just return it as is
    if DEBUG: print "error found"

def cache_retrieve(fargs):
  try:
    user_metadata = fargs['options']['user_metadata']
    saved_qpresults = user_metadata['saved_qpresults']
    n = saved_qpresults['numdims']
    tile_id = [0] * n
    level = 0
    if ('tile_id' in fargs) and ('level' in fargs):
      tile_id = fargs['tile_id']
      level = fargs['level']
    tile_id = str(tile_id)
    query = user_metadata['original_query']
    threshold = user_metadata['threshold']
    return result_cache[query][threshold][level][tile_id]
  except Exception as e:
    if DEBUG: print "could not find tile in cache:",e
    return None

def start_job(job_record,dbq,result_queue):
  fargs = json.loads(job_record.function_inputs)
  job_id = job_record.id
  # see if it's cached
  tile = cache_retrieve(fargs)
  if tile is not None:
    if DEBUG: print "found cached result for job %d" % (job_id)
    return_result(dbq,{'tile':tile,'job_id':job_id})
    return
  # not cached, so compute it
  fid = job_record.function_id
  f = fmap[fid]
  p = Process(target=f,args=(fargs,job_id,result_queue))
  p.start()

def return_result(dbq,result):
  job_id = result.pop('job_id',None)
  if DEBUG: print "result:",json.dumps(result)[:30]
  if job_id is not None:
    if 'error' in result:
      dbq.setJobRecordFail(job_id,result)
    else:
      tile = result['tile']
      if DEBUG: print "data:",tile['data'][:10]
      dbq.setJobRecordSuccess(job_id,tile)

if __name__ == "__main__":
  dbq = JobsQueue() # get job queue object
  # queue used to write answers to cache
  result_queue = Queue()
  while(True):
    #step 1: check for finished results in the result queue
    for i in range(10): # remove up to 10 items from the queue
      try:
        result = result_queue.get(timeout=1) # waits for a result
        cache_insert(result)
        return_result(dbq,result)
      except QueueEmptyException: # didn't find anything
        if DEBUG: print "result queue is empty"
        break

    #step 2: check for queued jobs
    if DEBUG: print "queued jobs:",len(dbq) # print total jobs in queue
    next_job = dbq.popNextQueuedJob() # get the next queued job
    if next_job is not None:
      if DEBUG: print "next queued job:",next_job
      start_job(next_job,dbq,result_queue)
    else:
      if DEBUG: print "no new jobs"
    sleep(2)
  
