# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, ValidationError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from .models import User


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(message="Enter your username")]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Enter your password")]
    )
    remember = BooleanField("Remember me")   # opcional; usa .remember.data

    # ────────────────────────────────────────────────────────────
    # Validación cruzada de credenciales
    # ────────────────────────────────────────────────────────────
    def validate_password(self, field):      # WTForms llama automáticamente
        try:
            user = (
                User.query                        # busca por username
                .filter(User.username == self.username.data)
                .one()                            # lanza NoResult/MultiResult
            )
        except (MultipleResultsFound, NoResultFound):
            raise ValidationError("Invalid user / password")

        if not user.check_password(field.data):
            raise ValidationError("Invalid user / password")

        # Si todo ok, guarda el objeto para que lo use la vista
        self.user = user
        return True
