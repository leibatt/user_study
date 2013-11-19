import os
import errno
import hashlib
from Queue import Empty as QueueEmptyException
from multiprocessing import Process, Queue
from scalar_worker_functions import fetch_first_tile as fft, fetch_tile as ft
from scidb_server_interface import D3_DATA_THRESHOLD
from functools import wraps
import database as db
import json
from time import sleep

DEBUG = True

cache_root_dir = '_scalar_cache_dir'
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

# hashes a string
def hash_it(s):
  h = hashlib.md5()
  h.update(str(s))
  return h.hexdigest()

def cache_insert_file(result):
  # only cache successful queries
  if not result['fail']:
    # hash string-based properties
    hashed_query = hash_it(result['query'])
    if DEBUG: print str(result['query']),",",hashed_query
    hashed_tile_id = hash_it(result['current_tile_id'])
    if DEBUG: print str(result['current_tile_id']),",",hashed_tile_id

    threshold = int(result['threshold'])
    zoom = int(result['current_zoom'])

    # tile to cache
    tile = result['tile']
    if DEBUG: print "k:",tile['threshold'],",l:",tile['max_zoom']

    # build directory location
    d = os.path.join(cache_root_dir, hashed_query, str(threshold), str(zoom))
    # successfully created, or already exists
    if setup_cache_directory(d):
      f = os.path.join(d,hashed_tile_id)
      # only write if file doesn't already exist
      if not os.path.isfile(f):
        with open(f,'w') as outf:
          outf.write(json.dumps(tile))

  else: # it's an error object, just return it as is
    if DEBUG: print "error found"

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

def cache_retrieve_file(fargs):
  f = None
  try:
    user_metadata = fargs['options']['user_metadata']
    saved_qpresults = user_metadata['saved_qpresults']
    query = user_metadata['original_query']
    if 'query' in fargs:
      query = fargs['query']

    # this is a hack for fft requests (no saved_qpresults yet!)
    n = 2 # assume 2d
    if (saved_qpresults is not None) and ('numdims' in saved_qpresults):
      n = int(saved_qpresults['numdims'])

    tile_id = [0] * n
    level = 0
    if ('tile_id' in fargs) and ('level' in fargs):
      tile_id = fargs['tile_id']
      level = int(fargs['level'])
    hashed_tile_id = hash_it(tile_id)
    hashed_query = hash_it(query)
    threshold = int(user_metadata['threshold'])
    if threshold < 0:
      threshold = D3_DATA_THRESHOLD
    f = os.path.join(cache_root_dir, hashed_query, str(threshold), 
      str(level), hashed_tile_id)
  except Exception as e:
    if DEBUG: print "could not build cache index:",e

  if f is None:
    return None
  try:
    result = ''
    with open(f,'r') as in_f:
      for line in in_f:
        result += line # includes newline chars from original file
    return json.loads(result)
  except Exception as e:
    if DEBUG: print "could not read tile from disk:",e
    return None

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
  #tile = cache_retrieve(fargs)
  tile = cache_retrieve_file(fargs)
  if tile is not None:
    if DEBUG: print "found cached result for job %d" % (job_id)
    return_result(dbq,{'tile':tile,'job_id':job_id,'fail':False})
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
    tile = result['tile']
    if result['fail']:
      dbq.setJobRecordFail(job_id,result)
    else:
      if DEBUG: print "data:",tile['data'][:10]
      dbq.setJobRecordSuccess(job_id,tile)

# must happen in main thread to avoid race conditions
def setup_cache_directory(d):
  try:
    os.makedirs(d)
    return True
  except OSError as e:
    # is some error other than already exists
    if e.errno != errno.EEXIST:
      print e
      return False
    # if it already exists, make sure it's a directory
    # this is not thread safe! only run in main thread
    elif not os.path.isdir(d):
      print e
      return False
    else: # directory already exists
      return True

if __name__ == "__main__":
  # setup
  # get job queue object
  dbq = JobsQueue()
  # queue used to write answers to cache
  result_queue = Queue()
  # setup cache directory

  # main loop
  tracker = 0
  maxtrack = 5
  sleeptime = .5 # 500 ms
  while(True):
    #step 1: check for queued jobs
    if DEBUG:
      if (tracker == 0):
        print "queued jobs:",len(dbq) # print total jobs in queue
      tracker += 1
      if tracker == (maxtrack - 1):
        tracker = 0
    for i in range(2): # start up to 2 new jobs
      next_job = dbq.popNextQueuedJob() # get the next queued job
      if next_job is not None:
        if DEBUG: print "next queued job:",next_job
        start_job(next_job,dbq,result_queue)
      #else:
      #  if DEBUG: print "no new jobs"

    #step 2: check for finished results in the result queue
    for i in range(10): # remove up to 10 items from the queue
      try:
        result = result_queue.get(timeout=1) # waits for a result
        #cache_insert(result)
        cache_insert_file(result)
        return_result(dbq,result)
      except QueueEmptyException: # didn't find anything
        #if DEBUG: print "result queue is empty"
        break

        sleep(sleeptime)
  
