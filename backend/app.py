from flask import Flask, Blueprint, request, jsonify, render_template
from dotenv import load_dotenv
import os
from FlaskTemplate.view import data as website_data
from FlaskTemplate.controllers import controller, auth

import sys
print(sys.path)

load_dotenv()

app = Flask(__name__, static_folder='static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_key')
app.register_blueprint(controller.books_bp)
app.register_blueprint(auth.auth_bp)


@app.route('/')
def index():
    data = website_data.get_index_data()
    return render_template('index.html', **data)


if __name__ == '__main__':
    print(f'Hello, World! Your secret key is {app.config['SECRET_KEY']}')
    app.run(debug=True)

# Run the following in terminal:
# pipenv shell
# flask run --debug
# or
# flask run
