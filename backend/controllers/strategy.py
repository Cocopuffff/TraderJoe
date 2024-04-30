import importlib.util

from flask import Blueprint, request, jsonify, current_app
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response
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
        file = request.files.get('file')
        type = form_data.get('type', '')
        name = form_data.get('name', '')
        comments = form_data.get('comments', '')

        if not (type and name and comments and file):
            return jsonify({'status': 'error', 'msg': 'All fields are required'}), 400
        if not isinstance(type, (str,)):
            return jsonify({'status': 'error', 'msg': 'type must be a string'}), 400
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM strategy_type WHERE type = %s', (type,))
            type_id = cur.fetchone()
        if not type_id:
            return jsonify({'status': 'error', 'msg': 'invalid type'}), 404
        type_id = type_id[0]
        if not (0 < len(name) <= 50 and 0 < len(comments) <= 500):
            return jsonify({'status': 'error', 'msg': 'Invalid input lengths'}), 400

        if file.filename == '':
            return jsonify({'status': 'error', 'msg': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'msg': 'Invalid file extension'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['SCRIPT_FOLDER'], filename)
        relative_file_path = os.path.relpath(file_path, start=current_app.root_path)
        file.save(file_path)
        with conn.cursor() as cur:
            new_strategy = """
            INSERT INTO strategies (owner_id, type, name, comments, script_path)
            VALUES (%s,%s,%s,%s,%s)
            """
            cur.execute(new_strategy, (user_id, type_id, name, comments, relative_file_path))
            conn.commit()
        return jsonify(({'status': 'ok', 'msg': 'File uploaded successfully'})), 201
    except Exception as e:
        error_message = str(e)
        log_error(f'Error: {error_message}')
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


@strategy_bp.get("/")
@jwt_required()
def get_strategies_by_user():
    try:
        claims = get_jwt()
        user_id = claims['id']
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        if not claims['role'] == 'Trader':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_user_strategies = """
            SELECT s.id AS id, s.owner_id AS owner_id, s.name AS name, s.comments AS comments, s.script_path AS script_path, t.type AS type FROM strategies s
            JOIN strategy_type t
            ON s.type = t.id 
            WHERE s.owner_id = %s
            """
            cur.execute(get_user_strategies, (user_id,))
            strategies = cur.fetchall()
        conn.close()
        return jsonify({'strategies': strategies}), 200
    except Exception as e:
        log_error(f"an error has occurred: {str(e)}")
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@strategy_bp.get("/types/")
@jwt_required()
def get_strategies_types():
    try:
        claims = get_jwt()
        user_id = claims['id']
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        conn = connect_to_db()
        with conn.cursor() as cur:
            get_types = """
            SELECT type FROM strategy_type 
            """
            cur.execute(get_types)
            types = cur.fetchall()
            types = [type[0] for type in types]
        conn.close()
        return jsonify({'types': types}), 200
    except Exception as e:
        log_error(f"an error has occurred: {str(e)}")
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@strategy_bp.delete('/')
@jwt_required()
def delete_strategy_by_id():
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
        strategy_id = data.get('id')
        if not strategy_id:
            return jsonify({'status': 'error', 'msg': 'Missing strategy parameter'}), 400
        try:
            strategy_id = int(strategy_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'strategy must be a positive integer'}), 400
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            cur.execute('SELECT id, owner_id, script_path FROM strategies WHERE id = %s', (strategy_id,))
            strategy = cur.fetchone()
            if not strategy['owner_id'] == user_id:
                return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
            if not strategy:
                return jsonify({'status': 'error', 'msg': 'strategy not found'}), 404

            try:
                os.remove(strategy['script_path'])
            except OSError as e:
                log_error(f"Failed to delete file: {str(e)}")
                return jsonify({'status': 'error', 'msg': 'Failed to delete associated file'}), 500

            cur.execute('DELETE FROM strategies WHERE id = %s', (strategy_id,))
            conn.commit()
            return jsonify({'status': 'ok', 'msg': 'Strategy deleted successfully'}), 200
    except Exception as e:
        log_error(f"an error has occurred: {str(e)}")
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@strategy_bp.patch("/")
@jwt_required()
def update_strategy():
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
        file = request.files.get('file')
        strategy_id = form_data.get('id', '')
        type = form_data.get('type', '')
        name = form_data.get('name', '')
        comments = form_data.get('comments', '')

        if not (type and name and comments):
            return jsonify({'status': 'error', 'msg': 'All fields are required'}), 400
        if not isinstance(type, (str,)):
            return jsonify({'status': 'error', 'msg': 'type must be a string'}), 400
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            cur.execute('SELECT id, owner_id, script_path FROM strategies WHERE id = %s', (strategy_id,))
            strategy = cur.fetchone()
            if not strategy['owner_id'] == user_id:
                return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
            if not strategy:
                return jsonify({'status': 'error', 'msg': 'strategy not found'}), 404

        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM strategy_type WHERE type = %s', (type,))
            type_id = cur.fetchone()
            if not type_id:
                return jsonify({'status': 'error', 'msg': 'invalid type'}), 404
            type_id = type_id[0]
            if not (0 < len(name) <= 50 and 0 < len(comments) <= 500):
                return jsonify({'status': 'error', 'msg': 'Invalid input lengths'}), 400

        if file and file.filename:
            if not allowed_file(file.filename):
                return jsonify({'status': 'error', 'msg': 'Invalid file extension'}), 400
            try:
                os.remove(strategy['script_path'])
            except OSError as e:
                log_error(f"Failed to delete file: {str(e)}")
                return jsonify({'status': 'error', 'msg': 'Failed to delete associated file'}), 500
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['SCRIPT_FOLDER'], filename)
            relative_file_path = os.path.relpath(file_path, start=current_app.root_path)
            file.save(file_path)
            with conn.cursor() as cur:
                new_strategy = """
                UPDATE strategies SET type = %s, name = %s, comments = %s, script_path = %s WHERE id = %s
                """
                cur.execute(new_strategy, (type_id, name, comments, relative_file_path, strategy_id))
                conn.commit()
                conn.close()
            return jsonify(({'status': 'ok', 'msg': 'Update successful'})), 201
        else:
            with conn.cursor() as cur:
                # update without changing file
                update_sql = """
                UPDATE strategies SET type = %s, name = %s, comments = %s WHERE id=%s
                """
                values = (type_id, name, comments, strategy_id)
                cur.execute(update_sql, values)
                conn.commit()

                return jsonify(({'status': 'ok', 'msg': 'Update successful'})), 200
    except Exception as e:
        error_message = str(e)
        log_error(f'Error: {error_message}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500
    finally:
        if conn:
            conn.close()
