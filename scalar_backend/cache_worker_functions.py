import scalar_tile_interface as sti
import scidb_server_interface as sdbi

usenumpy = False
DEBUG = True

# wrapper function to handle querying scidb for metadata
def verify_query(query):
  saved_qpresults = None
  try:
    db = sdbi.scidbOpenConn()
    sdbioptions = {'afl':False,'db':db}
    saved_qpresults = sdbi.verifyQuery(query,sdbioptions)
    sdbi.scidbCloseConn(db)
  except Exception as e:
    if DEBUG: print "error occured:",e
    pass
  return saved_qpresults

# compute the given tile and return the result
def compute_tile(fargs,cache_queue):
  user_metadata = TileMetadata()
  user_metadata.load_dict(fargs['user_metadata'])
  query = user_metadata.original_query
  tile_id = fargs['tile_id']
  level = fargs['level']
  tile = None
  # don't let this cause errors
  if DEBUG: print "preparing to compute tile"
  try:
    tile = sti.getTileByIDN(tile_id,level,user_metadata.get_dict(),usenumpy)
    if DEBUG: print "tile computed"
  except Exception as e:
    if DEBUG: print "error occured:",e
    tile = None
  if DEBUG: print "building result"
  result = {
    'fail': ((tile is None) or ('error' in tile)),
    'current_tile_id': tile_id,
    'current_zoom': level,
    'tile': tile,
    'query': query,
    'threshold': user_metadata.threshold
  }
  if DEBUG: "placing result in cache queue"
  cache_queue.put(result)

# compute the very first tile, and return the metadata
def compute_first_tile(fargs, metadata_queue):
  query = fargs['query']
  threshold = fargs['threshold']
  tile = None
  metadata = None
  user_metadata =  TileMetadata()
  user_metadata.original_query = query
  user_metadata.threshold = threshold
  saved_qpresults = verify_query(query)
  if saved_qpresults is None:
    if DEBUG: print "saved_qpresults is none"
  elif 'error' in saved_qpresults:
    if DEBUG: print "error occurred when getting qpresults:",saved_qpresults
  else:
    user_metadata.saved_qpresults = saved_qpresults
    base_id = [0] * saved_qpresults['numdims']
    # don't let this cause errors
    try:
      # expects metadata in json format
      tile = sti.getTileByIDN(base_id,0,user_metadata.get_dict(),usenumpy)
      # record new total tiles and threshold values
      user_metadata.total_zoom_levels = tile['max_zoom']
      user_metadata.threshold = tile['threshold']
    except Exception as e:
      if DEBUG: print "error occured: when fetching first tile",e
  if tile is not None:
    metadata = user_metadata.get_dict()
  metadata_queue.put(metadata)

def get_tile_counts(fargs,metadata_queue):
  tile = None
  user_metadata = TileMetadata()
  user_metadata.load_dict(fargs['user_metadata'])
  saved_qpresults = user_metadata.saved_qpresults
  total_levels = int(user_metadata.total_zoom_levels)
  total_tiles_per_level = [None] * total_levels
  tile_count = 0
  levels = range(total_levels)
  base_id = [0] * saved_qpresults['numdims']
  for level in levels:
    c = 1
    # don't let this cause errors
    try: # get the first tile at each remaining level
      # expects metadata in json format
      tile = sti.getTileByIDN(base_id,level,user_metadata.get_dict(),usenumpy)
    except Exception as e:
      if DEBUG: print "error occured:",e
      return

    if tile is not None:
      #list of total tiles along each dimension
      total_tiles = tile['total_tiles']
      for tt in total_tiles:
        c *= tt
      tile_count += c
      total_tiles_per_level[level] = total_tiles
    else:
      if DEBUG: print "tile is None"
      return
  user_metadata.tile_count = int(tile_count)
  user_metadata.total_tiles = total_tiles_per_level
  if DEBUG: print "tile_count:",user_metadata.tile_count
  metadata_queue.put(user_metadata.get_dict())

def list_all_tiles(fargs,jobs_queue):
  tile = None
  user_metadata = TileMetadata()
  user_metadata.load_dict(fargs['user_metadata'])
  saved_qpresults = user_metadata.saved_qpresults
  total_levels = int(user_metadata.total_zoom_levels)
  levels = range(total_levels)
  if DEBUG: print "levels:",levels
  base_id = [0] * saved_qpresults['numdims']
  for level in levels:
    # don't let this cause errors
    try: # get the first tile at each remaining level
      #list of total tiles along each dimension
      total_tiles = user_metadata.total_tiles[level]
      #for every remaining tile on this level
      for i in range(int(total_tiles[0])): # assume 2 dimensions for now
        for j in range(int(total_tiles[1])):
          new_id = [i,j]
          #if DEBUG: print "coord:",new_id
          # put it in the job queue
          jobs_queue.put({
            'tile_id':new_id,
            'level':level,
            'user_metadata':user_metadata.get_dict()
          })
    except Exception as e:
      if DEBUG: print "error occured:",e

      
  # failsafe so job looks done
  jobs_queue.put(None)

# wrapper for storing metadata on the user
# based on object from the app codbase
class TileMetadata(object):
  #def __init__(self,user_id,queryresultarr,threshold,query,dataset_id):
  def __init__(self):
    self.saved_qpresults = None
    self.total_zoom_levels = 0
    self.threshold = -1
    self.original_query = None
    self.total_tiles = None
    self.tile_count = 0

  def get_dict(self):
    return {
      'saved_qpresults': self.saved_qpresults,
      'total_zoom_levels': self.total_zoom_levels,
      'threshold': self.threshold,
      'original_query': self.original_query,
      'total_tiles': self.total_tiles,
      'tile_count': self.tile_count
    }

  def load_dict(self,d):
    self.saved_qpresults = d['saved_qpresults']
    self.total_zoom_levels = d['total_zoom_levels']
    self.threshold = d['threshold']
    self.original_query = d['original_query']
    self.total_tiles = d['total_tiles']
    self.tile_count = d['tile_count']
