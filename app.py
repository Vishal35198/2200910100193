import logging
from flask import Flask, request, jsonify, send_from_directory, redirect
import requests
import random
import string
from datetime import datetime, timedelta

# --- Configure File-based Logging ---
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)


LOG_API_URL = "http://20.244.56.144/evaluation-service/logs"

LOG_API_TOKEN = "YOUR_API_KEY_HERE"


shortened_urls = {}

# --- Logging Function ---
def log_to_api(stack, level, package, message):
    """
    Sends log data to a specified external API endpoint and logs locally.
    """
    log_payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LOG_API_TOKEN}"
    }
    try:
        response = requests.post(LOG_API_URL, json=log_payload, headers=headers)
        if response.status_code != 200:
            logging.warning(f"Failed to log to API: {response.status_code} - {response.text}")
        else:
            logging.info(f"Successfully logged to API. Message: {message}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Logging failed due to network error: {e}")

# --- Utility Functions ---
def generate_shortcode(length=6):
    """
    Generates a unique, alphanumeric shortcode.
    """
    characters = string.ascii_letters + string.digits
    while True:
        shortcode = ''.join(random.choice(characters) for _ in range(length))
        if shortcode not in shortened_urls:
            return shortcode

# --- API Endpoints ---
@app.route("/")
def serve_login_page():
    """
    Serves the static index.html file for the login page.
    """
    logging.info("Serving login page.")
    return send_from_directory('static', 'index.html')

@app.route("/shorten")
def serve_shorten_page():
    """
    Serves the static shorten.html file for the URL shortener.
    """
    logging.info("Serving URL shortener page.")
    return send_from_directory('static', 'shorten.html')
    
@app.route("/stats")
def serve_stats_page():
    """
    Serves the static stats.html file for URL statistics.
    """
    logging.info("Serving URL statistics page.")
    return send_from_directory('static', 'stats.html')

@app.route("/shorturls", methods=["POST"])
def create_short_url():
    """
    Creates a new shortened URL from a long URL.
    """
    data = request.get_json()


    if 'url' not in data:
        log_to_api("backend", "error", "shorturls", "Missing 'url' field in request body.")
        return jsonify({"error": "Missing 'url' field"}), 400

    long_url = data['url']
    validity_minutes = data.get('validity', 30)
    custom_shortcode = data.get('shortcode')

    if custom_shortcode:

        if not custom_shortcode.isalnum() or custom_shortcode in shortened_urls:
            log_to_api("backend", "error", "shorturls", f"Invalid or duplicate custom shortcode: {custom_shortcode}")
            return jsonify({"error": "Invalid or duplicate custom shortcode"}), 409
        shortcode = custom_shortcode
    else:
        shortcode = generate_shortcode()

    # Calculate expiry time
    expiry_time = datetime.utcnow() + timedelta(minutes=validity_minutes)

    shortened_urls[shortcode] = {
        "long_url": long_url,
        "expiry_timestamp": expiry_time.isoformat() + "Z", # Add 'Z' for UTC
        "creation_timestamp": datetime.utcnow().isoformat() + "Z",
        "clicks": 0,
        "click_data": [] 
    }


    log_to_api("backend", "info", "shorturls", f"New short URL created for {long_url}")

    # Construct the response
    short_link = f"{request.host_url}{shortcode}"
    return jsonify({
        "shortlink": short_link,
        "expiry": shortened_urls[shortcode]["expiry_timestamp"]
    }), 201

@app.route("/login", methods=["POST"])
def login():
    """
    A simulated login route that logs an error if credentials are not provided.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:

        log_to_api("backend", "error", "login", "Failed login attempt: missing username or password")
        return jsonify({"message": "Invalid login credentials"}), 401
    

    username = data['username']
    log_to_api("backend", "info", "login", f"Successful login for user: {username}")
    return jsonify({"message": "Login successful"}), 200


@app.route("/<shortcode>")
def redirect_to_long_url(shortcode):
    """
    Redirects from the short URL to the original long URL and logs click data.
    """
    if shortcode in shortened_urls:
        url_data = shortened_urls[shortcode]
        # Check for expiry
        if datetime.fromisoformat(url_data["expiry_timestamp"][:-1]) < datetime.utcnow():
            log_to_api("backend", "warning", "redirect", f"Expired shortcode accessed: {shortcode}")
            return "This short URL has expired.", 410


        url_data["clicks"] += 1


        click_info = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "referrer": request.referrer if request.referrer else "unknown",
            "geolocation": "mock-geolocation" # You'd need a real GeoIP service for this
        }
        url_data["click_data"].append(click_info)

        log_to_api("backend", "info", "redirect", f"Redirecting {shortcode} to {url_data['long_url']}")
        return redirect(url_data["long_url"])
    else:
        log_to_api("backend", "error", "redirect", f"Shortcode not found: {shortcode}")
        return "Short URL not found.", 404


@app.route("/shorturls/<shortcode>", methods=["GET"])
def get_url_statistics(shortcode):
    """
    Retrieves and returns usage statistics for a specific shortened URL.
    """
    if shortcode not in shortened_urls:
        log_to_api("backend", "error", "stats", f"Attempted to retrieve stats for non-existent shortcode: {shortcode}")
        return jsonify({"error": "Short URL not found"}), 404

    url_data = shortened_urls[shortcode]
    
    # Create the response payload
    stats_payload = {
        "shortcode": shortcode,
        "total_clicks": url_data["clicks"],
        "original_url": url_data["long_url"],
        "creation_date": url_data["creation_timestamp"],
        "expiry_date": url_data["expiry_timestamp"],
        "click_data": url_data["click_data"]
    }

    log_to_api("backend", "info", "stats", f"Successfully retrieved stats for shortcode: {shortcode}")
    return jsonify(stats_payload), 200

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
