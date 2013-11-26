import scidb_server_interface as sdbi
import scidb_server_interface_numpy as sdbinp
import math

DEBUG_PRINT = False

default_diff = 2

def getTileByIDN(tile_id,l,user_metadata,usenumpy=False):
  if DEBUG_PRINT: print "calling getTileByIDN"
  tile_info = {'type':'n','tile_id':tile_id}
  return getTileHelper(tile_info,l,user_metadata,usenumpy)


# does not require shared metadata object
def getTileHelper(tile_info,l,user_metadata,usenumpy=False):
  db = sdbi.scidbOpenConn()
  tile_id = tile_info['tile_id']
  orig_query = user_metadata['original_query']
  saved_qpresults = user_metadata['saved_qpresults']
  if DEBUG_PRINT: print "saved_qpresults:",saved_qpresults
  n = saved_qpresults['numdims']
  bases= [0]*n
  widths = [0]*n
  if n > 0: # adjust bases for array if possible
    for i in range(n):
      bases[i] = int(saved_qpresults['dimbases'][saved_qpresults['dims'][i]])
      widths[i] = int(saved_qpresults['dimwidths'][saved_qpresults['dims'][i]])
  k = user_metadata['threshold']
  levels = user_metadata['total_zoom_levels']
  if levels == 0: # need to compute # of levels
    root_k = math.ceil(math.pow(k,1.0/n))
    #k = root_k ** 2
    k = math.pow(root_k,n)
    if DEBUG_PRINT: print "root_k:",root_k,"d:",default_diff
    for i in range(n):
      w_i = widths[i]
      if DEBUG_PRINT: print "w_i:",w_i
      l_i = 1
      if w_i > root_k:
        t_i = math.ceil(w_i/root_k) # number of base level tiles
        if DEBUG_PRINT: print "t_i:",t_i
        if DEBUG_PRINT: print "log t_i:",math.log(t_i),"log d:",math.log(default_diff)
        l_i = math.ceil(math.log(t_i)/math.log(default_diff))+1
        if DEBUG_PRINT: print "l_i:",l_i,"levels:",levels
      if l_i > levels:
        levels = l_i
  setup_aggr_options = {'afl':False,'saved_qpresults':saved_qpresults}
  aggr_options = setup_reduce_type('AGGR',setup_aggr_options)
  aggr_options['db'] = db
  if DEBUG_PRINT: print "inputs:",",".join([orig_query,str(n),str(tile_info['tile_id']),str(l),str(levels-1),str(default_diff),str(bases),str(widths),str(k),str(aggr_options)])
  queryresultobj = sdbi.getTileByIDN(orig_query,n,tile_info['tile_id'],l,levels-1,default_diff,bases,widths,k,aggr_options)
  if 'error' in queryresultobj:
    # this is bad, return the error
    sdbi.scidbCloseConn(db)
    return queryresultobj
  #total_tiles = queryresultobj[1]['total_tiles']
  #total_tiles_root = queryresultobj[1]['total_tiles_root']
  #if DEBUG_PRINT: print "total_tiles_root:",total_tiles_root
  sdbioptions={'dimnames':saved_qpresults['dims']}
  if usenumpy:
    queryresultarr = sdbinp.getAllAttrArrFromQueryForNP(queryresultobj[0])
    data = sdbinp.arrs_to_json(queryresultarr['data'])
    queryresultarr['data'] = data
    stats = sdbinp.stats_to_json(queryresultarr['stats'])
    queryresultarr['stats'] = stats
  else:
    #queryresultarr = sdbi.getAllAttrArrFromQueryForJSON(queryresultobj[0],sdbioptions)
    queryresultarr = sdbi.buildCompressedJsonArr(queryresultobj[0])
  # return original saved_qpresults so front-end can track it for us
  queryresultarr['orig_sqpr'] = saved_qpresults
  saved_qpresults = queryresultobj[1] # don't need local saved_qpresults anymore, so reuse
  # get the new dim info
  queryresultarr['dimnames'] = saved_qpresults['dims']
  queryresultarr['dimbases'] = saved_qpresults['dimbases']
  queryresultarr['dimwidths'] = saved_qpresults['dimwidths']
  queryresultarr['numdims'] = saved_qpresults['numdims']
  queryresultarr['indexes'] = saved_qpresults['indexes']
  queryresultarr['max_zoom'] = levels
  queryresultarr['threshold'] = k
  queryresultarr['zoom_diff'] = default_diff
  queryresultarr['total_tiles'] = saved_qpresults['total_tiles']
  queryresultarr['future_tiles'] = saved_qpresults['future_tiles']
  queryresultarr['future_tiles_exact'] = saved_qpresults['future_tiles_exact']
  if DEBUG_PRINT: print "indexes:",saved_qpresults['indexes']
  sdbi.scidbCloseConn(db)
  return queryresultarr


#returns necessary options for reduce type
#options: {'afl':True/False, 'predicate':"boolean predicate",'probability':double,'chunkdims':[]}
#required options: afl, predicate (if filter specified)
#TODO: make these reduce types match the scidb interface api reduce types
def setup_reduce_type(reduce_type,options):
  saved_qpresults = options['saved_qpresults']
  returnoptions = {'qpresults':saved_qpresults,'afl':options['afl']}
  returnoptions['reduce_type'] = sdbi.RESTYPE[reduce_type]
  #if reduce_type == 'agg':
  if 'chunkdims' in options:
    returnoptions['chunkdims'] = chunkdims
    #returnoptions['reduce_type'] = sdbi.RESTYPE['AGGR']
  #elif reduce_type == 'sample':
  if 'probability' in options:
    returnoptions['probability'] = options['probability']
    #returnoptions['reduce_type'] = sdbi.RESTYPE['SAMPLE']
  #elif reduce_type == 'filter':
  if 'predicate' in options:
    returnoptions['predicate'] = options['predicate']
    #returnoptions['reduce_type'] = sdbi.RESTYPE['FILTER']
  #else: #unrecognized type
  #  raise Exception("Unrecognized reduce type passed to the server.")
  return returnoptions

