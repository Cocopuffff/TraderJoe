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
            SELECT 
                c.balance AS balance,
                c.margin_used AS margin_used,
                c.margin_available AS margin_available,
                c.nav AS nav,
                (SELECT SUM(net_realized_pl) FROM trade_audit WHERE user_id = %s) AS realized_pl,
                (SELECT SUM(unrealized_pl) FROM trades WHERE user_id = %s) AS unrealized_pl
            FROM cash_balances c
            WHERE c.trader_id = %s
            """
            cur.execute(get_account_summary, (user_id, user_id, user_id))
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


@trades_menu_bp.get("/positions/")
@jwt_required()
def get_positions_by_user():
    try:
        claims = get_jwt()
        user_id = claims['id']
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_positions_by_user = """
                SELECT s.name AS strategy_name, a.instrument AS instrument, t.unrealized_pl AS unrealized_pl, t.current_units AS units, t.transaction_id AS id
                FROM active_strategies_trades a
                JOIN strategies s
                ON a.strategy_id = s.id
                JOIN trades t
                ON t.id = a.trade_id
                WHERE a.user_id = %s AND t.state_id = 1;
                """
            cur.execute(get_positions_by_user, (user_id,))
            positions = cur.fetchall()
        return jsonify({'positions': positions}), 200
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500


@trades_menu_bp.get("/strategies/")
@jwt_required()
def list_active_strategies_by_user():
    try:
        claims = get_jwt()
        user_id = claims['id']
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_strategies_by_user = """
                SELECT a.id as id, s.name AS strategy_name, a.instrument AS instrument, t.initial_units AS initial_units, 
                t.current_units AS units, t.transaction_id AS trade_id, a.is_active as is_active, a.pid as pid
                FROM active_strategies_trades a
                JOIN strategies s
                ON a.strategy_id = s.id
                LEFT JOIN trades t
                ON t.id = a.trade_id
                JOIN instruments i
                ON a.instrument = i.name
                WHERE a.user_id = %s;
                """
            cur.execute(get_strategies_by_user, (user_id,))
            strategy_instrument_trade = cur.fetchall()
        return jsonify({'strategy_instrument_trade': strategy_instrument_trade}), 200
    except Exception as e:
        log_error(f'An error has occurred: {str(e)}')
        return jsonify({'status': 'error', 'msg': 'an error has occurred'}), 500