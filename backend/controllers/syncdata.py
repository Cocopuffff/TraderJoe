from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests, datetime
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db
import psycopg
from psycopg.rows import dict_row

load_dotenv()
oanda_platform = os.environ.get('OANDA_PLATFORM')
oanda_account = os.environ.get('OANDA_ACCOUNT')
oanda_API_key = os.environ.get('OANDA_API_KEY')

syncdata_bp = Blueprint('syncdata', __name__, url_prefix='/api/sync')


trade_states = None
with psycopg.connect("dbname=traderjoe user=db_user", row_factory=dict_row) as connect:
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
        r = requests.get(endpoint, params=payload, headers=headers).json()
        # print(r)
        log_trades_opened(r)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        log_error(e)


def log_trades_opened(response):
    conn = None
    try:
        list_of_trades_opened = response['changes']['tradesOpened']
        print(list_of_trades_opened)
        print(len(list_of_trades_opened))

        conn = connect_to_db()
        with conn.cursor() as cur:

            for trade in list_of_trades_opened:
                user_id = 1
                transaction_id = trade['id']
                open_time = trade['openTime']
                current_units = trade['currentUnits']
                instrument = trade['instrument']
                financing = trade['financing']
                initial_units = trade['initialUnits']
                price = trade['price']
                realized_pl = 0.0000
                unrealized_pl = 0.0000
                state = trade['state']
                state_id = get_trade_id_by_state(trade_states, state)
                if not state_id:
                    raise ValueError(f'{state} is not a valid state')
                check_duplicate_trade = """
                SELECT * FROM trades WHERE transaction_id = %s
                """
                cur.execute(check_duplicate_trade, (transaction_id,))
                result = cur.fetchone()
                if result:
                    update_trade = """
                    UPDATE trades
                    SET user_id = %s, open_time = %s, current_units = %s, financing = %s, initial_units = %s, instrument = %s, price = %s, realized_pl = %s, unrealized_pl = %s, state_id = %s, update_time = %s
                    WHERE transaction_id = %s
                    RETURNING id
                    """
                    values = (user_id, open_time, current_units, financing, initial_units, instrument, price, realized_pl, unrealized_pl, state_id, datetime.datetime.now(),transaction_id)
                    cur.execute(update_trade, values)
                    trade_id = cur.fetchone()[0]
                else:
                    insert_new_trade = """
                    INSERT INTO trades (user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (user_id, open_time, current_units, financing, transaction_id, initial_units, instrument, price, realized_pl, unrealized_pl, state_id)
                    cur.execute(insert_new_trade, values)

            conn.commit()
    except KeyError as e:
        print(f'KeyError: {e}')
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
    except Exception as e:
        print(e)
        log_error(f'error when logging open trades: {e}')
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
