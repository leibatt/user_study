from flask import current_app,Flask,Blueprint, session, request, render_template, g, redirect, send_file,url_for
import json
import traceback
import logging
from app.util.database.database import db_session
from app.home.models import User,DataSet
from app.scalar.models import UserTrace,UserTileSelection,UserTileUpdate,UserFilterUpdate
from app.util.queue.models import JobRecord,QueuedJob
from sqlalchemy.orm.exc import NoResultFound
from app.forms.decorators import consent_required
import uuid
import app.scalar.tasks as scalar_tasks
#from app.backend.scalrr_back import fetch_first_tile2
from app.util.queue.queue_obj import JobsQueue

mod = Blueprint('scalar',__name__,url_prefix='/scalar')

@mod.route('/test/queue/add_job', methods=["POST", "GET"])
@consent_required
def queue_add_job():
    q = JobsQueue(db_session)
    #print "numjobs:",len(q)
    taskid = q.addJobRecord(0,{})
    return json.dumps(taskid)

@mod.route('/test/queue/del_job/<job_id>', methods=["POST", "GET"])
@consent_required
def queue_del_job(job_id):
    q = JobsQueue(db_session)
    job_record = q.removeJobRecord(job_id)
    return json.dumps(job_record.id)

@mod.route('/test/queue/check_status/<job_id>', methods=["POST", "GET"])
@consent_required
def queue_check_job_status(job_id):
    q = JobsQueue(db_session)
    status = q.checkJobFinished(job_id)
    success = q.checkJobSuccess(job_id)
    fail = q.checkJobFail(job_id)
    if status:
      status = "job is finished"
    else:
      status = "job not finished"
    if success:
      status += ",job succeeded"
    if fail:
      status += ",job failed"
    return json.dumps(status)

@mod.route('/test/queue/finish/<job_id>', methods=["POST", "GET"])
@consent_required
def queue_succeed_job(job_id):
    q = JobsQueue(db_session)
    q.setJobRecordSuccess(job_id,{})
    return "job %s set to succeed" % (job_id)

@mod.route('/test/queue/fail/<job_id>', methods=["POST", "GET"])
@consent_required
def queue_fail_job(job_id):
    q = JobsQueue(db_session)
    q.setJobRecordFail(job_id,{})
    return "job %s set to failed" % (job_id)

@mod.route('/test/queue/start/<job_id>', methods=["POST", "GET"])
@consent_required
def queue_start_job(job_id):
    q = JobsQueue(db_session)
    q.setJobRecordStarted(job_id)
    return "job %s set to started" % (job_id)


@mod.route('/test/queue/pop_qjob', methods=["POST", "GET"])
@consent_required
def queue_pop_queued_job():
    q = JobsQueue(db_session)
    #print "numjobs:",len(q)
    qjob_record = q.popNextQueuedJob()
    #print "new numjobs:",len(q)
    if qjob_record is None:
      return "no jobs in queue"
    return json.dumps(qjob_record.id)

@mod.route('/test/', methods=["POST", "GET"])
@consent_required
def test():
    result = scalar_tasks.test.delay(10)   
    taskid = result.task_id
    return json.dumps(taskid)

@mod.route('/test/result/<task_id>', methods=["POST", "GET"])
@consent_required
def test_result(task_id):
    result = scalar_tasks.test.AsyncResult(task_id)
    if result.failed():
        return 'result failed'
    elif not result.ready():
        return 'result not ready yet'
    returnval = result.result
    return json.dumps(returnval)

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
    user_metadata = scalar_tasks.TileMetadata()
    current_app.logger.info("got fetch first tile request")
    query = request.args.get('query',"",type=str)
    taskname = request.args.get('task',"",type=str)
    ds = None
    if len(query) == 0: #look for data set
        data_set = request.args.get('data_set',"",type=str)
        if len(data_set) > 0:
            #ds = db_session.query(DataSet).filter_by(name=data_set).one()
            try:
                ds = db_session.query(DataSet).filter_by(name=data_set).one()
                query = ds.query
                session['data_set'] = ds.id
                if len(taskname) > 0 and taskname not in session: # record what data set was used for this task
                    session[taskname]=ds.id
                current_app.logger.info("found data set %s" % (data_set))

            except:
                current_app.logger.warning("could not locate data set %s" % \
                                           (data_set))
    session['query'] = query
    user_metadata.original_query = query
    data_threshold = request.args.get('data_threshold',0,type=int)
    session['threshold'] = data_threshold
    user_metadata.user_id = session['user_id']
    options = {'user_id':session['user_id']}
    session['usenumpy'] = request.args.get('usenumpy',False,type=bool)
    if data_threshold > 0:
        user_metadata.threshold = data_threshold
        options['data_threshold'] = data_threshold
    if session['usenumpy']:
        options['usenumpy'] = False
    options['user_metadata'] = user_metadata.get_dict()
    session['user_metadata'] = user_metadata.get_dict() # save for later
    #result = scalar_tasks.fft.delay(query,options)   
    #taskid = result.task_id
    fft = scalar_tasks.Fft(db_session)
    fft.run(query,options) # my queue now
    taskid = fft.job_id()
    #print "taskid:",taskid
    return json.dumps(taskid)

