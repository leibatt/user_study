import os
import errno
import hashlib
from Queue import Empty as QueueEmptyException
from multiprocessing import Process, Queue
from scidb_server_interface import D3_DATA_THRESHOLD
from cache_worker_functions import compute_tile, compute_first_tile, list_all_tiles, get_tile_counts, TileMetadata
import database as db
import json
from time import sleep

DEBUG = True

cache_root_dir = '_scalar_cache_dir2'
uri = 'postgresql+psycopg2://testuser:password@localhost:5432/test'
db.initialize_database(uri)

queries = ["select * from cali100"] # list of dataset names
data_thresholds = [D3_DATA_THRESHOLD] # list of thresholds (ints)

QUEUE_MARKER = "END"

sleeptime = 20
maxpool = 2

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
    #if DEBUG: print str(result['query']),",",hashed_query
    hashed_tile_id = hash_it(result['current_tile_id'])
    #if DEBUG: print str(result['current_tile_id']),",",hashed_tile_id

    threshold = int(result['threshold'])
    zoom = int(result['current_zoom'])

    # tile to cache
    tile = result['tile']
    #if DEBUG: print "k:",tile['threshold'],",l:",tile['max_zoom']

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
      if DEBUG: print e
      return False
    # if it already exists, make sure it's a directory
    # this is not thread safe! only run in main thread
    elif not os.path.isdir(d):
      if DEBUG: print e
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
      sleep(2)
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
  for i in range(maxpool):
    try:
      job = jobs_queue.get(timeout=.5) # waits for a result
      if job is not None:
        fargs = job
        p = Process(target=compute_tile,args=(fargs,cache_queue))
        jobs.append(p)
        p.start() # don't wait for p to finish, pipe could be too full
    except QueueEmptyException: # didn't find anything
      if DEBUG: print "jobs queue is empty"
      break
  return jobs

def print_all_datasets(metadata_queue):
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
    fargs = {
      'user_metadata':metadata_dict
    }
    print_all_tiles(fargs)

def print_all_tiles(fargs):
  user_metadata = TileMetadata()
  user_metadata.load_dict(fargs['user_metadata'])
  saved_qpresults = user_metadata.saved_qpresults
  total_levels = int(user_metadata.total_zoom_levels)
  levels = range(total_levels)
  #levels = [0,1]
  if DEBUG: print "levels:",levels
  if DEBUG: print "total tiles:",user_metadata.total_tiles
  base_id = [0] * saved_qpresults['numdims']
  query = user_metadata.original_query
  threshold = user_metadata.threshold
  for level in levels:
    # don't let this cause errors
    try: # get the first tile at each remaining level
      #list of total tiles along each dimension
      total_tiles = user_metadata.total_tiles[level]
      #for every remaining tile on this level
      for i in range(int(total_tiles[0])): # assume 2 dimensions for now
        for j in range(int(total_tiles[1])):
          #new_id = [i,j]
          #if DEBUG: print "coord:",new_id
          new_id = '['+str(i)+', '+str(j)+']'
          print '%s\t%s\t%s\t%s\t%d\t%d' % (query,str(hash_it(query)),new_id,str(hash_it(new_id)),level,threshold)
    except Exception as e:
      if DEBUG: print "error occured:",e

def cache_results(cache_queue):
  done_jobs = 0
  for i in range(10):
    try:
      result = cache_queue.get(timeout=.5) # waits for a result
      cache_insert_file(result)
      done_jobs += 1
    except QueueEmptyException: # didn't find anything
      #if DEBUG: print "cache queue is empty"
      break
  return done_jobs

def printmain():
  metadata_queue = Queue()
  cache_queue = Queue()
  dir_exists = setup_cache_directory(cache_root_dir)
  if not dir_exists:
    if DEBUG: print "directory %s does not exist " % (cache_root_dir)
    exit(1)

  get_all_metadata(cache_queue,metadata_queue)
  print_all_datasets(metadata_queue)

def main():
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
    if DEBUG: print "directory %s does not exist " % (cache_root_dir)
    exit(1)

  get_all_metadata(cache_queue,metadata_queue)
  #tell us when we're done
  total_jobs = get_total_jobs(metadata_queue)
  setup_jobs = setup_all_jobs(metadata_queue,jobs_queue)
  done_jobs = 0
  jobs_run = []
  current_jobs_done = True

  while done_jobs < total_jobs:
    new_results_count = cache_results(cache_queue) # store any new tiles
    if new_results_count > 0: # any newly cached tiles?
      done_jobs += new_results_count
      if DEBUG: print "total cached results:",done_jobs
    if current_jobs_done: # if currently running jobs have finished
      jobs_run = run_jobs(jobs_queue,cache_queue) # start new jobs
      if DEBUG: print "running %d new jobs" % (len(jobs_run))
    sleep(sleeptime) # wait for jobs for a while
    current_jobs_done = check_done(jobs_run) # see if the current jobs are done
    if DEBUG: print "current jobs done?:",current_jobs_done
  if DEBUG: print "got to the end"

if __name__ == "__main__":
  #main()
  printmain()

