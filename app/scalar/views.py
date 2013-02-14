from flask import current_app,Flask,Blueprint, session, request, render_template, g, redirect, send_file
import simplejson as json
import traceback
import websocket
import logging
from app.database import db_session
from app.models import User,DataSet
from app.scalar.models import UserTrace,UserTileSelection
from sqlalchemy.orm.exc import NoResultFound
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

@mod.route('/warmup/', methods=["POST", "GET"])
def warmup():
    return render_template('scalar/warmup.html')

@mod.route('/canvas/', methods=["POST", "GET"])
def get_data2_canvas():
    return render_template('scalar/canvas.html')

@mod.route('/fetch-first-tile',methods=["POST", "GET"])
def fetch_first_tile():
    current_app.logger.info("got fetch first tile request")
    query = request.args.get('query',"",type=str)
    if len(query) == 0: #look for data set
        data_set = request.args.get('data_set',"",type=str)
        if len(data_set) > 0:
            try:
                ds = db_session.query(DataSet).filter_by(name=data_set).one()
                query = ds.query
            except:
                current_app.logger.warning("could not locate data set %r" % \
                                           data_set)
    session['query'] = query
    data_threshold = request.args.get('data_threshold',0,type=int)
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
        user_trace = UserTrace(tile_id=str(tile_id),zoom_level=0,query=session['query'],user_id=g.user.id,dataset_id=None)
        # save current tile info for tracking tile selection
        uts = UserTileSelection(tile_id=str(tile_id),zoom_level=0,query=session['query'],user_id=g.user.id,dataset_id=None)
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
                                                    query=session['query'],
                                                    user_id=g.user.id,
                                                    dataset_id=None)

        # save current tile info for tracking tile selection
        uts = UserTileSelection(tile_id=str(tile_id),
                                zoom_level=level,
                                query=session['query'],
                                user_id=g.user.id,
                                dataset_id=None)

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

@mod.route('/tile-selected/',methods=["POST","GET"])
def tile_selected():
    try:
        db_session.add(session['user_tile_selection']) 
        db_session.commit()
    except:
        pass #didn't work but oh well
        current_app.logger.warning("unable to remove %r from database" \
                                       % (uts))

    return json.dumps(str(0))

@mod.route('/tile-unselected/',methods=["POST","GET"])
def tile_unselected():
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

@mod.before_request
def before_request(exception=None):
    g.user = None
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    try:
        g.user = db_session.query(User).filter_by(flask_session_id=session['user_id']).one()
    except NoResultFound: # user not found
        g.user = User(session['user_id'])
        db_session.add(g.user)
        db_session.commit()

@mod.teardown_request
def teardown_request(exception=None):
    db_session.remove()


