# app/database/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()        # la instancia única que usarán todos los modelos
Base = db.Model          # opcional: alias si prefieres llamar al mixin "Base"


def populate_db(app):
    """
    Crea datos de prueba. Se llama una vez que la app y la BD están inicializadas.
    """
    # ⬇️ Importar aquí evita la importación circular
    from app.auth.models import User

    with app.app_context():        # asegura un contexto válido para db.session
        if not User.query.filter_by(username='test@gmail.com').first():
            admin = User(
                username='test@gmail.com',
                password='shh',
                first_name='Chris',
                last_name='Hall'
            )
            db.session.add(admin)
            db.session.commit()
