from flask import current_app,Flask,Blueprint, session, request, render_template, g, redirect, send_file,url_for
import simplejson as json
import traceback
import websocket
import logging
from app.database import db_session
from app.models import User,DataSet
from app.scalar.models import UserTrace,UserTileSelection,UserTileUpdate,UserFilterUpdate
from sqlalchemy.orm.exc import NoResultFound
from app.forms.decorators import consent_required
import uuid

mod = Blueprint('scalar',__name__,url_prefix='/scalar')

def connect_to_backend():
    if 'backend_conn' not in session:
        try:
            ws = websocket.create_connection(current_app.config['CONN_STRING'])
            session['backend_conn'] = ws
        except Exception as e:
            current_app.logger.error('error occurred connecting to backend:\n'+str(type(e)))
            current_app.logger.error(str(e))
    if ('backend_conn' not in session) or (session['backend_conn'] is None):
        current_app.logger.warning('could not open connection to \''+current_app.config['CONN_STRING']+'\'')

def close_connection_to_backend():
    """Make sure we close the connection"""
    session['backend_conn'].close()
    session['backend_conn'] = None
    session.pop('backend_conn')

def send_request(request):
    connect_to_backend()
    ws = session['backend_conn']
    current_app.logger.info("sending request \""+json.dumps(request)+"\" to '"+current_app.config['CONN_STRING']+"'")
    ws.send(json.dumps(request))
    current_app.logger.info("retrieving data from '"+current_app.config['CONN_STRING']+"'")
    response = ws.recv()
    current_app.logger.info("received data from '"+current_app.config['CONN_STRING']+"'")
    close_connection_to_backend()
    return json.loads(response)

@mod.route('/tutorial/', methods=["POST", "GET"])
@consent_required
def tutorial():
    return render_template('scalar/tutorial.html')

@mod.route('/warmup/', methods=["POST", "GET"])
@consent_required
def warmup():
    return render_template('scalar/warmup.html')

@mod.route('/task1/', methods=["POST", "GET"])
@consent_required
def task1():
    return render_template('scalar/task1.html')

@mod.route('/task2/', methods=["POST", "GET"])
@consent_required
def task2():
    return render_template('scalar/task2.html')

@mod.route('/canvas/', methods=["POST", "GET"])
@consent_required
def get_data2_canvas():
    return render_template('scalar/canvas.html')

@mod.route('/fetch-first-tile',methods=["POST", "GET"])
@consent_required
def fetch_first_tile():
    current_app.logger.info("got fetch first tile request")
    query = request.args.get('query',"",type=str)
    taskname = request.args.get('task',"",type=str)
    ds = None
    if len(query) == 0: #look for data set
        data_set = request.args.get('data_set',"",type=str)
        if len(data_set) > 0:
            try:
                ds = db_session.query(DataSet).filter_by(name=data_set).one()
                query = ds.query
                session['data_set'] = ds
                if len(taskname) > 0 and taskname not in session: # record what data set was used for this task
                    session[taskname]=ds.id
            except:
                current_app.logger.warning("could not locate data set %r" % \
                                           data_set)
    session['query'] = query
    data_threshold = request.args.get('data_threshold',0,type=int)
    session['threshold'] = data_threshold
    options = {'user_id':session['user_id']}
    session['usenumpy'] = request.args.get('usenumpy',False,type=bool)
    if data_threshold > 0:
        options['data_threshold'] = data_threshold
    if session['usenumpy']:
        options['usenumpy'] = False
    server_request = {'query':query,'options':options,'function':'fetch_first_tile'}
    try:
        queryresultarr = send_request(server_request)
    except websocket.WebSocketConnectionClosedException as e: # uh oh, backend did something bad
        current_app.logger.info("backend unexpectedly closed while trying to retrieve data:")
        queryresultarr = {'error':{'type':str(type(e)),'args':e.args}}
    except Exception as e:
        current_app.logger.info("error occurred while trying to retrieve data:")
        queryresultarr = {'error':{'type':str(type(e)),'args':e.args}}
    if 'error' not in queryresultarr: # error didn't happen
        current_app.logger.info("result length: "+str(len(queryresultarr['data'])))
        tile_id = [0,0]
        if 'saved_qpresults' in queryresultarr:
            tile_id = [0] * int(queryresultarr['saved_qpresults']['numdims'])
        user_trace = UserTrace(tile_id=str(tile_id),zoom_level=0,threshold=data_threshold,query=session['query'],user_id=g.user.id,dataset_id=None)
        # save current tile info for tracking tile selection
        uts = UserTileSelection(tile_id=str(tile_id),zoom_level=0,threshold=data_threshold,query=session['query'],user_id=g.user.id,dataset_id=None,image=None)
        if ds is not None: #there is an associated data set
            user_trace.dataset_id = ds.id
            uts.dataset_id = ds.id
        else:
            current_app.logger.warning("data set not passed")
        db_session.add(user_trace)
        db_session.commit()
        #log the tile request

        session['user_tile_selection'] = uts
        try:
            db_session.query(UserTileSelection).filter_by(tile_id=uts.tile_id,
                                                      user_id=uts.user_id,
                                                      zoom_level=uts.zoom_level,
                                                      query=uts.query).one()
            queryresultarr['selected'] = True
        except NoResultFound:
            queryresultarr['selected'] = False
        except: # uh oh, something bad happened here
            current_app.logger.warning("error occured when querying \
                                   for user's selections")
    return json.dumps(queryresultarr)

