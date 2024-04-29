from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db
from werkzeug.utils import secure_filename


strategy_bp = Blueprint('strategy', __name__, url_prefix='/api/strategy')
ALLOWED_EXTENSIONS = ['py']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@strategy_bp.put("/create/")
@jwt_required()
def create_strategy():
    conn = None
    try:
        claims = get_jwt()
        user_id = claims['id']
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        if not claims['role'] == 'Trader':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        form_data = request.form
        try:
            type = int(form_data['type'])
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'type must be a positive integer'}), 400
        name = form_data['name']
        if not isinstance(name, (str,)) or not len(name) <= 50:
            return jsonify({'status': 'error', 'msg': 'name must be 50 characters or less string'}), 400
        comments = form_data['comments']
        if not isinstance(comments, (str,)) or not len(name) <= 500:
            return jsonify({'status': 'error', 'msg': 'comments must be 500 characters or less string'}), 400

        if 'file' not in request.files:
            return jsonify({'status': 'error', 'msg': 'No file found'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'msg': 'No file found'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['SCRIPT_FOLDER'], filename)
            file.save(file_path)
            conn = connect_to_db()
            with conn.cursor() as cur:
                new_strategy = """
                INSERT INTO strategies (owner_id, type, name, comments, script_path)
                VALUES (%s,%s,%s,%s,%s)
                """
                cur.execute(new_strategy, (user_id, type, name, comments, file_path))
            return jsonify(({'status': 'ok', 'msg': 'File uploaded successfully'})), 201
        return jsonify({'status': 'error', 'msg': 'Invalid file extension'}), 400
    except KeyError:
        return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500
    finally:
        if conn:
            conn.close()


@strategy_bp.put("/execute/")
def execute_strategy():
    conn = connect_to_db()
    pass


