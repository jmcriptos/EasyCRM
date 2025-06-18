# app/auth/__init__.py
from flask import Blueprint

auth = Blueprint('auth', __name__, template_folder='templates/auth')

# No hace falta importar User aquí.
# El propio controller importará lo que necesite, dentro de cada vista.
from . import controller
