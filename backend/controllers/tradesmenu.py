from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response
from backend.controllers.syncdata import sync_with_oanda

trades_menu_bp = Blueprint('trades_menu', __name__, url_prefix='/api/tradesMenu')

load_dotenv()
leverage = int(os.environ.get('LEVERAGE'))
print(f'Leverage: {leverage}')


@trades_menu_bp.get('/history/')
@jwt_required()
def get_trade_history_by_userid():
    try:
        claims = get_jwt()
        user_id = claims['id']
        if not claims['role'] == 'Trader':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        sync_with_oanda()
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_closed_trades = """
            SELECT *
            FROM trades
            WHERE user_id = %s AND state_id = 3
            ORDER BY close_time DESC
            """
            cur.execute(get_closed_trades, (user_id,))
            items = cur.fetchall()
            results = [item for item in items]
            print(results)
            return jsonify({'history': results})
    except KeyError:
        return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@trades_menu_bp.get('/summary/')
@jwt_required()
def get_summary_by_userid():
    try:
        claims = get_jwt()
        user_id = claims['id']
        if not claims['role'] == 'Trader':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        sync_with_oanda()
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_account_summary = """
            SELECT *
            FROM cash_balances
            WHERE trader_id = %s
            """
            cur.execute(get_account_summary, (user_id,))
            result = cur.fetchone()
            result['currency'] = 'SGD'
            result['leverage'] = 20
            print(result)
            return jsonify({'summary': result})
    except KeyError:
        return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500