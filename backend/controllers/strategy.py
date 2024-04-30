import importlib.util

from flask import Blueprint, request, jsonify, current_app
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db
from werkzeug.utils import secure_filename
import threading

strategy_bp = Blueprint('strategy', __name__, url_prefix='/api/strategy')
ALLOWED_EXTENSIONS = ['py']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Dictionary to hold information of running threads for trading scripts
threads = {}


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
            conn = connect_to_db()
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM strategy_type WHERE id = %s', (type,))
                id = cur.fetchone()
                if not id:
                    return jsonify({'status': 'error', 'msg': 'invalid type'}), 404
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
            relative_file_path = os.path.relpath(file_path, start=current_app.root_path)
            file.save(file_path)
            with conn.cursor() as cur:
                new_strategy = """
                INSERT INTO strategies (owner_id, type, name, comments, script_path)
                VALUES (%s,%s,%s,%s,%s)
                """
                cur.execute(new_strategy, (user_id, type, name, comments, relative_file_path))
                conn.commit()
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


@strategy_bp.post("/execute/")
@jwt_required()
def execute_strategy():
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
        data = request.json
        instrument_name = data.get('instrument')
        strategy = data.get('strategy')
        if not instrument_name or not strategy:
            return jsonify({'status': 'error', 'msg': 'Missing instrument or strategy parameter'}), 400
        try:
            strategy = int(strategy)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'strategy must be a positive integer'}), 400
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, owner_id, script_path FROM strategies WHERE id= %s", (strategy,))
            strategy_row = cur.fetchone()
            if not strategy_row:
                return jsonify({'status': 'error', 'msg': 'strategy not found'}), 404
            if not strategy_row[1][0] == user_id:
                return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
            cur.execute("SELECT * FROM instruments WHERE name = %s", (instrument_name,))
            instrument = cur.fetchone()
            if not instrument:
                return jsonify({'status': 'error', 'msg': 'instrument not found'}), 404
            script_path = strategy_row[2][0]
            thread = threading.Thread(target=run_script, args=(script_path, instrument_name))
            thread.start()

        return jsonify({'status': 'ok', 'msg': 'Trading script started'}), 202
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


def run_script(script_path, instrument_name):
    try:
        spec = importlib.util.spec_from_file_location(script_path.rsplit("/", 1)[-1].split(".")[0], script_path)
        trade_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(trade_script)
        trade_script.main(instrument_name)
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')
