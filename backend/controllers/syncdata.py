from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests, datetime
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response

load_dotenv()
leverage = int(os.environ.get('LEVERAGE'))
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
        db_latest_transaction_id = """
        SELECT last_transaction_id 
        FROM oanda_transaction_log
        ORDER BY recorded_at DESC
        LIMIT 1"""
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute(db_latest_transaction_id)
            latest_transaction_id_tuple = cur.fetchone()
            if latest_transaction_id_tuple:
                latest_transaction_id = latest_transaction_id_tuple[0]
            else:
                latest_transaction_id = 1
        payload = {'sinceTransactionID': latest_transaction_id}
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        response = requests.get(endpoint, params=payload, headers=headers)
        response_data = None
        print(f'latest_transaction_id: {latest_transaction_id}')
        if response.status_code == 200:
            try:
                response_data = response.json()
                if int(response_data['lastTransactionID']) == latest_transaction_id:
                    return jsonify({'status': 'ok', 'msg': 'already up to date'})
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
                tie_order_to_trade(response_data)
                if check_closed_trade_response['updated']:
                    audit_closed_trade_and_update_trader_cash_balance(check_closed_trade_response['closed_trades'])

                if check_open_trade_response['updated'] or check_reduced_trade_response['updated'] or check_closed_trade_response['updated']:
                    update_latest_polled_transaction(response_data)
                update_trader_nav()
                update_all_margin_used_and_available()
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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


def tie_order_to_trade(response):
    conn = None
    try:
        orders_filled = response['changes']['ordersFilled']
        orders_cancelled = response['changes']['ordersCancelled']
        conn = connect_to_db_dict_response()

        for order in orders_filled:
            if order['type'] == 'MARKET' and order['state'] == 'FILLED':
                order_id = order['id']
                with conn.cursor() as cur:
                    cur.execute("SELECT trader_id FROM orders WHERE order_id = %s", (order_id,))
                    trader_id = cur.fetchone()
                    if trader_id:
                        trader_id = trader_id[0]
                        trade_id = order['tradeOpenedID']
                        cur.execute("UPDATE trades SET user_id = %s WHERE transaction_id = %s", (trader_id, trade_id))
                        cur.execute("UPDATE orders SET completed = TRUE WHERE order_id = %s", (order_id,))
        for order in orders_cancelled:
            if order['type'] == 'MARKET':
                order_id = order['id']
                with conn.cursor() as cur:
                    cur.execute("UPDATE orders SET completed = TRUE WHERE order_id = %s", (order_id,))
    except KeyError:
        log_error("JSON structure unexpected")
        raise
    except Exception as e:
        log_error(f"An error has occurred: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def audit_closed_trade_and_update_trader_cash_balance(list_of_closed_trades):
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

                    update_trader_cash = """
                    UPDATE cash_balances
                    SET balance = %s
                    WHERE trader_id = %s
                    """
                    update_trader_cash_values = (new_balance, user_id)
                    cur.execute(update_trader_cash, update_trader_cash_values)

            conn.commit()
    except Exception as e:
        log_error(f'Error in auditing closed trade.\nClosed trades that failed to log: {list_of_closed_trades}.\nError message: {str(e)}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def update_trader_nav():
    conn = None
    try:
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_unrealized_pl_by_trader = """
            SELECT user_id, SUM(unrealized_pl) AS sum_of_unrealized_pl
            FROM trades
            GROUP BY user_id
            """
            cur.execute(get_unrealized_pl_by_trader)
            results = cur.fetchall()
            print(results)
            for result in results:
                unrealized_pl = result['sum_of_unrealized_pl']
                user_id = result['user_id']
                update_nav = """
                UPDATE cash_balances
                SET nav = balance + %s
                WHERE trader_id = %s
                """
                values = (unrealized_pl, user_id)
                cur.execute(update_nav, values)
            conn.commit()
    except Exception as e:
        log_error(f'Something went wrong updating trader nav: {str(e)}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def update_latest_polled_transaction(response_data):
    conn = None
    try:
        new_transaction_id = response_data['lastTransactionID']
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO oanda_transaction_log (last_transaction_id) VALUES (%s)""", (new_transaction_id,))
            conn.commit()
    except Exception as e:
        log_error(f'Something went wrong updating latest oanda polled transaction: {str(e)}')
        if conn:
            conn.rollback()
            raise
    finally:
        if conn:
            conn.close()


def update_all_margin_used_and_available():
    conn = None
    try:
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            get_all_margin_used_by_traders = """
            SELECT user_id, SUM(margin_used)
            FROM trades
            WHERE state_id != 3
            GROUP BY user_id
            """
            cur.execute(get_all_margin_used_by_traders)
            results = cur.fetchall()
            if results:
                for result in results:
                    trader_id = result['user_id']
                    margin_used = result['margin_used']
                    update_margin_used_and_available_for_each_trader = """
                    UPDATE cash_balances
                    SET margin_used = %s, margin_available = nav - %s
                    WHERE trader_id = %s
                    """
                    values = (margin_used, margin_used, trader_id)
                    cur.execute(update_margin_used_and_available_for_each_trader, values)
        conn.commit()
    except Exception as e:
        log_error(f'Error in updating margin used and available: {str(e)}')
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
