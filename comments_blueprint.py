from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection
import psycopg2.extras
from auth_middleware import token_required

comments_blueprint = Blueprint('comments_blueprint', __name__)

# Create a comment - POST /reports/<report_id>/comments
@comments_blueprint.route('/reports/<report_id>/comments', methods=['POST'])
@token_required
def create_comment(report_id):
    try:
        new_comment_data = request.get_json()
        new_comment_data["author"] = g.user["id"]

        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
                        INSERT INTO comments (report, author, text)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                       (report_id, new_comment_data['author'],
                        new_comment_data['text'])
                       )
        comment_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT c.id, 
                            c.author AS comment_author_id, 
                            c.text AS comment_text, 
                            u_comment.username AS comment_author_username
                        FROM comments c
                        JOIN users u_comment ON c.author = u_comment.id
                        WHERE c.id = %s
                       """, (comment_id,))
        created_comment = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(created_comment), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500



