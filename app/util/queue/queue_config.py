from celery import Celery

celery = None

#integrate celery with flask
def initialize_celery(app):
    global celery
    celery = Celery(app.import_name)
    celery.conf.update(
        BROKER_TRANSPORT=app.config['BROKER_TRANSPORT'],
        BROKER_URL=app.config['BROKER_URL'],
        CELERY_RESULT_BACKEND=app.config['CELERY_RESULT_BACKEND'],
        CELERY_RESULT_DBURI=app.config['CELERY_RESULT_DBURI'],
    )
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
