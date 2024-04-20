from flask import Blueprint, request, jsonify

# Models API page
auth_bp = Blueprint('roles', __name__, url_prefix='/auth')

@auth_bp.get('/')
def get_roles():
    roles_list = [
        "admin", "user"
    ]

    return jsonify(roles_list), 200