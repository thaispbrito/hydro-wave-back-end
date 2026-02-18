from functools import wraps
from flask import request, jsonify, g
import jwt
import os

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization_header = request.headers.get('Authorization')

        # Check if there is a header before attempting to decode it
        if authorization_header is None:
            return jsonify({"err": "Unauthorized"}), 401
        try:
            # Remove the 'Bearer' portion of the Auth header string
            token = authorization_header.split(' ')[1]
            # Decode will throw an error if the token is invalid, triggering the except block automatically
            token_data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
            g.user = token_data['payload']

        except Exception as err:
            return jsonify({"err": str(err)}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

