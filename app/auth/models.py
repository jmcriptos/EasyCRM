from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property

from flask_login import UserMixin

from app.database import db, Base          # ← la única fuente de db y Base
from app.extensions import bcrypt          # instancia de flask_bcrypt.Bcrypt


class User(UserMixin, Base):
    """Modelo de usuario con helpers para Flask-Login y bcrypt."""

    __tablename__ = "user"             

    # --- Campos ----------------------------------------------------------------
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(128), unique=True, index=True, nullable=False)

    # guardamos el hash en la BD; el atributo expuesto será .password
    _password  = db.Column("password", db.String(192), nullable=False)

    first_name = db.Column(db.String(128), nullable=False)
    last_name  = db.Column(db.String(128), nullable=False)

    active     = db.Column(db.Boolean, default=True, nullable=False)

    # --- Helpers CRUD -----------------------------------------------------------
    @classmethod
    def create(cls, **kwargs):
        """Crea y persiste un usuario. Lanza IntegrityError si hay duplicados."""
        user = cls(**kwargs)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise    # deja que la vista decida qué hacer con el error
        return user

    # --- Integración con Flask-Login -------------------------------------------
    def get_id(self):
        # Flask-Login almacenará este valor en la sesión
        return str(self.id)

    def is_active(self):
        return bool(self.active)

    # --- Gestión de contraseña --------------------------------------------------
    @hybrid_property
    def password(self):
        """Devuelve el hash; no expongas nunca la contraseña en texto plano."""
        return self._password

    @password.setter
    def password(self, plaintext: str):
        # bcrypt devuelve bytes → decodificamos a str para almacenarlo
        self._password = bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def check_password(self, plaintext: str) -> bool:
        """Comprueba si el texto plano coincide con el hash almacenado."""
        return bcrypt.check_password_hash(self._password, plaintext)

    # --- Representación útil en logs -------------------------------------------
    def __repr__(self):
        return f"<User {self.username}>"
