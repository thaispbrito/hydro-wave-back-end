from flask import Blueprint, request, jsonify
import requests

geocoding_blueprint = Blueprint("geocoding_blueprint", __name__)

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "HydroWave/1.0 (hydro-wave-app)"  # Required by Nominatim

@geocoding_blueprint.route("/geocode/reverse", methods=["GET"])
def reverse_geocode():
    """
    Proxy endpoint for Nominatim reverse geocoding.
    Converts lat/lng coordinates to a human-readable address.
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if not lat or not lng:
        return jsonify({"error": "lat and lng parameters are required"}), 400

    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/reverse",
            params={
                "format": "json",
                "lat": lat,
                "lon": lng
            },
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({"error": "Geocoding service unavailable"}), response.status_code

        return jsonify(response.json()), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Geocoding request timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@geocoding_blueprint.route("/geocode/search", methods=["GET"])
def forward_geocode():
    """
    Proxy endpoint for Nominatim forward geocoding.
    Converts an address/place name to lat/lng coordinates.
    """
    query = request.args.get("q")

    if not query:
        return jsonify({"error": "q (query) parameter is required"}), 400

    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params={
                "format": "json",
                "q": query,
                "limit": 5
            },
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({"error": "Geocoding service unavailable"}), response.status_code

        return jsonify(response.json()), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Geocoding request timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500