from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests, datetime
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning, get_function_name
from backend.db.db import connect_to_db, connect_to_db_dict_response
from decimal import Decimal

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


def check_strategy_exists(cur, strategy_id):
    try:
        print(f"Checking existence for strategy_id: {strategy_id}")
        cur.execute("SELECT COUNT(*) AS count FROM strategies WHERE id = %s", (strategy_id,))
        result = cur.fetchone()

        if isinstance(result, dict):
            count = result.get('count', 0)
            exists = count > 0
            print(f"Result as dict - count: {count}, exists: {exists}")
        else:
            # Assuming result is a tuple if not a dict
            count = result[0]
            exists = count > 0
            print(f"Result as tuple - count: {count}, exists: {exists}")

        return exists
    except Exception as e:
        print(f"Error while checking strategy existence: {e}")
        return False


@syncdata_bp.get('/oanda/')
@jwt_required()
def sync_with_oanda():
    function_name = None
    try:
        function_name = get_function_name()
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
                tie_order_to_trade_and_active_strategies(response_data)
                update_open_trade(response_data)
                if check_closed_trade_response['updated']:
                    audit_closed_trade_and_update_trader_cash_balance(check_closed_trade_response['closed_trades'])

                if check_open_trade_response['updated'] or check_reduced_trade_response['updated'] or check_closed_trade_response['updated']:
                    update_latest_polled_transaction(response_data)
                update_trader_nav()
                update_all_margin_used_and_available()
                return jsonify({'status': 'ok'}), 200
            except ValueError as e:
                log_error(f'Invalid JSON response: {response_data}\nerror: {e}', function_name)
                return jsonify({'status': 'error', 'message': 'Invalid JSON response'}), 500
        else:
            log_error(f'Failed to fetch data: {response.status_code} {response.text}', function_name)
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}', function_name)
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500


