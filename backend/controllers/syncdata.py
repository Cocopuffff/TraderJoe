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

syncdata_bp = Blueprint('syncdata', __name__, url_prefix='/api/sync')


@syncdata_bp.get('/oanda/')
@jwt_required()
def sync_with_oanda():
    try:
        endpoint = f"{oanda_platform}/v3/accounts/{oanda_account}/changes"
        latest_transaction_id = 4
        payload = {'sinceTransactionID': latest_transaction_id}
        headers = {'Authorization': f'Bearer {oanda_API_key}', 'Connection': 'keep-alive'}
        r = requests.get(endpoint, params=payload, headers=headers).json()
        print(r)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        log_error(e)

