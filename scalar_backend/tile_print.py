import sys
sys.path.append('/opt/scidb/12.3/lib')
sys.path.append('/opt/scidb/12.7/lib')
sys.path.append('/opt/scidb/12.10/lib')
import scidbapi as scidb
import string, re
import simplejson as json
import math
from datetime import datetime

DEBUG_PRINT = False
USE_NEW_SYNTAX = True
LOGICAL_PHYSICAL = "explain_physical"
RESTYPE = {'AGGR': 'aggregate', 'SAMPLE': 'sample','OBJSAMPLE': 'samplebyobj','FILTER':'filter','OBJAGGR': 'aggregatebyobj', 'BSAMPLE': 'biased_sample'}
AGGR_CHUNK_DEFAULT = 1
TILE_AGGR_CHUNK_DEFAULT = 1 # don't aggregate if we're at the lowest zoom level
PROB_DEFAULT = .5
SIZE_THRESHOLD = 50
D3_DATA_THRESHOLD = 10000

default_diff = 2

def scidbOpenConn():
    #global db
    db = scidb.connect("localhost",1239)
    #db = scidb.connect("vise4.csail.mit.edu",1239)
    #db = scidb.connect("istc11.csail.mit.edu",1239)
    return db

def scidbCloseConn(db):
    #global db
    if db != 0:
        db.disconnect()
        db = 0

def getTileByIDN(tile_id,l,user_metadata):
   if DEBUG_PRINT: print "calling getTileByIDN"
   tile_info = {'type':'n','tile_id':tile_id}
   return getTileHelper(tile_info,l,user_metadata)


# does not require shared metadata object
def getTileHelper(tile_info,l,user_metadata):
    db = scidbOpenConn()
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
    aggr_options = {'afl':False,'saved_qpresults':saved_qpresults,'db':db}
    if DEBUG_PRINT: print "inputs:",",".join([orig_query,str(n),str(tile_info['tile_id']),str(l),str(levels-1),str(default_diff),str(bases),str(widths),str(k),str(aggr_options)])
    result = getTileMath(orig_query,n,tile_info['tile_id'],l,levels-1,default_diff,bases,widths,k,aggr_options)
    scidbCloseConn(db)
    return result

