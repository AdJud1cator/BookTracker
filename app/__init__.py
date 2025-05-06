from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    global app
    app = Flask(__name__)
    app.secret_key = 'secret_key' # A temporary measure to apply authentication, needs to be changed
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from . import routes

    with app.app_context():
        db.create_all()

    return app