@mod.route('/fetch-tile',methods=["POST", "GET"])
@consent_required
def fetch_tile():
    current_app.logger.info("got fetch tile request")
    tile_xid = request.args.get('tile_xid',"",type=int)
    tile_yid = request.args.get('tile_yid',"",type=int)
    tile_id = request.args.getlist('temp_id[]')
    for i in range(len(tile_id)):
        tile_id[i] = int(tile_id[i])
    x_label = request.args.get('x_label',"",type=str)
    y_label = request.args.get('y_label',"",type=str)
    level = request.args.get('level',"",type=int)
    options = {'user_id':session['user_id']}
    if session['usenumpy']:
        options['usenumpy'] = False
    server_request = {'options':options,'tile_xid':tile_xid,
                      'tile_yid':tile_yid,'tile_id':tile_id,
                      'level':level,'y_label':y_label,
                      'x_label':x_label,
                      'function':'fetch_tile'}
    try:
        queryresultarr = send_request(server_request)
    except WebSocketConnectionClosedException as e: # uh oh, backend did something bad
        current_app.logger.info("backend unexpectedly closed while \
                                trying to retrieve data:")
        queryresultarr = {'error':{'type':str(type(e)),'args':e.args}}
    except Exception as e:
        current_app.logger.info("error occurred while trying to retrieve data:")
        queryresultarr = {'error':{'type':str(type(e)),'args':e.args}}
    if 'saved_qpresults' in queryresultarr:
        session['saved_qpresults'] = queryresultarr['saved_qpresults']
        user_trace = UserTrace(tile_id=str(tile_id),zoom_level=level,
                                                    threshold=session['threshold'],
                                                    query=session['query'],
                                                    user_id=g.user.id,
                                                    dataset_id=None)

        # save current tile info for tracking tile selection
        uts = UserTileSelection(tile_id=str(tile_id),
                                zoom_level=level,
                                threshold=session['threshold'],
                                query=session['query'],
                                user_id=g.user.id,
                                dataset_id=None,
                                image=None)

        if g.ds is not None:
            user_trace.dataset_id = g.ds.id
            uts.dataset_id = g.ds.id
        else:
            current_app.logger.warning("g.ds is None!")

        db_session.add(user_trace)
        db_session.commit()
        session['user_tile_selection'] = uts
        try:
            db_session.query(UserTileSelection).filter_by(tile_id=uts.tile_id,
                                                      user_id=uts.user_id,
                                                      zoom_level=uts.zoom_level,
                                                      query=uts.query).one()
            queryresultarr['selected'] = True
        except NoResultFound:
            queryresultarr['selected'] = False
        except: # uh oh, something bad happened here
            current_app.logger.warning("error occured when querying \
                                       for user's tile selection")

    current_app.logger.info("result length: "+str(len(queryresultarr['data'])))
    #current_app.logger.info("tile id:"+str(tile_id))
    return json.dumps(queryresultarr)

def get_menu_args(method,args):
    result = {}
    if method == 'GET':
        result['img'] = args.get('img',"",type=str)
        result['x_label'] = args.get('x_label',"",type=str)
        result['y_label'] = args.get('y_label',"",type=str)
        result['z_label'] = args.get('z_label',"",type=str)
        result['x_inv'] = args.get('x_inv',False,type=bool)
        result['y_inv']= args.get('y_inv',False,type=bool)
        result['z_inv'] = args.get('z_inv',False,type=bool)
        result['color'] = args.get('color',"",type=str)
        result['width'] = args.get('width',-1,type=int)
        result['height'] = args.get('height',-1,type=int)
    elif method == 'POST':
        result = {
        'img': "",
        'x_label': "",
        'y_label': "",
        'z_label': "",
        'x_inv': False,
        'y_inv': False,
        'z_inv': False,
        'color': "",
        'width': -1,
        'height': -1}
        form = dict(request.form)
        for name,value in form.items():
            #if name != 'img':
            #    current_app.logger.warning("name: %r, value: %r" % (name,value[0]))
            if name in result:
                if type(result[name]) is bool:
                    try:
                        result[name] = (value[0] in ["True","true"])
                    except:
                        pass
                elif type(result[name]) is int:
                    try:
                        result[name] = int(value[0])
                    except:
                        pass
                else:
                    result[name] = value[0] # just take string version
            else:
                current_app.logger.warning("%r not in result dict" % (name))
    return result