#orig_query = original user query
#cx,cy= center
#l = current zoom level
#d = resolution difference between zoom levels along 1 axis
#threshold = tile size, used for resolution reduction and tile computation
#mxn = original array dimensions
#TODO: just pass qpresults!!!!!
def getTileMath(orig_query,n,tile_id,l,max_l,d,bases,widths,threshold,aggregate_options): # zero-based indexing
    if DEBUG_PRINT: print "tile id request: (",tile_id,")"
    root_threshold = math.ceil(math.pow(threshold,1.0/n)) # assume the tiles are squares
    #orig_query = re.sub(r"[^\\](\'|\")","\\\1",orig_query) #escape single and double quotes
    #orig_query = re.sub("(\'|\")","\\\1",orig_query) #escape single and double quotes
    toprint = "["
    for v in tile_id:
        toprint += str(v) + ","
    toprint = toprint[:len(toprint)-1]
    toprint += "],"+str(l)+","
    total_tiles = [1.0]*n
    total_tiles_l = [1.0]*n
    lower = [0]*n
    upper= [0]*n
    future_tiles = [d]*n
    future_tiles_exact = [d]*n
    total = 1
    bottomtiles_per_currenttile = math.pow(d,max_l-l)
    bottomtiles_per_currenttile_plus1level = math.pow(d,max_l-min(l+1,max_l))
    tile_width = root_threshold*math.pow(d,max_l-l) # figure out tile dimensions
    for i in range(n):
        if DEBUG_PRINT: print "range width:",widths[i]
        total_tiles[i] = math.ceil(1.0*widths[i]/root_threshold) # number of tiles along dimension i on the lowest level
        total_tiles_l[i] = math.ceil(1.0*total_tiles[i]/bottomtiles_per_currenttile)
        total *= total_tiles_l[i]
        lower[i] = int(bases[i]+tile_width*tile_id[i])
        upper[i] = int(lower[i]+tile_width-1)
        if upper[i] > (widths[i]+bases[i]-1):
            upper[i] = bases[i]+widths[i]-1
            total_bottomtiles_here = total_tiles[i] - (total_tiles_l[i]-1)*bottomtiles_per_currenttile
            if DEBUG_PRINT: print "total_bottomtiles_here: ",total_bottomtiles_here
            future_tiles[i] = math.ceil(total_bottomtiles_here/bottomtiles_per_currenttile_plus1level)
        future_tiles_exact[i] = 1.0*(upper[i]-lower[i])/max(tile_width/2.0,root_threshold)
        if DEBUG_PRINT: print "upper:",upper[i]
    if DEBUG_PRINT: print "level: ",l,", total levels: ",max_l
    if DEBUG_PRINT: print "total bottomtiles: ",total_tiles
    if DEBUG_PRINT: print "root_threshold: ",root_threshold
    if DEBUG_PRINT: print "bottomtiles_per_currenttile: ",bottomtiles_per_currenttile
    if DEBUG_PRINT: print "bottomtiles_per_currenttile_plus1level: ",bottomtiles_per_currenttile_plus1level
    if DEBUG_PRINT: print "current_tiles: ",total_tiles_l
    if DEBUG_PRINT: print "future_tiles: ",future_tiles
    newquery = "select * from subarray(("+orig_query+")"
    for i in range(n):
        newquery += "," + str(lower[i])
	toprint += str(lower[i]) + ","
    for i in range(n):
        newquery += "," + str(upper[i])
	toprint += str(upper[i]) + ","
    newquery += ")"
    #newquery = "select * from subarray(("+orig_query+"),"+str(lower_x)+","+str(lower_y)+","+str(upper_x)+","+str(upper_y)+")"
    newquery = str(newquery)
    if DEBUG_PRINT: print "newquery: ",newquery
    sdbioptions = {'db':aggregate_options['db'],'afl':False}
    qpresults = verifyQuery(newquery,sdbioptions)
    qpsize = int(qpresults['size'])
    quotient = 1.0*qpsize/threshold # approximate number of base tiles

    dimension = qpresults['numdims']
    defaultchunkval = math.pow(quotient,1.0/dimension)
    if quotient < 1.0:
        defaultchunkval = TILE_AGGR_CHUNK_DEFAULT
    defaultchunkval = int(math.ceil(defaultchunkval)) # round up
    toprint += str(defaultchunkval)
    return toprint

#options: {'afl':True/False}
#required options: afl
#function to verify query query result size
def verifyQuery(query,options):
    queryplan = query_optimizer(query,options)
    if 'error' in queryplan:
        return queryplan
    return check_query_plan(queryplan) #returns a dictionary

#function to do the resolution reduction when running queries
# get the queryplan for the given query and return the line with info about the result matrix
def query_optimizer(query,options):
    db = options['db']
    afl = options['afl']
    query = re.sub(r"([^\\])(\'|\")",r"\1\\\2",query)
    #query = re.sub(r"[^\\](\'|\")","\\\1",query) #escape single and double quotes
    #query = re.sub("(\\')","\\\\\\1",query)
    # eventually want to be able to infer this
    queryplan_query = ""
    optimizer_answer = []
    if(afl):
        queryplan_query = LOGICAL_PHYSICAL+"('"+query+"','afl')"
    else:
        queryplan_query = LOGICAL_PHYSICAL+"('"+query+"','aql')"
    #if DEBUG_PRINT: print  "queryplan query: "
    #if DEBUG_PRINT: print  queryplan_query
    optimizer_answer = None
    try:
        optimizer_answer = db.executeQuery(queryplan_query,'afl')
    except Exception as e:
        return {'error':{'type':str(type(e)),'args':e.args}}
    #if DEBUG_PRINT: print  optimizer_answer
    # flatten the list into one big string, and then split on '\n'
    optimizer_answer_array = getOneAttrArrFromQuery(optimizer_answer,"")[0].split('\n') #should return array with one item (the query plan)
    # find the line with the first instance of 'schema' in the front
    for i, s in enumerate(optimizer_answer_array):
        if(re.search("^\s*schema", s)):
            return s

