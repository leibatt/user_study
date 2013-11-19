import os
import errno
import hashlib
from Queue import Empty as QueueEmptyException
from multiprocessing import Process, Queue
from scidb_server_interface import D3_DATA_THRESHOLD
from cache_worker_functions import compute_tile, compute_first_tile, list_all_tiles, get_tile_counts
import database as db
import json
from time import sleep

DEBUG = True

cache_root_dir = '_scalar_cache_dir'
uri = 'postgresql+psycopg2://testuser:password@localhost:5432/test'
db.initialize_database(uri)

queries = ["select * from cali100"] # list of dataset names
data_thresholds = [D3_DATA_THRESHOLD] # list of thresholds (ints)

QUEUE_MARKER = "END"

sleeptime = 2

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
      else:
        if DEBUG: print "file %s already exists" % (f)

  else: # it's an error object, just return it as is
    if DEBUG: print "error found"

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

def get_all_metadata(cache_queue,metadata_queue):
  # get metadata for all queries and threshold values
  jobs = []
  for q in queries:
    for d in data_thresholds:
      fargs = {
        'query':q,
        'threshold':d
      }
      p = Process(target=compute_first_tile,args=(fargs,metadata_queue))
      jobs.append(p)
      p.start()
  if DEBUG: print "waiting..."
  for j in jobs:
    j.join()
  metadata_queue.put(QUEUE_MARKER) # marker to know we are done
  if DEBUG: print "got all metadata"

def get_metadata_objects(metadata_queue):
  done = False
  metadata_objects = []
  while(not done):
    try:
      metadata_dict = metadata_queue.get(timeout=1) # waits for a result
      if metadata_dict != QUEUE_MARKER:
        if metadata_dict is not None:
          metadata_objects.append(metadata_dict)
      else:
        done = True
    except QueueEmptyException: # didn't find anything
      #if DEBUG: print "metadata queue is currently empty"
      sleep(sleeptime)
  return metadata_objects

def get_total_jobs(metadata_queue):
  total_jobs = 0
  done = False
  jobs = []
  metadata_objects = get_metadata_objects(metadata_queue)
  for metadata_dict in metadata_objects:
    fargs = {
      'user_metadata':metadata_dict
    }
    p = Process(target=get_tile_counts,args=(fargs,metadata_queue))
    jobs.append(p)
    p.start()

  for j in jobs:
    j.join()
  metadata_queue.put(QUEUE_MARKER)
  metadata_objects = get_metadata_objects(metadata_queue)
  for metadata_dict in metadata_objects:
    total_jobs += metadata_dict['tile_count']
    metadata_queue.put(metadata_dict)
  metadata_queue.put(QUEUE_MARKER)
  if DEBUG: print "total jobs:",total_jobs
  return total_jobs

def setup_all_jobs(metadata_queue,jobs_queue):
  done = False
  jobs = []
  metadata_objects = get_metadata_objects(metadata_queue)
  for metadata_dict in metadata_objects:
    fargs = {
      'user_metadata':metadata_dict
    }
    p = Process(target=list_all_tiles,args=(fargs,jobs_queue))
    jobs.append(p)
    p.start() # don't wait for p to finish, pipe could be too full
  return jobs

# checks if a list of jobs is done
def check_done(jobs):
  done = True
  for j in jobs:
    if j.is_alive():
      done = False
      break
  if done:
    for j in jobs:
      j.join()
  return done

def run_jobs(jobs_queue,cache_queue):
  jobs = []
  for i in range(2):
    try:
      job = jobs_queue.get(timeout=.5) # waits for a result
      if job is not None:
        fargs = job
        p = Process(target=compute_tile,args=(fargs,cache_queue))
        jobs.append(p)
        p.start() # don't wait for p to finish, pipe could be too full
        print "got here"
    except QueueEmptyException: # didn't find anything
      if DEBUG: print "jobs queue is empty"
      break
  return jobs

def cache_results(cache_queue):
  done_jobs = 0
  for i in range(10):
    try:
      result = cache_queue.get(timeout=sleeptime) # waits for a result
      cache_insert_file(result)
      done_jobs += 1
    except QueueEmptyException: # didn't find anything
      #if DEBUG: print "metadata queue is empty"
      break
  return done_jobs

if __name__ == "__main__":
  # setup
  # queue used to schedule jobs for caching specific tiles
  jobs_queue = Queue()
  # queue used to write answers to cache
  cache_queue = Queue()
  # queue used to collect metadata for all queries
  metadata_queue = Queue()
  # setup cache directory
  dir_exists = setup_cache_directory(cache_root_dir)

  if not dir_exists:
    print "directory %s does not exist " % (cache_root_dir)
    exit(1)

  get_all_metadata(cache_queue,metadata_queue)
  #tell us when we're done
  total_jobs = get_total_jobs(metadata_queue)
  setup_jobs = setup_all_jobs(metadata_queue,jobs_queue)
  done_jobs = 0

  while done_jobs <= 4:
    print "running more jobs"
    jobs_run = run_jobs(jobs_queue,cache_queue)
    done_jobs += cache_results(cache_queue)
    print "jobs done?:",check_done(jobs_run)
    print "total cached results:",done_jobs
    sleep(sleeptime)
  print "got to the end"


