import json
import traceback
import scidb_server_interface as sdbi
import scalar_tile_interface as sti
from multiprocessing import Queue

DEBUG = True

def fetch_first_tile(fargs,job_id,q):
  query = str(fargs['query'])
  options = fargs['options']
  user_metadata = options['user_metadata']
  if user_metadata['threshold'] < 0:
    user_metadata['threshold'] = sdbi.D3_DATA_THRESHOLD

  db = sdbi.scidbOpenConn()
  sdbioptions = {'afl':False,'db':db}
  saved_qpresults = sdbi.verifyQuery(query,sdbioptions)
  sdbi.scidbCloseConn(db)
  tile = None

  if DEBUG: print "saved qp results, looking for error"
  if 'error' in saved_qpresults:
    if DEBUG: print "error found, returning error:",saved_qpresults
    tile = saved_qpresults
  else:
    if DEBUG: print "saved_qpresults:",saved_qpresults
  # user metadata does not contain saved_qpresults at this point, store it
    user_metadata['saved_qpresults'] = saved_qpresults
    #get tile
    base_id = [0] * saved_qpresults['numdims']
    if DEBUG: print "base id:",base_id
    if 'usenumpy' in options:
      usenumpy = options['usenumpy']
    else:
      usenumpy = False
    tile = sti.getTileByIDN(base_id,0,user_metadata,usenumpy)
  result = {
    'fail': ('error' in tile),
    'job_id':job_id,
    'current_tile_id': base_id,
    'current_zoom': 0,
    'tile': tile,
    'query': query,
    'threshold': user_metadata['threshold']
  }
  #return tile
  q.put(result)


#this is called after original query is run
def fetch_tile(fargs,job_id,q):
  tile_id = fargs['tile_id']
  level = fargs['level']
  options = fargs['options']
  user_metadata = options['user_metadata']
  if 'usenumpy' in options:
    usenumpy = options['usenumpy']
  else:
    usenumpy = False
  tile = sti.getTileByIDN(tile_id,level,user_metadata,usenumpy)
  result = {
    'fail': ('error' in tile),
    'job_id':job_id,
    'current_tile_id': tile_id,
    'current_zoom': level,
    'tile': tile,
    'query': user_metadata['original_query'],
    'threshold': user_metadata['threshold']
  }
  q.put(result)
 
if __name__ == "__main__":
  user_metadata = {
    "saved_qpresults":None,
    "threshold":10000,
    "original_query":"select * from cali100",
    "user_id":"5426925e-a74d-4b1d-83a3-c660ee45bf9a",
    "total_zoom_levels":0
  }
  options = {
    "user_metadata":user_metadata
  }
  tile = fetch_first_tile("select * from cali100",options)
  if DEBUG: print "k:",tile['threshold'],",l:",tile['max_zoom']
  #print "data:",tile['data']