# get the matrix size (across all dimensions) and the number of dimensions of the result matrix
def check_query_plan(queryplan):
    # get the text in between the square brackets
    queryplan = str(queryplan)
    dim_string = queryplan[queryplan.find("[")+1:queryplan.find("]")]
    dim_array = dim_string.split(',')
    #if DEBUG_PRINT: print  dim_array
    dims = 0
    size = 1
    names = []
    truenames = []
    bases= {}
    uppers = {}
    widths = {}
    indexes = {}
    chunkwidths = {}
    chunkoverlaps = {}
    for i, s in enumerate(dim_array):
        #if (i % 3) == 0:
        if "=" in s:
            # split on equals, get the range, split on ':'
            #if DEBUG_PRINT: print  "s:",s
            rangeval = s.split('=')[1]
            name = s.split('=')[0]
            if name.find("(") >= 0:
                name = name[:name.find("(")]
                truenames.append(name)
                name = "dims."+name
                rangewidth = int(rangeval)
                bases[name] = 1 #1 by default
                uppers[name] = rangewidth
            else:
                truenames.append(name)
                name = "dims."+name
                rangevals = rangeval.split(':')
                rangewidth = int(rangevals[1]) - int(rangevals[0]) + 1
                bases[name]=int(rangevals[0])
                uppers[name] = int(rangevals[1])
            names.append(name)
            indexes[name] = dims
            chunkwidths[name] = int(dim_array[i+1])
            chunkoverlaps[name] = int(dim_array[i+2])
            size *= rangewidth
            dims += 1
            widths[name] =rangewidth;
    return {'size': size, 'numdims': dims,'truedims':truenames, 'dims': names, 'indexes':indexes, 'attrs':get_attrs(queryplan)
        ,'dimbases':bases,'dimwidths':widths,'chunkwidths':chunkwidths,'chunkoverlaps':chunkoverlaps,'dimuppers':uppers}

#get all attributes of the result matrix
def get_attrs(queryplan):
    # get the text in between the angle brackets
    attr_string = queryplan[queryplan.find('<')+1:queryplan.find('>')]
    attr_array = attr_string.split(',')
    names = []
    types = []
    for i,s in enumerate(attr_array):
        name_type = (s.split(' ')[0]).split(':') # does this work?
        names.append(name_type[0])
        types.append(name_type[1])
    return {'names':names,'types':types}

def build_cast(saved_qpresults):
    cast = "<"
    front = True
    attrs = saved_qpresults['attrs']
    for i,name in enumerate(attrs['names']):
        if not front:
            cast += ","
        else:
            front = False
        cast += name+":"+attrs['types'][i]+ " NULL"
    cast += "> ["
    front = True
    for i,name in enumerate(saved_qpresults['dims']):
        if not front:
            cast += ","
        else:
            front = False
        cast += saved_qpresults['truedims'][i]+"="+str(saved_qpresults['dimbases'][name])+":"+str(saved_qpresults['dimbases'][name]+saved_qpresults['dimwidths'][name]-1)+","+str(saved_qpresults['chunkwidths'][name])+","+str(saved_qpresults['chunkoverlaps'][name])
    cast += "]"
    return cast

