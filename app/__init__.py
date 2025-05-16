from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from .errors import register_error_handlers

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    from app.blueprints import bp
    app.register_blueprint(bp)

    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # from app import routes 
    # from app import controllers 

    register_error_handlers(app)

    csrf.init_app(app)

    return app