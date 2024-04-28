from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_jwt_extended import jwt_required, get_jwt
from backend.utilities import log_info, log_error, log_warning
from backend.db.db import connect_to_db, connect_to_db_dict_response
from backend.controllers.syncdata import sync_with_oanda

review_trader_bp = Blueprint('review_trader', __name__, url_prefix='/api/review')

load_dotenv()


@review_trader_bp.get('/performance/')
@jwt_required()
def get_traders_performance():
    try:
        claims = get_jwt()
        if not claims['role'] == 'Manager':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        sync_with_oanda()
        conn = connect_to_db_dict_response()
        with conn.cursor() as cur:
            traders_performance = """
            SELECT 
                a.id,
                a.display_name,
                a.email,
                MAX(c.nav) as current_nav,
                -- Yesterday's performance
                SUM(CASE 
                    WHEN t.close_time >= CURRENT_DATE - INTERVAL '1 day' AND t.close_time < CURRENT_DATE 
                    THEN t.realized_pl + t.financing ELSE 0 
                    END) AS yesterday_net_realized_pl,
                SUM(CASE 
                    WHEN t.open_time >= CURRENT_DATE - INTERVAL '1 day' 
                    THEN t.unrealized_pl ELSE 0 
                    END) AS yesterday_unrealized_pl,
            
                -- Last 7 days' performance
                SUM(CASE 
                    WHEN t.close_time >= CURRENT_DATE - INTERVAL '7 days' AND t.close_time < CURRENT_DATE 
                    THEN t.realized_pl + t.financing ELSE 0 
                    END) AS last_7_days_net_realized_pl,
                SUM(CASE 
                    WHEN t.open_time >= CURRENT_DATE - INTERVAL '7 days' 
                    THEN t.unrealized_pl ELSE 0 
                    END) AS last_7_days_unrealized_pl,
            
                -- Last 30 days' performance
                SUM(CASE 
                    WHEN t.close_time >= CURRENT_DATE - INTERVAL '30 days' AND t.close_time < CURRENT_DATE 
                    THEN t.realized_pl + t.financing ELSE 0 
                    END) AS last_30_days_net_realized_pl,
                SUM(CASE 
                    WHEN t.open_time >= CURRENT_DATE - INTERVAL '30 days' 
                    THEN t.unrealized_pl ELSE 0 
                    END) AS last_30_days_unrealized_pl,
            
                -- Year to date performance
                SUM(CASE 
                    WHEN t.close_time >= DATE_TRUNC('year', CURRENT_DATE) AND t.close_time < CURRENT_DATE
                    THEN t.realized_pl + t.financing ELSE 0
                    END) as ytd_net_realized_pl,
                SUM(CASE WHEN t.open_time >= DATE_TRUNC('year', CURRENT_DATE)
                    THEN t.unrealized_pl ELSE 0
                    END) as ytd_unrealized_pl
            FROM auth a
            LEFT JOIN trades t ON a.id = t.user_id
            LEFT JOIN cash_balances c ON a.id = c.trader_id
            WHERE a.role_id = 1 AND c.trader_id IS NOT NULL
            GROUP BY a.id;
            """
            cur.execute(traders_performance)
            performances = cur.fetchall()
            for performance in performances:
                performance['initial_balance'] = '1000.00000'
            return jsonify({'performances': performances}), 200
    except Exception as e:
        log_error(f"Something went wrong when getting traders' performance: {str(e)}")
        return jsonify({'status': 'error', 'msg': "Something went wrong when getting traders' performance"}), 500