#options: {'numdims':int, 'chunkdims': [ints], 'attrs':[strings],'flex':'more'/'less'/'none','afl':True/False, 'qpsize':int}
#required options: numdims, afl, attrs, attrtypes, qpsize
#NOTE: ASSUMES AVG IS THE AGG FUNCTION!
#TODO: Fix the avg func assumption
def daggregate(query,options):
    saved_qpresults = options['saved_qpresults']
    cast = build_cast(saved_qpresults)
    if DEBUG_PRINT: print "cast:",cast
    final_query = query
    if 'threshold' in options:
        threshold = options['threshold']
    else:
        threshold= D3_DATA_THRESHOLD
    dimension = options['numdims']
    attrs = options['attrs']

    # need to escape apostrophes or the new query will break
    #final_query = re.sub("(')","\\\1",final_query)

    #make the new query an aql query so we can rename the aggregates easily
    attraggs = ""
    #if DEBUG_PRINT: print  "options attrtypes: ",options['attrtypes']
    for i in range(len(attrs)):
        #if DEBUG_PRINT: print  "attr type: ",options['attrtypes'][i]
        if (options['attrtypes'][i] == "int32") or (options['attrtypes'][i] == "int64") or (options['attrtypes'][i] == "double"): # make sure types can be aggregated
            if attraggs != "":
                attraggs += ", "
            attraggs+= "avg("+str(attrs[i])+") as avg_"+attrs[i]
            attraggs+= ", min("+str(attrs[i])+") as min_"+attrs[i] # need for the color scale
            attraggs+= ", max("+str(attrs[i])+") as max_"+attrs[i] # need for the color scale
        else:
            if attraggs != "":
                attraggs += ", "
            attraggs+= "max("+str(attrs[i])+") as max_"+attrs[i]

    if attraggs != "":
        attraggs += ", "
    attraggs+= " count(*) as count"

    equal_chunks_per_dim = max(1.0,math.floor(math.pow(threshold,1.0/dimension)))

    if USE_NEW_SYNTAX:
        chunks = ""
        if ('chunkdims' in options) and (len(options['chunkdims']) > 0): #chunkdims specified
            chunkdims = options['chunkdims']
            chunks += saved_qpresults['truedims'][0]+","+str(chunkdims[0])
            for i in range(1,len(chunkdims)):
                chunks += ", "+saved_qpresults['truedims'][i]+","+str(chunkdims[i])
        elif dimension > 0: # otherwise do default chunks
            quotient = 1.0*options['qpsize']/threshold # approximate number of base tiles
            defaultchunkval = math.pow(quotient,1.0/dimension)
            if quotient < 1.0:
                if ('tile' in options) and options['tile']:
                    defaultchunkval = TILE_AGGR_CHUNK_DEFAULT
                else:
                    defaultchunkval = AGGR_CHUNK_DEFAULT
            defaultchunkval = int(math.ceil(defaultchunkval)) # round up
            #defaultchunkval = int(max(1,math.ceil(int(saved_qpresults['dimwidths'][saved_qpresults['dims'][0]])/equal_chunks_per_dim)))
            if DEBUG_PRINT: print "chunk size:",defaultchunkval,"quotient:",quotient,",size:",options['qpsize'],",threshold:",threshold
            chunks += saved_qpresults['truedims'][0]+" "+str(defaultchunkval)
            #chunks += options['dimnames'][0]+" "+ str(defaultchunkval)
            for i in range(1,dimension) :
                chunks += ", "+saved_qpresults['truedims'][i]+" "+str(defaultchunkval)
        final_query = "select "+attraggs+" from cast(("+ final_query +"),"+cast+") regrid as (partition by "+chunks+")"
    else:
        chunks = ""
        if ('chunkdims' in options) and (len(options['chunkdims']) > 0): #chunkdims specified
            chunkdims = options['chunkdims']
            chunks += str(chunkdims[0])
            for i in range(1,len(chunkdims)):
                chunks += ", "+str(chunkdims[i])
        elif dimension > 0: # otherwise do default chunks
            quotient = 1.0*options['qpsize']/threshold # approximate number of base tiles
            defaultchunkval = math.pow(quotient,1.0/dimension)
            #defaultchunkval = int(max(1,math.ceil(int(saved_qpresults['dimwidths'][saved_qpresults['dims'][0]])/equal_chunks_per_dim)))
            if DEBUG_PRINT: print "chunk size:",defaultchunkval,"quotient:",quotient,",size:",options['qpsize'],",threshold:",threshold
            if quotient < 1.0:
                if ('tile' in options) and options['tile']:
                    defaultchunkval = TILE_AGGR_CHUNK_DEFAULT
                else:
                    defaultchunkval = AGGR_CHUNK_DEFAULT
            defaultchunkval = int(math.ceil(defaultchunkval)) # round up
            chunks += str(defaultchunkval)
            #chunks += options['dimnames'][0]+" "+ str(defaultchunkval)
            for i in range(1,dimension) :
                chunks += ", "+str(defaultchunkval)
                #chunks += ", "+ options['dimnames'][i]+" "+ str(defaultchunkval)
        final_query = "select "+attraggs+" from ("+ final_query +") regrid "+chunks
    if DEBUG_PRINT: print  "final query:",final_query
    return final_query

