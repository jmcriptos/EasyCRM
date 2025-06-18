# app/core/__init__.py
from flask import Blueprint

core = Blueprint('core', __name__, template_folder='templates/core')

# No importes modelos aquí; deja que controller los pida cuando los necesite.
from . import controller

