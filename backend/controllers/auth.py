import os

from flask import Blueprint, request, jsonify
import bcrypt
from backend.utilities import log_info, log_warning, log_error
from backend.db.db import connect_to_db
from dotenv import load_dotenv

load_dotenv()
manager_secret_key = os.environ.get('MANAGER_SECRET_KEY')

# Models API page
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.get('/')
def get_roles():
    roles_list = [
        "admin", "user"
    ]

    return jsonify(roles_list), 200


@auth_bp.put('/register')
def register():
    try:
        # validate json body
        data = request.json
        email = data['email']
        display_name = data['display_name']
        password = data['password']
        role = data['role']
        if role == 'Manager':
            secret_key = data['secret_key']
            if not secret_key == manager_secret_key:
                return jsonify({"status": "error", "msg": "an error has occurred"}), 500

        # check db for unique email & display name and valid role
        conn = connect_to_db()
        with conn.cursor() as cur:
            find_duplicates = """
            SELECT id FROM auth
            WHERE display_name = %s OR email = %s
            """
            cur.execute(find_duplicates, (display_name, email))
            if cur.fetchone():
                return jsonify({"status": "error", "msg": "email / display name has been taken"}), 409

            get_role_id = """
            SELECT role_id FROM user_roles WHERE role_name = %s
            """
            print(f"Fetching role_id for role: {role}")
            cur.execute(get_role_id, (role,))
            role_result = cur.fetchone()
            if role_result is None:
                return jsonify("invalid role"), 400
            role_id = role_result[0]

            hashed = hash_password(password)

            register_user = f"""
            INSERT INTO auth(display_name, password_hash, email, role_id) VALUES
            (%s, %s, %s, %s)
            """

            cur.execute(register_user, (display_name, hashed, email, role_id))
            conn.commit()
    except KeyError:
        return jsonify({"status": "error", "msg": "missing parameters in body"}), 400
    except Exception as e:
        log_error(e)
        return jsonify({"status": "error", "msg": "an error has occurred"}), 500

    return jsonify({"status": "ok", "msg": "account created"}), 201


def hash_password(password):
    """Hash a password for storing."""
    try:
        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        password_hashed = bcrypt.hashpw(password_bytes, salt)
        return password_hashed.decode('utf-8')
    except Exception as e:
        log_error(f"error in hashing password: {e}")
        raise Exception("error in hashing password")


def check_password(input_password, db_hash):
    """checking password"""
    try:
        password_bytes = input_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, db_hash)
    except Exception as e:
        print(e)
        log_error(f"user input password {input_password} resulted in following error:\n{e}")
        return False

