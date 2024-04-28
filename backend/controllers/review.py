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
                a.can_trade,
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
            WHERE a.role_id = 1 AND c.trader_id IS NOT NULL AND a.account_disabled IS FALSE
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


@review_trader_bp.patch('/toggleTrade/')
@jwt_required()
def toggle_ability_to_trade():
    conn = None
    try:
        claims = get_jwt()
        data = request.json
        can_trade = data['can_trade']
        if not claims['role'] == 'Manager':
            return jsonify({'status': 'error', 'msg': 'unauthorized'}), 401
        if not isinstance(can_trade, bool):
            raise TypeError('can_trade has to be boolean')
        try:
            user_id = int(data['id'])
        except ValueError:
            return jsonify({'status': 'error', 'msg': 'ID must be a positive integer'}), 400
        print(data)
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
            update_trader_ability_to_trade = """
            UPDATE auth
            SET can_trade = %s
            WHERE id = %s
            """
            cur.execute(update_trader_ability_to_trade, (can_trade, user_id))
            conn.commit()
        # need to add cancel all open trades and orders
        return jsonify({'status': 'ok', 'msg': 'trader ability to trade changed successfully'}), 200
    except TypeError as e:
        return jsonify({'status': 'error', 'msg': f'{e}'}), 400
    except KeyError:
        return jsonify({'status': 'error', 'msg': "missing parameters"}), 400
    except Exception as e:
        log_error(f"Something went wrong when toggling trader's ability to trade: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'msg': "Something went wrong when toggling trader's ability to trade"}), 500
    finally:
        if conn:
            conn.close()


@review_trader_bp.patch('/fire/')
@jwt_required()
def fire_trader():
    conn = None
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
            update_trader_ability_to_trade = """
                        UPDATE auth
                        SET can_trade = FALSE, account_disabled = TRUE
                        WHERE id = %s
                        """
            cur.execute(update_trader_ability_to_trade, (user_id,))
            sync_with_oanda()
            get_trade_cash = """
                        SELECT balance
                        FROM cash_balances
                        WHERE trader_id = %s
                        """
            cur.execute(get_trade_cash, (user_id,))
            trader_balance = cur.fetchone()[0]

            zero_out_trader_balance = """
                        UPDATE cash_balances
                        SET balance = 0 
                        WHERE  trader_id = %s;
                        """
            cur.execute(zero_out_trader_balance, (user_id,))

            move_trader_cash_to_unallocated = """
                                    UPDATE cash_balances
                                    SET balance = balance + %s 
                                    WHERE id = 1 AND description = 'Unallocated Capital';
                                    """
            cur.execute(move_trader_cash_to_unallocated, (trader_balance,))
            conn.commit()
            # need to add cancel all open trades and orders
        return jsonify({'status': 'ok', 'msg': 'trader ability to trade changed successfully'}), 200
    except KeyError:
        return jsonify({'status': 'error', 'msg': "missing parameters"}), 400
    except Exception as e:
        log_error(f"Something went wrong when toggling trader's ability to trade: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify(
            {'status': 'error', 'msg': "Something went wrong when toggling trader's ability to trade"}), 500
    finally:
        if conn:
            conn.close()