def log_trades_opened(response):
    conn = None
    function_name = None
    try:
        function_name = get_function_name()
        list_of_trades_opened = response['changes']['tradesOpened']
        trade_info = response['state']['trades']
        if len(list_of_trades_opened) == 0:
            return {'updated': None}
        log_info(f'{len(list_of_trades_opened)} List of trades opened:')
        conn = connect_to_db()
        with conn.cursor() as cur:

            for trade in list_of_trades_opened:
                log_info(f'{len(list_of_trades_opened)} open trade: {trade}')
                user_id = None
                client_extensions = trade.get('clientExtensions', '')
                if client_extensions:
                    user_id = client_extensions.get('tag').split("_")[1]
                    strategy_id = client_extensions.get('comment').split("_")[1]
                else:
                    log_info(f"client extensions user_id not found, defaulting user_id to 1 for {trade['id']}")
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
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def log_trades_reduced(response):
    conn = None
    function_name = None
    try:
        function_name = get_function_name()
        list_of_trades_reduced = response['changes']['tradesReduced']
        trade_info = response['state']['trades']
        if len(list_of_trades_reduced) == 0:
            return {'updated': None}
        print(f'{len(list_of_trades_reduced)} trades reduced.')
        log_info(f'{len(list_of_trades_reduced)} trades reduced:')
        conn = connect_to_db()
        with conn.cursor() as cur:

            for trade in list_of_trades_reduced:
                log_info(f'reduced trade: {trade}')
                user_id = None
                client_extensions = trade.get('clientExtensions', '')
                if client_extensions:
                    user_id = client_extensions.get('tag').split("_")[1]
                    strategy_id = client_extensions.get('comment').split("_")[1]
                else:
                    log_info(f"client extensions user_id not found, defaulting user_id to 1 for {trade['id']}")
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
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def log_trades_closed(response):
    conn = None
    function_name = None
    try:
        function_name = get_function_name()
        list_of_trades_closed = response['changes']['tradesClosed']
        list_of_closed_trades = []
        if len(list_of_trades_closed) == 0:
            return {'updated': None, 'closed_trades': list_of_closed_trades}
        print(f'{len(list_of_trades_closed)} trades closed.')
        log_info(f'{len(list_of_trades_closed)} trades closed:')
        conn = connect_to_db_dict_response()

        with conn.cursor() as cur:

            for trade in list_of_trades_closed:
                log_info(f'closed trade: {trade}')
                user_id = None
                client_extensions = trade.get('clientExtensions', '')
                if client_extensions:
                    user_id = client_extensions.get('tag').split("_")[1]
                    strategy_id = client_extensions.get('comment').split("_")[1]
                else:
                    log_info(f"client extensions user_id not found, defaulting user_id to 1 for {trade['id']}")
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, realized_pl, close_time
                    """
                    values = (
                        user_id, open_time, close_time, current_units, financing, transaction_id, initial_units, instrument, price,
                        realized_pl, unrealized_pl, state_id, margin_used)
                    cur.execute(insert_new_trade, values)
                    closed_trade_info_dictionary = cur.fetchone()
                    list_of_closed_trades.append(closed_trade_info_dictionary)
            conn.commit()

        return {'updated': True, 'closed_trades': list_of_closed_trades}
    except KeyError as e:
        print(f'KeyError: {e}')
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}', function_name)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def tie_order_to_trade_and_active_strategies(response):
    conn = None
    try:
        orders_filled = response['changes']['ordersFilled']
        orders_cancelled = response['changes']['ordersCancelled']
        conn = connect_to_db_dict_response()

        for order in orders_filled:
            if order['type'] == 'MARKET' and order['state'] == 'FILLED' and not order['positionFill'] == 'REDUCE_ONLY':
                print(order)
                order_id = order['id']
                oanda_trade_id = order.get('tradeOpenedID', '')
                if not oanda_trade_id:
                    oanda_trade_id = order.get('tradeReducedID', '')
                instrument = order['instrument']
                user_id = None
                strategy_id = None
                client_extensions = order.get('clientExtensions', '')
                if client_extensions:
                    user_id = client_extensions.get('tag').split("_")[1]
                    strategy_id = client_extensions.get('comment').split("_")[1]
                else:
                    log_info(f"client extensions user_id not found, defaulting user_id to 1 for {order['id']}")
                    user_id = 1
                with conn.cursor() as cur:
                    cur.execute("SELECT trader_id FROM orders WHERE order_id = %s", (order_id,))
                    trader_id = cur.fetchone()
                    if trader_id:
                        trader_id = trader_id[0]

                        cur.execute("UPDATE trades SET user_id = %s WHERE transaction_id = %s", (trader_id, oanda_trade_id))
                        cur.execute("UPDATE orders SET completed = TRUE WHERE order_id = %s", (order_id,))
                    cur.execute('SELECT id FROM trades WHERE transaction_id = %s', (oanda_trade_id,))
                    result = cur.fetchone()
                    if result:
                        trade_id = result['id']
                    if client_extensions and strategy_id:

                        if check_strategy_exists(cur, strategy_id):
                            update_active_strategy_trade = """UPDATE active_strategies_trades SET trade_id = %s, is_active = %s
                            WHERE user_id = %s AND strategy_id = %s AND instrument = %s AND trade_id IS NULL;
                            """
                            cur.execute(update_active_strategy_trade,
                                        (trade_id, True, user_id, strategy_id, instrument))
                            updated_rows = cur.rowcount

                            if updated_rows == 0:
                                print("no rows updated, inserting instead.")
                                insert_active_strategy_trade = """
                                INSERT INTO active_strategies_trades (user_id, strategy_id, instrument, trade_id, is_active)
                                VALUES (%s, %s, %s, %s, %s)
                                """
                                cur.execute(insert_active_strategy_trade,
                                            (user_id, strategy_id, instrument, trade_id, True))
                    conn.commit()

        for order in orders_cancelled:
            if order['type'] == 'MARKET':
                order_id = order['id']
                with conn.cursor() as cur:
                    cur.execute("UPDATE orders SET completed = TRUE WHERE order_id = %s", (order_id,))
                    conn.commit()
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
                net_realized_pl = closed_trades['realized_pl'] + closed_trades.get('financing', Decimal('0.00'))
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


def update_open_trade(response):
    conn = None
    try:
        open_trades = response['state']['trades']
        conn = connect_to_db_dict_response()
        for order in open_trades:
            unrealized_pl = order['unrealizedPL']
            margin_used = order['marginUsed']
            transaction_id = order['id']
            with conn.cursor() as cur:
                update_trade = """
                UPDATE trades SET unrealized_pl = %s, margin_used = %s WHERE id = %s
                RETURNING unrealized_pl, margin_used
                """
                cur.execute(update_trade, (unrealized_pl, margin_used, transaction_id))
                result = cur.fetchone()
                conn.commit()
    except Exception as e:
        log_error(f"error occurred updating open trades: {str(e)}")
        if conn:
            conn.rollback()
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
                    margin_used = result.get('margin_used', Decimal('0.00'))
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
