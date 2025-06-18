# app/auth/controller.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from app.auth.forms import LoginForm
from app.auth.models import User
from app.extensions import login_manager
from . import auth   # blueprint creado en app/auth/__init__.py


# ───────────────────────────────────────────────────────────────
#  Carga de usuario para Flask-Login
# ───────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id: str):
    """Recibe el id (str) que User.get_id() guardó en la sesión."""
    return User.query.get(int(user_id))


# ───────────────────────────────────────────────────────────────
#  Inicio de sesión
# ───────────────────────────────────────────────────────────────
@auth.route("/login", methods=["GET", "POST"])
@auth.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.home"))

    form = LoginForm()

    if form.validate_on_submit():          # ahora sí existe gracias a FlaskForm
        # La validación cruzada dejó el usuario bueno en form.user
        login_user(
            form.user,
            remember=getattr(form, "remember", False)
        )

        # Redirige a la URL original (‘next’) o al home
        next_url = request.args.get("next") or url_for("core.home")
        return redirect(next_url)

    return render_template("auth/login.html", form=form)


# ───────────────────────────────────────────────────────────────
#  Cierre de sesión
# ───────────────────────────────────────────────────────────────
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))



