from flask import Flask, Blueprint, request, jsonify, render_template
from dotenv import load_dotenv
import os
from backend.view import data as website_data
from backend.controllers import controller, auth
from backend.view import data as website_data
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager

def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder='static')
    CORS(app, resources={r"/*": {
        "origins": "*",
        "allow_headers": [
            "Content-Type", "Authorization", "Access-Control-Allow-Credentials"
        ],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }})

    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')

    app.register_blueprint(controller.books_bp)
    app.register_blueprint(auth.auth_bp)
    jwt = JWTManager(app)

    @app.route('/')
    def index():
        data = website_data.get_index_data()
        return render_template('index.html', **data)

    return app

# def start_app():
#     app = create_app()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)

    # print(f'Hello, World! Your secret key is {app.config['SECRET_KEY']}')
    # app.run(debug=True, port=port)

# Run the following in terminal:
# pipenv shell
# flask run --debug
# or
# flask run
