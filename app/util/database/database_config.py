def initialize_database(app):
    #initialize database
    import app.util.database.database as db
    db.configure_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_db()
