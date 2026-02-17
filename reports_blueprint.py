from flask import Blueprint, jsonify, request, g
from db_helpers import get_db_connection, consolidate_comments_in_reports
import psycopg2, psycopg2.extras
from auth_middleware import token_required
from main import upload_image
from datetime import datetime 

reports_blueprint = Blueprint('reports_blueprint', __name__)

# Create a report - POST /reports
@reports_blueprint.route('/reports', methods=['POST'])
@token_required
def create_report():
    try:
        image = request.files.get("image_url")
        # image_url refers to the column name on the hoots table
        # if the user does not upload an image it will default to None
        image_url = None
        # if the user does upload an image, then we update our image_url field to the uploaded image
        if image:
            image_url = upload_image(image)

        # set the author_id to be the id of the currently logged in user
        author_id = g.user["id"]

        # specify the rest of the fields in our table and grab that information
        title = request.form.get("title")
        reported_at = request.form.get("reported_at")
        water_source = request.form.get("water_source")
        water_feature = request.form.get("water_feature")
        location_lat = request.form.get("location_lat")
        location_long = request.form.get("location_long")
        location_name = request.form.get("location_name")
        observation = request.form.get("observation")
        condition = request.form.get("condition")
        status = request.form.get("status")

        # connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)

        # insert all the form data into the database
        cursor.execute("""
                        INSERT INTO reports (author, title, reported_at, water_source, water_feature, location_lat, location_long, location_name, observation, condition, status, created_at, updated_at, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                       (author_id, title, reported_at, water_source, water_feature, location_lat, location_long, location_name, observation, condition, status, datetime.utcnow(), datetime.utcnow(), image_url)
                       )
        report_id = cursor.fetchone()["id"]

        # Join the user table and the hoots table
        # Show the newly created information along with the user information
        cursor.execute("""SELECT r.id, 
                            r.author AS report_author_id, 
                            r.title, 
                            r.reported_at, 
                            r.water_source, 
                            r.water_feature,
                            r.location_lat,
                            r.location_long,
                            r.location_name,
                            r.observation,
                            r.condition,
                            r.status,
                            r.created_at,
                            r.updated_at,
                            r.image_url,
                            u_report.username AS author_username
                        FROM reports r
                        JOIN users u_report ON r.author = u_report.id
                        WHERE r.id = %s
                       """, (report_id,))
        created_report = cursor.fetchone()
        connection.commit()
        connection.close()

        # Return the newly created information
        return jsonify(created_report), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    
# Read reports - GET /reports
@reports_blueprint.route('/reports', methods=['GET'])
def reports_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""SELECT r.id, r.author AS report_author_id, r.title, r.reported_at, r.water_source, r.water_feature, r.location_lat, r.location_long, r.location_name, r.observation, r.condition, r.status, r.created_at, r.updated_at, r.image_url, u_report.username AS author_username, c.id AS comment_id, c.text AS comment_text, c.created_at AS comment_created_at, c.updated_at AS comment_updated_at, u_comment.username AS comment_author_username
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
            SELECT r.id, r.author AS report_author_id, r.title, r.reported_at, r.water_source, r.water_feature, r.location_lat, r.location_long, r.location_name, r.observation, r.condition, r.status, r.created_at, r.updated_at, r.image_url, u_report.username AS author_username, c.id AS comment_id, c.text AS comment_text, c.created_at AS comment_created_at, c.updated_at AS comment_updated_at, u_comment.username AS comment_author_username
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
        image = request.files.get("image_url")
        # image_url refers to the column name on the hoots table
        # if the user does not upload an image it will default to None
        image_url = None
        # if the user does upload an image, then we update our image_url field to the uploaded image
        if image:
            image_url = upload_image(image)

        # Check for image removal signal from frontend
        remove_image = request.form.get("remove_image")
            
        # specify the rest of the fields in our table and grab that information
        title = request.form.get("title")
        reported_at = request.form.get("reported_at")
        water_source = request.form.get("water_source")
        water_feature = request.form.get("water_feature")
        location_lat = request.form.get("location_lat")
        location_long = request.form.get("location_long")
        location_name = request.form.get("location_name")
        observation = request.form.get("observation")
        condition = request.form.get("condition")
        status = request.form.get("status")
        
        # connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM reports WHERE reports.id = %s", (report_id,))
        report_to_update = cursor.fetchone()
        if report_to_update is None:
            return jsonify({"error": "Report not found"}), 404
        connection.commit()
        if report_to_update["author"] is not g.user["id"]:
            return jsonify({"error": "Unauthorized"}), 401

        # Decide final image_url value
        if remove_image == "true":
            final_image_url = None
        elif image_url:
            final_image_url = image_url
        else:
            final_image_url = report_to_update.get("image_url")

         # update all the form data in the database
        cursor.execute("UPDATE reports SET title = %s, reported_at = %s, water_source = %s, water_feature = %s, location_lat = %s, location_long = %s, location_name = %s, observation = %s, condition = %s, status = %s, updated_at = %s, image_url = %s WHERE reports.id = %s RETURNING *",
                       (title, reported_at, water_source, water_feature, location_lat, location_long, location_name, observation, condition, status, datetime.utcnow(), final_image_url, report_id))
        report_id = cursor.fetchone()["id"]

        # Join the user table and the hoots table
        # Show the newly created information along with the user information
        cursor.execute("""SELECT r.id, 
                            r.author AS report_author_id, 
                            r.title, 
                            r.reported_at, 
                            r.water_source, 
                            r.water_feature,
                            r.location_lat,
                            r.location_long,
                            r.location_name,
                            r.observation,
                            r.condition,
                            r.status,
                            r.created_at,
                            r.updated_at,
                            r.image_url,
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