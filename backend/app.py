from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from datetime import timedelta
from backend.controllers import watchlist, auth, strategy, syncdata, order, tradesmenu, review
from backend.utilities import log_error
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import BadRequest
from backend.db.db import connect_to_db


def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder='static')
    CORS(app, resources={r"/*": {
        "origins": "*",
        "allow_headers": [
            "Content-Type", "Authorization", "Access-Control-Allow-Credentials"
        ],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    }})

    # Create / define directory to store python strategy scripts
    app.config['SCRIPT_FOLDER'] = os.path.join(app.root_path, 'scripts')
    os.makedirs(app.config['SCRIPT_FOLDER'], exist_ok=True)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    jwt = JWTManager(app)

    app.register_blueprint(watchlist.watchlist_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(strategy.strategy_bp)
    app.register_blueprint(syncdata.syncdata_bp)
    app.register_blueprint(order.order_bp)
    app.register_blueprint(tradesmenu.trades_menu_bp)
    app.register_blueprint(review.review_trader_bp)

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        if 'Failed to decode JSON object' in str(e):
            return jsonify({'status': 'error', 'msg': 'An error has occurred'}), 400
        return jsonify({'status': 'error', 'msg': 'Bad request'}), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        log_error(f'Server Error: {e}')
        return jsonify({'status': 'error', 'msg': 'An error has occurred'}), 500

    conn = connect_to_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE active_strategies_trades SET is_active = FALSE, pid = NULL")
        conn.commit()
    conn.close()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)

# Run the following in terminal:
# pipenv shell
# flask run --debug
# or
# flask run