@mod.route('/tile-updated/',methods=["POST","GET"])
@consent_required
def menu_updated():
    if 'user_tile_selection' in session:
        uts = session['user_tile_selection']
        result = get_menu_args(request.method,request.args)
        # build a new menu update entry every time
        utu = UserTileUpdate(tile_id=uts.tile_id,zoom_level=uts.zoom_level,query=session['query'],user_id=g.user.id,dataset_id=None)
        #print "result:",result
        try:
            utu.x_label = result['x_label']
            utu.y_label = result['y_label']
            utu.z_label = result['z_label']
            utu.x_inv = result['x_inv']
            utu.y_inv = result['y_inv']
            utu.z_inv = result['z_inv']
            utu.color = result['color']
            utu.width = result['width']
            utu.height = result['height']
            db_session.add(utu) 
            db_session.commit()
        except Exception as e:
            current_app.logger.warning("unable to insert into database: %r" % (e))
            #print "utu:",utu
        current_app.logger.info("got here")
    return json.dumps(str(0))


@mod.route('/filters-cleared/',methods=["POST","GET"])
@consent_required
def filters_cleared():
    ds = None
    query = None
    if 'data_set' in session:
        ds = session['data_set']
    else: # we need to know the dataset
        current_app.logger.warning("no dataset recorded for user: %r" % (session['user_id']))
        return json.dumps(str(0))

    if 'query' in session:
        query = session['query']
    try:
        ufu = UserFilterUpdate(filter_name="SCALAR_FILTER_CLEAR",
                                    lower=0.0,
                                    upper=0.0,
                                    applied=False,
                                    query=query,
                                    user_id=g.user.id,
                                    dataset_id=ds.id)
        db_session.add(ufu)
        db_session.commit()
    except Exception as e:
        current_app.logger.warning("unable to insert filter update into database: %r" % (e))
    return json.dumps(str(0))


@mod.route('/filters-applied/',methods=["POST","GET"])
@consent_required
def filters_applied():
    ds = None
    query = None
    if 'data_set' in session:
        ds = session['data_set']
    else:
        current_app.logger.warning("no dataset recorded for user: %r" % (session['user_id']))
        return json.dumps(str(0))

    if 'query' in session:
        query = session['query']

    filter_names = request.values.getlist('filter_labels[]')
    filter_lowers = request.values.getlist('filter_lowers[]')
    filter_uppers = request.values.getlist('filter_uppers[]')
    #print "filter names:",filter_names
    #print "filter lowers:",filter_lowers
    #print  request.args.get('filter_labels',"",type=str)
    for i in range(len(filter_names)):
        try:
            #print "lower:",float(filter_lowers[i])
            ufu = UserFilterUpdate(filter_name=filter_names[i],
                                    lower=float(filter_lowers[i]),
                                    upper=float(filter_uppers[i]),
                                    applied=True,
                                    query=query,
                                    user_id=g.user.id,
                                    dataset_id=ds.id)
            db_session.add(ufu)
            db_session.commit()
        except Exception as e:
            current_app.logger.warning("unable to insert filter update into database: %r" % (e))
    return json.dumps(str(0))



@mod.route('/tile-selected/',methods=["POST","GET"])
@consent_required
def tile_selected():
    result = get_menu_args(request.method,request.args)
    try:
        img = result['img']
        if len(img) > 0: # tile_id and zoom accounted for in fetch_tile function
            session['user_tile_selection'].image = img
            session['user_tile_selection'].x_label = result['x_label']
            session['user_tile_selection'].y_label = result['y_label']
            session['user_tile_selection'].z_label = result['z_label']
            session['user_tile_selection'].x_inv = result['x_inv']
            session['user_tile_selection'].y_inv = result['y_inv']
            session['user_tile_selection'].z_inv = result['z_inv']
            session['user_tile_selection'].color = result['color']
            session['user_tile_selection'].width = result['width']
            session['user_tile_selection'].height = result['height']
        db_session.add(session['user_tile_selection']) 
        db_session.commit()
    except Exception as e:
        current_app.logger.warning("unable to insert into database %r" % (e))
    current_app.logger.info("got here")
    return json.dumps(str(0))

