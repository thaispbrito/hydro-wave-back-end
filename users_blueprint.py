from flask import Blueprint, jsonify, g
from db_helpers import get_db_connection
import psycopg2, psycopg2.extras
from auth_middleware import token_required

users_blueprint = Blueprint('users_blueprint', __name__)

# Fetching all users, if authenticated
@users_blueprint.route('/users')
@token_required
def users_index():
    connection = get_db_connection()

    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users;")

    users = cursor.fetchall()

    connection.close()

    return jsonify(users), 200
   
# Fetching specific user by id, if authenticated
@users_blueprint.route('/users/<user_id>')
@token_required
def users_show(user_id):
    # If the user is looking for the details of another user, block the request
    # Send a 403 status code to indicate that the user is unauthorized
    if int(user_id) != g.user["id"]:
        return jsonify({"err": "Unauthorized"}), 403
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, username FROM users WHERE id = %s;", (user_id))
    user = cursor.fetchone()
    connection.close()
    if user is None:
        return jsonify({"err": "User not found"}), 404
    return jsonify(user), 200

