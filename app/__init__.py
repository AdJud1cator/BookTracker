from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from .errors import register_error_handlers

bp = Blueprint('main', __name__)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()   

def create_app():
    global app
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    register_error_handlers(app)

    return app