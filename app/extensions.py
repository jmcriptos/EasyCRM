# app/extensions.py
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate

# IMPORTA la instancia única, no crees otra
from app.database import db

bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()


