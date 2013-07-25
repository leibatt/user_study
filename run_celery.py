from app import app
from app.util.celery.celery_config import celery


if __name__ == '__main__':
    with app.app_context():
        celery.start()
