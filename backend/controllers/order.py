from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, requests, datetime
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response

load_dotenv()
oanda_platform = os.environ.get('OANDA_PLATFORM')
oanda_account = os.environ.get('OANDA_ACCOUNT')
oanda_API_key = os.environ.get('OANDA_API_KEY')

order_bp = Blueprint('order', __name__, url_prefix='/api/order')


@order_bp.post('/oanda/')
@jwt_required()
def create_market_order_oanda():
    try:
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/orders"
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        data = {
            'order': {
                'stopLossOnFill': {
                    'timeInForce': "GTC",
                    'price': "155.00000",
                },
                'takeProfitOnFill': {
                    'price': "157.00000",
                },
                'timeInForce': "FOK",
                'instrument': "USD_JPY",
                'units': "1000",
                'type': "MARKET",
                'positionFill': "DEFAULT",
                'clientExtensions': {
                    'comment': "trader_1",
                    'tag': "strategy_1",
                    'id': "my_order_1",
                },
            },
        }
        response = requests.post(endpoint, headers=headers, json=data)
        # capture response data
        if response.status_code == 201:
            add_client_extensions_to_trade()
            return jsonify({'status': 'ok', 'msg': 'order created'}), 201
        else:
            log_error(f'Failed to create order: {response.status_code} {response.text}')
            return jsonify({{'status code': response.status_code}, {'msg': response.text}})
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500


@order_bp.post('/oanda/updateClientExtensions')
@jwt_required()
def add_client_extensions_to_trade():
    try:
        # endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/trades/{trade_id}/clientExtensions"
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/trades/18/clientExtensions"
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        data = {
            'clientExtensions': {
                'comment': "trader_1",
                'tag': "strategy_1",
                'id': "my_order_1",
            },
        }
        response = requests.put(endpoint, headers=headers, json=data)
        # capture response data
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'msg': 'order created, filled and corresponding trade client extensions updated'}), 201
        else:
            log_error(f'Failed to update client extensions for trade 18: {response.status_code} {response.text}')
            return jsonify({{'status code': response.status_code}, {'msg': f'order created but failed to update client extensions for trade 18: {response.text}'}})
    except Exception as e:
        log_error(f'Unexpected error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'An unexpected error has occurred'}), 500