from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests, datetime
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response
import psycopg

load_dotenv()
oanda_platform = os.environ.get('OANDA_PLATFORM')
oanda_account = os.environ.get('OANDA_ACCOUNT')
oanda_API_key = os.environ.get('OANDA_API_KEY')

syncdata_bp = Blueprint('syncdata', __name__, url_prefix='/api/sync')


trade_states = None
connect = connect_to_db_dict_response()
with connect.cursor() as cursor:
    cursor.execute("""SELECT * FROM trade_state""")
    trade_states = cursor.fetchall()


def get_trade_id_by_state(list_of_trade_states_dict, state):
    for trade_state in list_of_trade_states_dict:
        if trade_state['state'].lower() == state.lower():
            return trade_state['id']
    return None


@syncdata_bp.get('/oanda/')
@jwt_required()
def sync_with_oanda():
    try:
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/changes"
        latest_transaction_id = 4
        payload = {'sinceTransactionID': latest_transaction_id}
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        response = requests.get(endpoint, params=payload, headers=headers)
        response_data = None
        if response.status_code == 200:
            try:
                response_data = response.json()
                """
                log_trades_opened and log_trades_reduced functions returns a dictionary:
                updated: True   if successfully logged new trades
                or
                updated: None   if no new trades were in detected.
                """
                check_open_trade_response = log_trades_opened(response_data)
                check_reduced_trade_response = log_trades_reduced(response_data)
                """
                log_trades_closed returns a dictionary with two key value pairs:
                updated: True   if successfully logged new trades
                or
                updated: None   if no new trades were in detected,
                closed_trades: [{id: id, user_id: user_id, realized_pl: realized_pl, close_time: close_time} ...]
                """
                check_closed_trade_response = log_trades_closed(response_data)
                if check_closed_trade_response['updated']:
                    # audit closed trade
                    audit_closed_trade_and_update_trader_nav(check_closed_trade_response['closed_trades'])
                return jsonify({'status': 'ok'}), 200
            except ValueError as e:
                log_error(f'Invalid JSON response: {response_data}\nerror: {e}')
                return jsonify({'status': 'error', 'message': 'Invalid JSON response'}), 500
        else:
            log_error(f'Failed to fetch data: {response.status_code} {response.text}')
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500


