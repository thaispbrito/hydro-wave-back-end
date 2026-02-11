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

# Read a single report - GET /reports/<report_id>
@reports_blueprint.route('/reports/<report_id>', methods=['GET'])
def show_report(report_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT r.id, r.author AS report_author_id, r.title, r.reported_at, r.water_source, r.water_feature, r.location_lat, r.location_long, r.observation, r.condition, r.status, r.image_url, u_report.username AS author_username, c.id AS comment_id, c.text AS comment_text, u_comment.username AS comment_author_username
            FROM reports r
            INNER JOIN users u_report ON r.author = u_report.id
            LEFT JOIN comments c ON r.id = c.report
            LEFT JOIN users u_comment ON c.author = u_comment.id
            WHERE r.id = %s;""",
                       (report_id,))
        unprocessed_report = cursor.fetchall()
        if unprocessed_report is not None:
            processed_report = consolidate_comments_in_reports(unprocessed_report)[0]
            connection.close()
            return jsonify(processed_report), 200
        else:
            connection.close()
            return jsonify({"error": "Report not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
# Update a report - PUT /reports/<report_id>
@reports_blueprint.route('/reports/<report_id>', methods=['PUT'])
@token_required
def update_report(report_id):
    try:
        updated_report_data = request.json
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM reports WHERE reports.id = %s", (report_id,))
        report_to_update = cursor.fetchone()
        if report_to_update is None:
            return jsonify({"error": "Report not found"}), 404
        connection.commit()
        if report_to_update["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("UPDATE reports SET title = %s, reported_at = %s, water_source = %s, water_feature = %s, location_lat = %s, location_long = %s, observation = %s, condition = %s, status = %s, image_url = %s WHERE reports.id = %s RETURNING *",
                       (updated_report_data["title"], updated_report_data["reported_at"], updated_report_data["water_source"], updated_report_data["water_feature"], updated_report_data["location_lat"], updated_report_data["location_long"], updated_report_data["observation"], updated_report_data["condition"], updated_report_data["status"], updated_report_data["image_url"], report_id))
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
        updated_report = cursor.fetchone()
        connection.commit()
        connection.close()
        return jsonify(updated_report), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
# Delete a report - DELETE /reports/<report_id>
@reports_blueprint.route('/reports/<report_id>', methods=['DELETE'])
@token_required
def delete_report(report_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM reports WHERE reports.id = %s", (report_id,))
        report_to_delete = cursor.fetchone()
        if report_to_delete is None:
            return jsonify({"error": "Report not found"}), 404
        connection.commit()
        if report_to_delete["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401
        cursor.execute("DELETE FROM reports WHERE reports.id = %s", (report_id,))
        connection.commit()
        connection.close()
        return jsonify(report_to_delete), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500    