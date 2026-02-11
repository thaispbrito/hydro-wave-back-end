from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection, consolidate_comments_in_reports
import psycopg2, psycopg2.extras
from auth_middleware import token_required

reports_blueprint = Blueprint('reports_blueprint', __name__)

# Create a report - POST /reports
@reports_blueprint.route('/reports', methods=['POST'])
@token_required
def create_report():
    try:
        new_report = request.get_json()
        new_report["author"] = g.user["id"]
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
                        INSERT INTO reports (
                            author, title, reported_at, water_source, water_feature, location_lat, 
                            location_long, observation, condition, status, image_url
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                       (
                           new_report['author'], new_report['title'], new_report['reported_at'], new_report['water_source'], 
                           new_report['water_feature'], new_report['location_lat'], new_report['location_long'], 
                           new_report['observation'], new_report['condition'], new_report['status'], new_report['image_url']
                        )
                      )
        report_id = cursor.fetchone()["id"]
        cursor.execute("""SELECT r.id, 
                            r.author AS report_author_id, 
                            r.title, 
                            r.reported_at, 
                            r.water_source,
                            r.water_feature,
                            r.location_lat,
                            r.location_long,
                            r.observation,
                            r.condition,
                            r.status,
                            r.image_url,
                            r.created_at,
                            r.updated_at,
                            u_report.username AS author_username
                        FROM reports r
                        JOIN users u_report ON r.author = u_report.id
                        WHERE r.id = %s
                       """, (report_id,))
        created_report = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(created_report), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
# Read reports - GET /reports
@reports_blueprint.route('/reports', methods=['GET'])
def reports_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""SELECT r.id, r.author AS report_author_id, r.title, r.reported_at, r.water_source, r.water_feature, r.location_lat, r.location_long, r.observation, r.condition, r.status, r.image_url, u_report.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
                            FROM reports r
                            INNER JOIN users u_report ON r.author = u_report.id
                            LEFT JOIN comments c ON r.id = c.report
                            LEFT JOIN users u_comment ON r.author = u_comment.id;
                       """)
        reports = cursor.fetchall()

        consolidated_reports = consolidate_comments_in_reports(reports)

        connection.commit()
        connection.close()
        return jsonify(consolidated_reports), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