def log_trades_opened(response):
    conn = None
    try:
        list_of_trades_opened = response['changes']['tradesOpened']
        trade_info = response['state']['trades']
        if len(list_of_trades_opened) == 0:
            return {'updated': None}
        print(f'{len(list_of_trades_opened)} List of trades opened:\n')
        log_info(f'{len(list_of_trades_opened)} List of trades opened:')
        conn = connect_to_db()
        with conn.cursor() as cur:

            for trade in list_of_trades_opened:
                print(f'{len(list_of_trades_opened)} open trade: {trade}')
                log_info(f'{len(list_of_trades_opened)} open trade: {trade}')
                user_id = 1
                transaction_id = trade['id']
                open_time = trade['openTime']
                current_units = trade['currentUnits']
                instrument = trade['instrument']
                financing = trade['financing']
                initial_units = trade['initialUnits']
                price = trade['price']
                realized_pl = trade['realizedPL']
                unrealized_pl = [trade['unrealizedPL'] for trade in trade_info if trade['id'] == transaction_id][0]
                margin_used = [trade['marginUsed'] for trade in trade_info if trade['id'] == transaction_id][0]
                state = trade['state']
                state_id = get_trade_id_by_state(trade_states, state)
                if not state_id:
                    raise ValueError(f'{state} is not a valid state')
                check_existing_trade = """
                SELECT * FROM trades WHERE transaction_id = %s
                """
                cur.execute(check_existing_trade, (transaction_id,))
                result = cur.fetchone()
                if result:
                    update_trade = """
                    UPDATE trades
                    SET user_id = %s, open_time = %s, current_units = %s, financing = %s, initial_units = %s, instrument = %s, price = %s, realized_pl = %s, unrealized_pl = %s, state_id = %s, update_time = %s, margin_used = %s
                    WHERE transaction_id = %s
                    """
                    values = (user_id, open_time, current_units, financing, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, datetime.datetime.now(), margin_used, transaction_id)
                    cur.execute(update_trade, values)
                else:
                    insert_new_trade = """
                    INSERT INTO trades (user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, margin_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, margin_used)
                    cur.execute(insert_new_trade, values)

            conn.commit()
        return {'updated': True}
    except KeyError as e:
        print(f'KeyError: {e}')
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def log_trades_reduced(response):
    conn = None
    try:
        list_of_trades_reduced = response['changes']['tradesReduced']
        trade_info = response['state']['trades']
        if len(list_of_trades_reduced) == 0:
            return {'updated': None}
        print(f'{len(list_of_trades_reduced)} trades reduced:\n')
        log_info(f'{len(list_of_trades_reduced)} trades reduced:')
        conn = connect_to_db()
        with conn.cursor() as cur:

            for trade in list_of_trades_reduced:
                print(f'reduced trade: {trade}')
                log_info(f'reduced trade: {trade}')
                user_id = 1
                transaction_id = trade['id']
                open_time = trade['openTime']
                current_units = trade['currentUnits']
                instrument = trade['instrument']
                financing = trade['financing']
                initial_units = trade['initialUnits']
                price = trade['price']
                realized_pl = trade['realizedPL']
                unrealized_pl = [trade['unrealizedPL'] for trade in trade_info if trade['id'] == transaction_id][0]
                margin_used = [trade['marginUsed'] for trade in trade_info if trade['id'] == transaction_id][0]
                state = 'reduced'
                state_id = get_trade_id_by_state(trade_states, state)
                if not state_id:
                    raise ValueError(f'{state} is not a valid state')
                check_existing_trade = """
                SELECT * FROM trades WHERE transaction_id = %s
                """
                cur.execute(check_existing_trade, (transaction_id,))
                result = cur.fetchone()
                if result:
                    update_trade = """
                    UPDATE trades
                    SET user_id = %s, open_time = %s, current_units = %s, financing = %s, initial_units = %s, instrument = %s, price = %s, realized_pl = %s, unrealized_pl = %s, state_id = %s, update_time = %s, margin_used = %s
                    WHERE transaction_id = %s
                    """
                    values = (
                    user_id, open_time, current_units, financing, initial_units, instrument, price, realized_pl,
                    unrealized_pl, state_id, datetime.datetime.now(), margin_used, transaction_id)
                    cur.execute(update_trade, values)
                else:
                    insert_new_trade = """
                    INSERT INTO trades (user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, margin_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                    user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price,
                    realized_pl, unrealized_pl, state_id, margin_used)
                    cur.execute(insert_new_trade, values)

            conn.commit()
        return {'updated': True}
    except KeyError as e:
        print(f'KeyError: {e}')
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def log_trades_closed(response):
    conn = None
    try:
        list_of_trades_closed = response['changes']['tradesClosed']
        list_of_closed_trades = []
        if len(list_of_trades_closed) == 0:
            return {'updated': None, 'closed_trades': list_of_closed_trades}
        print(f'{len(list_of_trades_closed)} trades closed:\n')
        log_info(f'{len(list_of_trades_closed)} trades closed:')
        conn = connect_to_db_dict_response()

        with conn.cursor() as cur:

            for trade in list_of_trades_closed:
                print(f'closed trade: {trade}')
                log_info(f'closed trade: {trade}')
                user_id = 1
                transaction_id = trade['id']
                open_time = trade['openTime']
                close_time = trade['closeTime']
                current_units = trade['currentUnits']
                instrument = trade['instrument']
                financing = trade['financing']
                initial_units = trade['initialUnits']
                price = trade['price']
                realized_pl = trade['realizedPL']
                unrealized_pl = 0
                margin_used = 0
                state = 'closed'
                state_id = get_trade_id_by_state(trade_states, state)
                if not state_id:
                    raise ValueError(f'{state} is not a valid state')
                check_existing_trade = """
                SELECT * FROM trades WHERE transaction_id = %s
                """
                cur.execute(check_existing_trade, (transaction_id,))
                result = cur.fetchone()
                if result:
                    close_trade = """
                    UPDATE trades
                    SET user_id = %s, open_time = %s, close_time = %s, current_units = %s, financing = %s, initial_units = %s, instrument = %s, price = %s, realized_pl = %s, unrealized_pl = %s, state_id = %s, update_time = %s, margin_used = %s
                    WHERE transaction_id = %s
                    RETURNING id, user_id, realized_pl, financing, close_time
                    """
                    values = (
                    user_id, open_time, close_time, current_units, financing, initial_units, instrument, price,
                    realized_pl, unrealized_pl, state_id, datetime.datetime.now(), margin_used, transaction_id)
                    cur.execute(close_trade, values)
                    closed_trade_info_dictionary = cur.fetchone()
                    list_of_closed_trades.append(closed_trade_info_dictionary)
                else:
                    insert_new_trade = """
                    INSERT INTO trades (user_id, open_time, close_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, margin_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, realized_pl, close_time
                    """
                    values = (
                    user_id, open_time, close_time, current_units, financing, transaction_id, initial_units, instrument, price,
                    realized_pl, state_id, margin_used)
                    cur.execute(insert_new_trade, values)
                    closed_trade_info_dictionary = cur.fetchone()
                    list_of_closed_trades.append(closed_trade_info_dictionary)
            conn.commit()

        return {'updated': True, 'closed_trades': list_of_closed_trades}
    except KeyError as e:
        print(f'KeyError: {e}')
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def audit_closed_trade_and_update_trader_nav(list_of_closed_trades):
    """
    Example parameter data type:
    [{'id': 1, 'user_id': 1, 'realized_pl': Decimal('5.87780'), 'financing': Decimal('-0.13150'), 'close_time': datetime.datetime(2024, 4, 26, 10, 17, 27, 681522, tzinfo=zoneinfo.ZoneInfo(key='Asia/Singapore'))}]
    """
    conn = None
    try:
        conn = connect_to_db()
        with conn.cursor() as cur:
            for closed_trades in list_of_closed_trades:
                trade_id = closed_trades['id']
                user_id = closed_trades['user_id']
                net_realized_pl = closed_trades['realized_pl'] + closed_trades['financing']
                close_time = closed_trades['close_time']

                find_existing_trade = """SELECT * FROM trade_audit WHERE trade_id = %s"""
                values = (trade_id,)
                cur.execute(find_existing_trade, values)
                result = cur.fetchone()
                if result:
                    continue
                else:
                    insert_new_audit = """INSERT INTO trade_audit (trade_id, user_id, net_realized_pl, close_time)
                    VALUES (%s, %s, %s, %s)
                    """
                    new_audit_values = (trade_id, user_id, net_realized_pl, close_time)
                    cur.execute(insert_new_audit, new_audit_values)

                    get_trader_cash_balance = """ SELECT balance FROM cash_balances WHERE trader_id = %s
                    """
                    get_trader_balance_values = (user_id,)
                    cur.execute(get_trader_cash_balance, get_trader_balance_values)
                    balance = cur.fetchone()[0]
                    new_balance = balance + net_realized_pl

                    update_trader_nav = """
                    UPDATE cash_balances
                    SET balance = %s
                    WHERE trader_id = %s
                    """
                    update_trader_nav_values = (new_balance, user_id)
                    cur.execute(update_trader_nav, update_trader_nav_values)

            conn.commit()
    except Exception as e:
        log_error(f'Error in auditing closed trade.\nClosed trades that failed to log: {list_of_closed_trades}.\nError message: {str(e)}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

