from celery.signals import task_postrun
from app.util.celery.celery_config import celery
from app.util.database.database import db_session

@celery.task(name="tasks.test")
def test(num):
    return num+1

@task_postrun.connect
def close_session(*args, **kwargs):
    db_session.remove()
