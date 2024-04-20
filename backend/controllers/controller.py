from flask import Blueprint, request, jsonify, render_template
from dotenv import load_dotenv
from FlaskTemplate.utilities import log_info, log_error, log_warning

books_bp = Blueprint('movies', __name__, url_prefix='/api')

load_dotenv()


@books_bp.route('/')
def get_books():
    try:
        books_list = [
            {
                "genre": "science fiction",
                "book_name": "Dune"
            },
            {
                "genre": "horror",
                "book_name": "IT",
            },
            {
                "genre": "science fiction",
                "book_name": "Three Body problem",
            },
        ]
        return jsonify(books_list), 200
    except Exception as e:
        error_message = str(e)
        log_error(error_message)
        return jsonify({"error": error_message}), 400


@books_bp.post('/')
def get_book_by_id():
    try:
        pass
    except Exception as e:
        error_message = str(e)
        return jsonify({"error": error_message}), 400


@books_bp.delete('/')
def delete_books():
    try:
        pass
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        error_message = str(e)
        return jsonify({"error": error_message}), 400
