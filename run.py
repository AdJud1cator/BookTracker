from flask_migrate import Migrate
from app import create_app, db
from config import DeploymentConfig

if __name__ == '__main__':
    app = create_app(DeploymentConfig)
    migrate = Migrate(app, db)
    app.run(debug=False)