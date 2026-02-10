import os
import jwt
import bcrypt
import psycopg2, psycopg2.extras
from flask import Blueprint, jsonify, request
from db_helpers import get_db_connection

authentication_blueprint = Blueprint('authentication_blueprint', __name__)

# Sign-up route
@authentication_blueprint.route('/auth/sign-up', methods=['POST'])
def sign_up():
    try:
        new_user_data = request.get_json()

        # Establish the connection with the db
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Through the connection, run a SQL command to find existing user in the db
        cursor.execute("SELECT * FROM users WHERE username = %s;", (new_user_data["username"],))

        # Then fetch the user
        existing_user = cursor.fetchone()

        # Close the connection if there is a user and return message specifying existing user
        if existing_user:
            cursor.close()
            return jsonify({"err": "Username already taken"}), 400
        
        # Hash the password
        hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())
        
        # With no existing user, we can add the user to db and return the user object
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, username",
            (new_user_data["username"], hashed_password.decode("utf-8")),
        )

        # Grab the user object from db, then commit (save to db) then close connection with the DB
        created_user = cursor.fetchone()
        connection.commit()
        connection.close()

        # Construct the payload
        payload = {"username": created_user["username"], "id": created_user["id"]}

        # Create the token, attaching the payload
        token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))

        # Send the token instead of the user
        return jsonify({"token": token}), 201
    
    except Exception as err:
        return jsonify({"err": str(err)}), 401
    
#Sign-in route
@authentication_blueprint.route('/auth/sign-in', methods=["POST"])
def sign_in():
    try:
        # Grabbing the form data/body of req
        sign_in_form_data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Checking if the user does exist in the db
        cursor.execute("SELECT * FROM users WHERE username = %s;", (sign_in_form_data["username"],))
        existing_user = cursor.fetchone()

        # If no existing user, return appropriate message
        if existing_user is None:
            return jsonify({"err": "Invalid credentials."}), 401
        
        # Else, check the password against the hashed version of the password
        password_is_valid = bcrypt.checkpw(bytes(sign_in_form_data["password"], 'utf-8'), bytes(existing_user["password"], 'utf-8'))
        
        if not password_is_valid:
            return jsonify({"err": "Invalid credentials."}), 401
        
        # Construct the payload
        payload = {"username": existing_user["username"], "id": existing_user["id"]}

        # Create the token, attaching the payload
        token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))

        # Send the token instead of the user
        return jsonify({"token": token}), 200
    
    except Exception as err:
        return jsonify({"err": "Invalid credentials."}), 401
    
    finally:
        connection.close()