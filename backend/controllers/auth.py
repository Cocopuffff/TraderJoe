import os
import uuid
from flask import Blueprint, request, jsonify
import bcrypt
from backend.utilities import log_info, log_warning, log_error
from backend.db.db import connect_to_db
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

load_dotenv()
manager_secret_key = os.environ.get('MANAGER_SECRET_KEY')
access_secret = os.environ.get('ACCESS_SECRET')
refresh_secret = os.environ.get('REFRESH_SECRET')

# Models API page
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


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
        db_password_bytes = db_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, db_password_bytes)
    except Exception as e:
        print(e)
        log_error(f"user input password {input_password} resulted in following error:\n{e}")
        return False


@auth_bp.get('/')
def get_roles():
    roles_list = [
        "Trader", "Manager"
    ]

    return jsonify(roles_list), 200


@auth_bp.put('/register/')
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


@auth_bp.post('/login/')
def login():
    try:
        # validate json body
        data = request.json
        email = data['email']
        input_password = data['password']
        conn = connect_to_db()
        with conn.cursor() as cur:
            get_hash = """
            SELECT auth.id AS user_id, auth.password_hash, user_roles.role_name AS role_name
            FROM auth
            JOIN user_roles
            ON user_roles.role_id = auth.role_id
            WHERE email = %s
            """
            cur.execute(get_hash, (email,))
            [user_id, password_hash, role_name] = cur.fetchone()
        if check_password(input_password, password_hash):
            access_claims = {
                'role': role_name,
                'id': user_id,
                'jwt_id': uuid.uuid4()
            }
            refresh_claims = {
                'role': role_name,
                'id': user_id,
                'jwt_id': uuid.uuid4()
            }

            access_token = create_access_token(identity=user_id,
                                               fresh=True,
                                               additional_claims=access_claims)
            refresh_token = create_refresh_token(identity=user_id,
                                                 additional_claims=refresh_claims)

            return jsonify({'access': access_token, 'refresh': refresh_token}), 200
    except KeyError:
        return jsonify({"status": "error", "msg": "missing parameters in body"}), 400
    except Exception as e:
        log_error(e)


@auth_bp.post('/refresh/')
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify({'access_token': access_token})


@auth_bp.post('/check-email/')
def check_email():
    try:
        data = request.json
        email = data['email']
        conn = connect_to_db()
        with conn.cursor() as cur:
            find_existing_email = """
            SELECT LOWER(email)
            FROM auth
            WHERE email = %s
            """
            cur.execute(find_existing_email, (email,))
            existing_email = cur.fetchone()
            if existing_email:
                return jsonify("duplicate email")
            else:
                return jsonify({"status": "ok", "msg": "email available"})
    except KeyError:
        return jsonify({"status": "error", "msg": "missing email parameter in body"}), 400
    except Exception as e:
        log_error(f"something went wrong while checking {email} for duplicates: {e}")


@auth_bp.post('/check-name/')
def check_name():
    try:
        data = request.json
        name = data['display_name']
        conn = connect_to_db()
        with conn.cursor() as cur:
            find_existing_email = """
            SELECT LOWER(display_name)
            FROM auth
            WHERE display_name = %s
            """
            cur.execute(find_existing_email, (name,))
            existing_name = cur.fetchone()
            if existing_name:
                return jsonify("duplicate email")
            else:
                return jsonify({"status": "ok", "msg": "email available"})
    except KeyError:
        return jsonify({"status": "error", "msg": "missing email parameter in body"}), 400
    except Exception as e:
        log_error(f"something went wrong while checking {email} for duplicates: {e}")


@auth_bp.route('/roles/')
def fetch_roles():
    try:
        conn = connect_to_db()
        with conn.cursor() as cur:
            find_existing_role = """
            SELECT role_name
            FROM user_roles
            """
            cur.execute(find_existing_role)
            roles = cur.fetchall()
            role_names = [role[0] for role in roles]
            return jsonify({'account_types': role_names})
    except KeyError:
        return jsonify({"status": "error", "msg": "missing email parameter in body"}), 400
    except Exception as e:
        log_error(f"something went wrong: {e}")