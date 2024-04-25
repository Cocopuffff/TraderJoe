from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db


strategy_bp = Blueprint('strategy', __name__, url_prefix='/api/strategy')
ALLOWED_EXTENSIONS = ['py']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@strategy_bp.put("/execute/")
def execute_strategy():
    conn = connect_to_db()
    pass


