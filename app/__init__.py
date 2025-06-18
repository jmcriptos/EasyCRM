# app/__init__.py
from flask import Flask

from config import BaseConfig
from app.extensions import bcrypt, login_manager, db, migrate


def create_app(config_class: type = BaseConfig) -> Flask:
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    _register_extensions(app)
    _register_blueprints(app)

    return app


# ------------------------------------------------------------------
# Extensiones
# ------------------------------------------------------------------
def _register_extensions(app: Flask) -> None:
    """Inicializa las extensiones de Flask que usa la app."""
    bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"          # ← redirección por defecto
    # opcional:
    # login_manager.login_message_category = "info"

    db.init_app(app)
    migrate.init_app(app, db)                        # habilita comandos flask db


# ------------------------------------------------------------------
# Blueprints
# ------------------------------------------------------------------
def _register_blueprints(app: Flask) -> None:
    """Importa y registra todos los blueprints."""
    # Importar aquí evita dependencias prematuras con modelos y db
    from app.core import core as core_blueprint
    from app.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(core_blueprint)