@mod.route('/tile-unselected/',methods=["POST","GET"])
@consent_required
def tile_unselected():
    result = get_menu_args(request.method,request.args)
    if 'user_tile_selection' in session:
        uts = session['user_tile_selection']
        try:
            db_session.query(UserTileSelection).filter_by(tile_id=uts.tile_id,
                                                      user_id=uts.user_id,
                                                      zoom_level=uts.zoom_level,
                                                      query=uts.query).delete()
            db_session.commit()
        except:
            pass #didn't work but oh well
            current_app.logger.warning("unable to remove %r from database" \
                                       % (uts))
    return json.dumps(str(0))

@mod.route('/warmup/selections/',methods=["POST","GET"])
@consent_required
def warmup_selections():
    return get_tile_selections("warmup")

@mod.route('/task1/selections/',methods=["POST","GET"])
@consent_required
def task1_selections():
    return get_tile_selections("task1")

@mod.route('/task2/selections/',methods=["POST","GET"])
@consent_required
def task2_selections():
    return get_tile_selections("task2")

@mod.route('/warmup/selections/delete/',methods=["POST","GET"])
@consent_required
def delete_warmup_selections():
    delete_selections()
    return redirect(url_for('scalar.warmup_selections'))

@mod.route('/task1/selections/delete/',methods=["POST","GET"])
@consent_required
def delete_task1_selections():
    delete_selections()
    return redirect(url_for('scalar.task1_selections'))

@mod.route('/task2/selections/delete/',methods=["POST","GET"])
@consent_required
def delete_task2_selections():
    delete_selections()
    return redirect(url_for('scalar.task2_selections'))

def delete_selections():
    form = dict(request.form)
    for fieldname, value in form.items():
        try:
            db_session.query(UserTileSelection).filter_by(id=int(value[0])).delete()
        except:
            pass # didn't work, oh well
    db_session.commit()

def get_tile_selections(taskname):
    selections = []
    examples = []
    results = []
    if taskname in session: # if there is a dataset_id already associated with this task
        results = db_session.query(UserTileSelection).filter_by(user_id=g.user.id,dataset_id=session[taskname]).all()
        if taskname == 'warmup':
            for item in results:
                current_app.logger.warning("item: %r,%r,%r,%r,%r,%r" % (item.x_inv,item.y_inv,item.z_inv,item.color,item.tile_id,item.zoom_level))
                item.correct = "correct"
                if (not item.x_inv) and item.y_inv and item.z_inv and item.color == u'GnBu':
                    if item.tile_id == u'[0, 0]' and item.zoom_level == 0:
                        examples.append(1)
                    elif item.tile_id == u'[0, 1]' and item.zoom_level == 1:
                        examples.append(2)
                    elif item.tile_id == u'[3, 3]' and item.zoom_level == 3:
                        examples.append(3)
                    elif item.tile_id == u'[1, 0]' and item.zoom_level == 1:
                        examples.append(4)
                    else:
                        item.correct = "incorrect"
                else:
                   item.correct = "incorrect"
            #find found examples
                #elif g.ds is not None: # else grab the most recent data set
    #    results = db_session.query(UserTileSelection).filter_by(user_id=g.user.id,dataset_id=g.ds.id).all()
    #else: # else grab the latest query
    #    results = db_session.query(UserTileSelection).filter_by(user_id=g.user.id,query=session['query']).all()
    for result in results:
        item = dict(image=result.image,
                   tile_id=result.tile_id,
                   zoom_level=result.zoom_level,
                   timestamp=result.timestamp,
                   id=result.id)
        try:
            item['correct'] = result.correct
        except:
            pass
        selections.append(item) 

    return render_template('scalar/selections_'+taskname+'.html',selections=selections,examples=examples)
    
@mod.before_request
def before_request(exception=None):
    g.consent = None
    if 'consent' in session:
        g.consent = session['consent']
    g.ds = None
    if 'data_set' in session:
         g.ds = session['data_set']
         db_session.add(g.ds)
         db_session.commit()
    g.user = None
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    try:
        g.user = db_session.query(User).filter_by(flask_session_id=session['user_id']).one()
        g.user.set_last_update()
    except NoResultFound: # user not found
        g.user = User(session['user_id'])
        db_session.add(g.user)
        db_session.commit()

@mod.teardown_request
def teardown_request(exception=None):
    if 'user_id' in session:
        try:
            user = db_session.query(User).filter_by(flask_session_id=session['user_id']).one()
            user.set_last_update()
            db_session.add(user)
            db_session.commit()
        except:
            current_app.logger.warning("unable to update last update time for user %r" \
                                       % (session['user_id']))

    db_session.remove()


