from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

load_dotenv()


@watchlist_bp.post('/')
@jwt_required()
def get_watchlist_instrument_by_userid():
    try:
        claims = get_jwt()
        user_id = claims['id']
        conn = connect_to_db()
        with conn.cursor() as cur:
            get_watchlist = """
            SELECT *
            FROM watchlist
            WHERE user_id = %s
            """
            cur.execute(get_watchlist, (user_id,))
            items = cur.fetchall()
            results = [{'id': item[0], 'name': item[2], 'display_name': item[3], 'type': item[4]} for item in items]
            return jsonify({'watchlist': results})
    except KeyError:
        return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@watchlist_bp.delete('/<int:watchlist_id>/')
@jwt_required()
def delete_watchlist_instrument(watchlist_id):
    conn = None
    try:
        conn = connect_to_db()
        claims = get_jwt()
        user_id = claims['id']
        with conn.cursor() as cur:
            get_delete_item_owner = """
                        SELECT user_id FROM watchlist
                        WHERE id = %s
                        """
            cur.execute(get_delete_item_owner, (watchlist_id,))
            owner = cur.fetchone()
            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'No record found with the provided ID'}), 404
            if not owner[0] == user_id:
                return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
            get_delete_item = """
            DELETE FROM watchlist
            WHERE id = %s
            """
            cur.execute(get_delete_item, (watchlist_id,))
            conn.commit()

            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'No record found with the provided ID'}), 404
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500
    finally:
        if conn:
            conn.close()


@watchlist_bp.put('/add/')
@jwt_required()
def add_instrument_to_watchlist():
    conn = None
    try:
        data = request.json
        name = data['name']
        display_name = data['display_name']
        instrument_type = data['type']
        claims = get_jwt()
        user_id = claims['id']

        conn = connect_to_db()
        with conn.cursor() as cur:
            add_instrument = """
            INSERT INTO watchlist (user_id, name, display_name, type) VALUES (%s, %s, %s, %s)
            RETURNING id, user_id, name, display_name, type
            """
            cur.execute(add_instrument, (user_id, name, display_name, instrument_type))
            new_instrument = cur.fetchone()
            conn.commit()
            return jsonify({'status': 'ok', 'new_instrument': {
                'id': new_instrument[0],
                'user_id': new_instrument[1],
                'name': new_instrument[2],
                'display_name': new_instrument[3],
                'type': new_instrument[4]
            }}), 201
    except KeyError:
        return jsonify({'status': 'error', 'message': 'missing email parameter in body'}), 401
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500
    finally:
        if conn:
            conn.close()
