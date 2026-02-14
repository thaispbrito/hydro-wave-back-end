from flask import Blueprint, request, jsonify, g
from auth_middleware import token_required
from google import genai
from google.genai import types
from db_helpers import get_db_connection
import psycopg2.extras
import os

from dotenv import load_dotenv
load_dotenv()

ai_blueprint = Blueprint("ai_blueprint", __name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Explicitly pass API key

@ai_blueprint.route("/ai/<report_id>", methods=["GET"])
@token_required
def generate_insight_for_report(report_id):        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Fetch the report from the DB
            cursor.execute("SELECT observation, condition, water_source, location_name author FROM reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()
            connection.close()

            if not report:
                return jsonify({"error": "Report not found"}), 404

            # Only allow the author to get AI insight
            if report["author"] != g.user["id"]:
                return jsonify({"error": "Unauthorized"}), 401

            prompt = (
                f"User submitted a water report with the following details:\n"
                f"- Observation: {report['observation']}\n"
                f"- Condition: {report['condition']}\n"
                f"- Water source: {report['water_source']}\n"
                f"- Location: {report['location_name']}\n\n"
                "Provide a short, plain-text suggestion or next step for the user."
                "Use google search to find environmental agencies names based on the report location, water source, condition, and observation. "
                "If you find any relevant agencies, include their names in the suggestion. If you don't find any relevant agencies, provide a general suggestion based on the report details."
                "Keep it concise (1-2 sentences), actionable, and do NOT use bullet points or markdown."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    tools=types.ToolsConfig(google_search=types.GoogleSearch())
                )
            )

            return jsonify({"insight": response.text.strip()}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


