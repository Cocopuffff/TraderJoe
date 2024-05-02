import importlib.util

from flask import Blueprint, request, jsonify, current_app
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.controllers.order import cancel_trade_by_trade_id
from backend.db.db import connect_to_db, connect_to_db_dict_response
from werkzeug.utils import secure_filename
import threading
from subprocess import Popen

strategy_bp = Blueprint('strategy', __name__, url_prefix='/api/strategy')
ALLOWED_EXTENSIONS = ['py']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Dictionary to hold information of running threads for trading scripts
threads = {}
processes= {}

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


def run_script(script_path, instrument_name):
    try:
        spec = importlib.util.spec_from_file_location(script_path.rsplit("/", 1)[-1].split(".")[0], script_path)
        trade_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(trade_script)
        trade_script.main(instrument_name)
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')

@strategy_bp.post("/start/")
@jwt_required()
def start_strategy():
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
        strategy_id = data.get('strategy_id')
        if not instrument_name or not strategy_id:
            return jsonify({'status': 'error', 'msg': 'Missing instrument or strategy parameter'}), 400
        try:
            strategy_id = int(strategy_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'strategy must be a positive integer'}), 400
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, owner_id, script_path FROM strategies WHERE id= %s", (strategy_id,))
            strategy_row = cur.fetchone()
            if not strategy_row:
                return jsonify({'status': 'error', 'msg': 'strategy not found'}), 404
            if not strategy_row[1] == user_id:
                return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
            cur.execute("SELECT * FROM instruments WHERE name = %s", (instrument_name,))
            instrument = cur.fetchone()
            if not instrument:
                return jsonify({'status': 'error', 'msg': 'instrument not found'}), 404
            script_path = strategy_row[2]
            abs_script_path = os.path.join(current_app.root_path, script_path)

            cmd = ['python', abs_script_path, instrument_name]
            process = Popen(cmd)
            processes[process.pid] = process
            log_info(f'started subprocess: {str(process.pid)}')
            log_info(f'processes: {str(processes)}')

            insert_active_strategy = """
                                    INSERT INTO active_strategies_trades (user_id, strategy_id, instrument, is_active, pid)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """
            cur.execute(insert_active_strategy, (user_id, strategy_id, instrument_name, True, process.pid))
            conn.commit()
        return jsonify({'status': 'ok', 'msg': 'Trading script started', 'pid': process.pid}), 202
        # return jsonify({'status': 'ok', 'msg': 'Trading script started', 'thread_id': thread_id}), 202
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@strategy_bp.delete("/stop/")
@jwt_required()
def stop_strategy():
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
        active_strategy_trade_id = data.get('active_id', '')
        print(f'active_id: {active_strategy_trade_id}')
        if not active_strategy_trade_id:
            return jsonify({'status': 'error', 'msg': 'missing required parameters'}), 400
        pid = None
        conn = connect_to_db()
        with conn.cursor() as cur:
            get_pid = """
                SELECT a.pid AS pid, t.transaction_id AS trade_id, t.close_time as close_time 
                FROM active_strategies_trades a JOIN trades t ON a.trade_id = t.id 
                WHERE a.id = %s
                """
            cur.execute(get_pid, (active_strategy_trade_id,))
            result = cur.fetchone()
            cur.execute('DELETE FROM active_strategies_trades WHERE id = %s', (active_strategy_trade_id,))
            if result:
                pid = result[0]
                trade_id = result[1]
                close_time = result[2]
                if trade_id and close_time is None:
                    is_successful = cancel_trade_by_trade_id(trade_id)
                    if not is_successful:
                        conn.rollback()
                conn.commit()
                if not pid:
                    return jsonify({'status': 'ok', 'msg': 'deleted'}), 200
            else:
                return jsonify({'status': 'ok', 'msg': 'Stopped trading script'}), 200
            if pid and os.path.exists(f'/proc/{pid}'):
                process = processes.pop(pid, None)
                if process:
                    process.terminate()
                    process.wait()

                return jsonify({'status': 'ok', 'msg': 'Stopped trading script'}), 200
            else:
                return jsonify({'status': 'error', 'msg': 'Process not found'}), 404

    except Exception as e:
        log_error(f'An error has occurred in stopping strategy: {str(e)}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': 'An error has occurred in stopping strategy'}), 500
    finally:
        if conn:
            conn.close()


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
            check_for_conflict = """
            SELECT s.id, s.owner_id, s.script_path, a.id AS active_strat_id
            FROM strategies s
            JOIN active_strategies_trades a
            ON a.strategy_id = s.id
            WHERE s.id = %s
            """
            cur.execute(check_for_conflict, (strategy_id,))
            strategy = cur.fetchone()
            if not strategy['owner_id'] == user_id:
                return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
            if not strategy:
                return jsonify({'status': 'error', 'msg': 'strategy not found'}), 404
            if strategy['active_strat_id']:
                return jsonify({'status': 'error', 'msg': 'strategy is still in use!'}), 409

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