@mod.route('/fetch-first-tile/result/<task_id>',methods=["POST", "GET"])
@consent_required
def fetch_first_tile_result(task_id):
    user_metadata = scalar_tasks.TileMetadata()
    user_metadata.load_dict(session['user_metadata'])
    # setup job wrapper
    fft = scalar_tasks.Fft(db_session)
    # query for our job
    fft.peek(task_id)
    if not fft.finished():
        current_app.logger.info("fetch_first_tile result for job %s not ready yet" \
                                    % (task_id))
        return json.dumps('wait')
    elif fft.failed():
        current_app.logger.info("fetch_first_tile request failed for job %s" \
                                    % (task_id))
        return json.dumps('fail')
    queryresultarr = fft.result()
    '''
    result = scalar_tasks.fft.AsyncResult(task_id)
    if result.failed():
        current_app.logger.info("fetch_first_tile request failed for job %s" \
                                    % (task_id))
        return json.dumps('fail')
    elif not result.ready():
        current_app.logger.info("fetch_first_tile result for job %s not ready yet" \
                                    % (task_id))
        return json.dumps('wait')
    queryresultarr = result.result
    '''
    if 'error' not in queryresultarr: # error didn't happen
        user_metadata.total_zoom_levels = queryresultarr['max_zoom']
        user_metadata.threshold = queryresultarr['threshold']
        user_metadata.saved_qpresults = queryresultarr.pop('original_saved_qpresults',None)
        current_app.logger.info("result length: "+str(len(queryresultarr['data'])))
        tile_id = [0,0]
        if 'saved_qpresults' in queryresultarr:
            tile_id = [0] * int(queryresultarr['saved_qpresults']['numdims'])
        user_trace = UserTrace(tile_id=str(tile_id),
                                zoom_level=0,
                                threshold=session['threshold'],
                                query=session['query'],
                                user_id=g.user.id,
                                dataset_id=None)
        # save current tile info for tracking tile selection
        uts = UserTileSelection(tile_id=str(tile_id),
                                zoom_level=0,
                                threshold=session['threshold'],
                                query=session['query'],
                                user_id=g.user.id,
                                dataset_id=None,
                                image=None)
        if g.ds is not None: #there is an associated data set
            user_trace.dataset_id = g.ds.id
            uts.dataset_id = g.ds.id
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
    session.pop('user_metadata',None)
    session['user_metadata'] = user_metadata.get_dict() # save updates
    #print "user_metadata.saved_qpresults:",user_metadata.saved_qpresults
    return json.dumps(queryresultarr)

@mod.route('/fetch-tile',methods=["POST", "GET"])
@consent_required
def fetch_tile():
    user_metadata = scalar_tasks.TileMetadata()
    user_metadata.load_dict(session['user_metadata'])
    #print "user_metadata.saved_qpresults:",user_metadata.saved_qpresults
    current_app.logger.info("got fetch tile request")
    tile_id = request.args.getlist('temp_id[]')
    for i in range(len(tile_id)):
        tile_id[i] = int(tile_id[i])
    x_label = request.args.get('x_label',"",type=str)
    y_label = request.args.get('y_label',"",type=str)
    level = request.args.get('level',"",type=int)
    options = {'user_id':session['user_id']}
    if session['usenumpy']:
        options['usenumpy'] = False
    options['user_metadata'] = user_metadata.get_dict()
    session['tile_id'] = tile_id
    session['zoom_level'] = level
    
    ft = scalar_tasks.Ft(db_session)
    ft.run(tile_id,level,options) # my queue now
    taskid = ft.job_id()
    #print "taskid:",taskid
    return json.dumps(taskid)



@mod.route('/fetch-tile/result/<task_id>',methods=["POST", "GET"])
@consent_required
def fetch_tile_result(task_id):
    user_metadata = scalar_tasks.TileMetadata()
    user_metadata.load_dict(session['user_metadata'])

    # setup job wrapper
    ft = scalar_tasks.Ft(db_session)
    # query for our job
    ft.peek(task_id)
    if not ft.finished():
        current_app.logger.info("fetch_first_tile result for job %s not ready yet" \
                                    % (task_id))
        return json.dumps('wait')
    elif ft.failed():
        current_app.logger.info("fetch_first_tile request failed for job %s" \
                                    % (task_id))
        return json.dumps('fail')
    queryresultarr = ft.result()

    if 'saved_qpresults' in queryresultarr:
        tile_id = session['tile_id']
        level = session['zoom_level']
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
            current_app.logger.warning("unable to insert into database: %r" % (str(e)))
            #print "utu:",utu
        current_app.logger.info("got here")
    return json.dumps(str(0))


@mod.route('/filters-cleared/',methods=["POST","GET"])
@consent_required
def filters_cleared():
    query = None
    if g.ds is None:
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
                                    dataset_id=g.ds.id)
        db_session.add(ufu)
        db_session.commit()
    except Exception as e:
        current_app.logger.warning("unable to insert filter update into database: %r" % (str(e)))
    return json.dumps(str(0))


@mod.route('/filters-applied/',methods=["POST","GET"])
@consent_required
def filters_applied():
    query = None
    if g.ds is None:
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
                                    dataset_id=g.ds.id)
            db_session.add(ufu)
            db_session.commit()
        except Exception as e:
            current_app.logger.warning("unable to insert filter update into database: %r" % (str(e)))
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
        current_app.logger.warning("unable to insert into database %r" % (str(e)))
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
                                       % (str(uts)))
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
                current_app.logger.warning("item: %r,%r,%r,%r,%r,%r" % (item.x_inv,item.y_inv,item.z_inv,item.color,str(item.tile_id),item.zoom_level))
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
         try:
             g.ds = db_session.query(DataSet).filter_by(id=session['data_set']).one()
             #db_session.add(g.ds)
             #db_session.commit()
         except:
             pass
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