def reduce_resolution(query,options):
    db = options['db']
    reduce_type = options['reduce_type']
    qpresults = options['qpresults']
    if DEBUG_PRINT: print "qpresults:",qpresults
    #add common reduce function options
    reduce_options = {'afl':options['afl'],'qpsize':qpresults['size']}
    if 'tile' in options:
        reduce_options['tile'] = options['tile']
    if 'resolution' in options:
        reduce_options['threshold'] = options['resolution']
    if reduce_type == RESTYPE['AGGR']:
        reduce_options['numdims'] = qpresults['numdims']
        reduce_options['attrs'] = qpresults['attrs']['names']
        reduce_options['attrtypes'] = qpresults['attrs']['types']
        reduce_options['dimnames'] = qpresults['dims']
        reduce_options['saved_qpresults'] = qpresults
        newquery = daggregate(query,reduce_options)
    else:
        raise Exception('reduce_type not recognized by scidb interface api')
    newquery = str(newquery)

def getOneAttrArrFromQuery(query_result,attrname):
    desc = query_result.array.getArrayDesc()
    dims = desc.getDimensions() # list of DimensionDesc objects
    attrs = desc.getAttributes() # list of AttributeDesc objects

    dimlengths= []
    dimchunkintervals = []
    dimoverlaps = []
    dimindexes = []
    dimindexesbase = []

    if(dims.size() < 1):
        return [];

    for i in range(dims.size()):
        dimlengths.append(dims[i].getLength())
        dimchunkintervals.append(dims[i].getChunkInterval())
        dimoverlaps.append(dims[i].getChunkOverlap())
        dimindexes.append(0)
        dimindexesbase.append(0)

    # get arr ready
    arr = createArray(dimlengths)
    #if DEBUG_PRINT: print  "arr is initialized: ",str(arr)
    attrid = 0
    for i in range(attrs.size()): # find the right attrid
        if(attrs[i].getName() == attrname):
            attrid = i
            #if DEBUG_PRINT: print  "found attribute",attrname, ",id: %d" % attrid 
            break

    # get the iterator for this attrid
    it = query_result.array.getConstIterator(attrid)

    start = True
    while not it.end():
        #if DEBUG_PRINT: print  "iterating over items..."
        currentchunk = it.getChunk()
        # TODO: will have to fix this at some point, can't just ignore empty cells or overlaps
        chunkiter = currentchunk.getConstIterator((scidb.swig.ConstChunkIterator.IGNORE_EMPTY_CELLS |
                                               scidb.swig.ConstChunkIterator.IGNORE_OVERLAPS))

        if(not start): # don't update for the first chunk
            #update base indexes
            dimindexesbase = updateBaseIndex(dimindexesbase,dimlengths,dimchunkintervals)
            #if DEBUG_PRINT: printIndexes(dimindexesbase)
            verifyIndexes(dimindexesbase,dimlengths)
                
            #reset the indexes to new base indexes
            for i in range (dims.size()):
                dimindexes[i] = dimindexesbase[i]
        else:
            start = False

        while not chunkiter.end():
            #if DEBUG_PRINT: printIndexes(dimindexes)
            verifyIndexes(dimindexes,dimlengths)
            dataitem = chunkiter.getItem()
            # look up the value according to its attribute's typestring
            item = scidb.getTypedValue(dataitem, attrs[attrid].getType()) # TBD: eliminate 2nd arg, make method on dataitem
            #if DEBUG_PRINT: print  "Data: %s" % item

            #insert the item
            arr = insertItem(arr,item,dimindexes)
            #update the indexes
            dimindexes = updateIndexes(dimindexes,dimchunkintervals,dimindexesbase,dimlengths)
            lastpos = chunkiter.getPosition()
            #if DEBUG_PRINT: print  lastpos[0],",",lastpos[1], ",",lastpos[2]
            chunkiter.increment_to_next()
        #if DEBUG_PRINT: print  "current state of arr: ", str(arr)
        it.increment_to_next();
    return arr

