from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db

load_dotenv()
oanda_platform = os.environ.get('OANDA_PLATFORM')
oanda_account = os.environ.get('OANDA_ACCOUNT')
oanda_API_key = os.environ.get('OANDA_API_KEY')

order_bp = Blueprint('order', __name__, url_prefix='/api/order')


@order_bp.post('/oanda/create/')
@jwt_required()
def create_market_order_oanda():
    try:
        claims = get_jwt()
        trader_id = claims['id']
        data = request.json
        try:
            instrument = data['instrument']
            stop_loss_price = data['stop_loss_price']
            take_profit_price = data['take_profit_price']
            abs_script_path = data['script_path']
            units = data['units']
            print(data)
        except KeyError as e:
            log_error(f'missing key parameters: {e}')
            return jsonify({'status': 'error', 'msg': 'missing key parameters'}), 400
        try:
            if 'JPY' in instrument:
                stop_loss_price = f'{float(stop_loss_price):.2f}'
                take_profit_price = f'{float(take_profit_price):.2f}'
            else:
                stop_loss_price = f'{float(stop_loss_price):.5f}'
                take_profit_price = f'{float(take_profit_price):.5f}'
            units = int(units)
        except ValueError:
            log_error(f'parameters needs to be valid numbers'), 400
            return jsonify({'status': 'error', 'msg': 'parameters needs to be valid numbers'}), 400
        if not isinstance(instrument, (str,)):
            log_error(f'instrument parameter has to be a string'), 400
            return jsonify({'status': 'error', 'msg': 'instrument parameter has to be a string'}), 400

        conn = connect_to_db()
        with conn.cursor() as cur:
            get_script_path_by_trader = """
            SELECT id, script_path FROM strategies WHERE owner_id = %s"""
            cur.execute(get_script_path_by_trader, (trader_id,))
            strategies = cur.fetchall()
            matching_strategy_id = None
            if strategies:
                for strategy in strategies:
                    print(strategy)
                    if strategy[1] in abs_script_path:
                        matching_strategy_id = strategy[0]
                        print('found strategy!')
                        break
            if not matching_strategy_id:
                return jsonify({'status': 'error', 'msg': 'matching strategy not found'}), 404
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/orders"
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        data = {
            'order': {
                'stopLossOnFill': {
                    'timeInForce': "GTC",
                    'price': stop_loss_price,
                },
                'takeProfitOnFill': {
                    'price': take_profit_price,
                },
                'timeInForce': "FOK",
                'instrument': instrument,
                'units': units,
                'type': "MARKET",
                'positionFill': "DEFAULT",
                "clientExtensions": {
                    'tag': f'trader_{trader_id}',
                    'comment': f'strategy_{matching_strategy_id}'
                }
            },
        }
        response = requests.post(endpoint, headers=headers, json=data)
        # capture response data
        response_data = None
        if response.status_code == 201:
            try:
                response_data = response.json()
                log_info(response_data)
                print(response_data)
                # check if order is filled
                try:
                    trade_id = response_data['orderFillTransaction']['id']
                    return jsonify({'status': 'ok', 'msg': 'order filled'}), 201
                except KeyError:
                    log_info(f"no order filled yet for: {response_data}")
                # else, check if order is created and log it
                try:
                    order_id = response_data['orderCreateTransaction']['id']
                    conn = connect_to_db()
                    with conn.cursor() as cur:
                        insert_unfilled_order = """INSERT INTO orders (trader_id, order_id) VALUES (%s, %s)"""
                        cur.execute(insert_unfilled_order, (trader_id, order_id))
                    return jsonify({'status': 'ok', 'msg': 'order created'}), 201
                except Exception as e:
                    log_error(f"an error has occurred for {response_data}: {str(e)}")
                return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500
            except ValueError as e:
                log_error(f'Invalid JSON response: {response_data}\nerror: {e}')
                return jsonify({'status': 'error', 'message': 'Invalid JSON response'}), 500
        else:
            log_error(f'Failed to create order: {response.status_code} {response.text}')
            return jsonify({'status code': response.status_code, 'msg': response.text})
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500


@order_bp.post('/oanda/cancelAllTrades/')
@jwt_required()
def cancel_all_trades_by_trader_oanda():
    try:
        claims = get_jwt()
        data = request.json

        if not claims['role'] == 'Manager':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        try:
            user_id = int(data['id'])
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        conn = connect_to_db()
        with conn.cursor() as cur:
            get_role_of_user = """
                                SELECT u.role_name
                                FROM auth a
                                JOIN user_roles u
                                ON a.role_id = u.role_id
                                WHERE a.id = %s
                                """
            cur.execute(get_role_of_user, (user_id,))
            result = cur.fetchone()
            if not result:
                return jsonify({'status': 'error', 'msg': "not found"}), 404
            elif not result[0] == 'Trader':
                return jsonify({'status': 'error', 'msg': "unauthorized"}), 401
            cur.execute("SELECT transaction_id FROM trades WHERE state_id != 3 AND user_id = %s", (user_id,))
            trade_ids = cur.fetchall()
            for trade_id in trade_ids:
                endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/trades/{trade_id[0]}/close"
                headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
                data = {
                    'order': 'ALL'
                }
                response = requests.post(endpoint, headers=headers, json=data)
                # capture response data
                response_data = None
                if response.status_code == 200:
                    pass
                else:
                    log_error(f'Failed to cancel order #{trade_id[0]}: {response.status_code} {response.text}')
                    # return False
        # return True
        return jsonify({'status': 'ok', 'msg': f'{len(trade_ids)} trades cancelled'}), 200
    except KeyError:
        return jsonify({'status': 'error', 'msg': "missing parameters"}), 400
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500


def cancel_trade_by_trade_id(trade_id):
    conn = None
    try:
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/trades/{trade_id}/close"
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        data = {
            'order': 'ALL'
        }
        response = requests.put(endpoint, headers=headers, json=data)
        if response.status_code == 200:
            conn = connect_to_db()
            with conn.cursor() as cur:
                get_pid = """
                SELECT a.pid FROM active_strategies_trades a 
                JOIN trades t ON a.trade_id = t.id 
                WHERE a.trade_id = %s
                """
                cur.execute(get_pid, (trade_id,))
                pid = cur.fetchone()
                if pid:
                    pid = pid[0]
                    cur.execute("UPDATE active_strategies_trades SET pid = NULL WHERE pid = %s", (pid,))
                    conn.commit()

            return True
        else:
            log_error(f'Failed to cancel order #{trade_id[0]}: {response.status_code} {response.text}')

            return False
    except Exception as e:
        log_error(f'Failed to cancel order #{trade_id}: {e}')
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