#helper function for createArray to do the recursive building of the array to be initialized
def createArrayHelper(dimlengths,currdim,numdims):
    arr = [0]*dimlengths[currdim]
    if(currdim < (numdims-1)):
        for i in range(dimlengths[currdim]):
            arr[i] = createArrayHelper(dimlengths,currdim+1,numdims)
    return arr

#exterior function for initializing an array of the appropriate size
def createArray(dimlengths):
    return createArrayHelper(dimlengths,0,len(dimlengths))

# function that verifies that we are not trying to use indexes
# that are out of bounds
def verifyIndexes(dimlist,dimboundaries):
    for i in range(len(dimlist)):
        assert dimlist[i] < dimboundaries[i], "indexes out of range." #" index:",str(dimlist[i]),", boundary:",str(dimboundaries[i])

#exterior function to insert the given item in the the array using the given indexes
def insertItem(arr,item,dimindexes):
    #if DEBUG_PRINT: print  "inserting item %d" % item
    return insertItemHelper(arr,item,dimindexes,0,len(dimindexes))

#helper function to recursively find the appropriate list to insert the item into in the array
def insertItemHelper(arr,item,dimindexes,currdim,numdims):
    if(currdim == (numdims-1)):
        arr[dimindexes[currdim]] = item
    else:
        arr[dimindexes[currdim]] = insertItemHelper(arr[dimindexes[currdim]],item,dimindexes,currdim + 1, numdims)
    return arr


# function to update to the next appropriate index location after inserting 1 item
#not to be confused with the similar updateBaseIndex, which updates by chunk lengths
def updateIndexes(dimindexes,dimchunkintervals, dimindexesbase,dimlengths):
    i = len(dimindexes) - 1
    while i > 0:
        dimindexes[i] += 1
        if((dimindexes[i] - dimindexesbase[i]) >= dimchunkintervals[i]):
            dimindexes[i] = dimindexesbase[i]
            # next dimension up will be incremented in next iteration of the while loop
            i -= 1
        elif(dimindexes[i] >= dimlengths[i]): # edge case for odd chunks
            dimindexes[i]= dimindexesbase[i]
            i-= 1
        else:
            break
    if(i == 0):
        dimindexes[i] += 1
    return dimindexes

#function to recompute the base indexes when we've completed
#traversal of the current chunk
def updateBaseIndex(dimindexesbase,dimlengths,dimchunkintervals):
    i = len(dimindexesbase) - 1
    while i > 0:
        dimindexesbase[i] += dimchunkintervals[i]
        if(dimindexesbase[i] >= dimlengths[i]):
            dimindexesbase[i] = 0
            i -= 1
        else:
            break    
    if(i == 0):
        dimindexesbase[i] += dimchunkintervals[i]
    return dimindexesbase

