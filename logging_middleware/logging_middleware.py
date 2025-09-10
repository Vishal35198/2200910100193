import datetime
import requests
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Replace with your actual log API endpoint
LOG_API_URL = "http://20.244.56.144/evaluation-service/logs"

# Add your authorization token for the logging API here
# You should get this token from your log API provider
LOG_API_TOKEN = "YOUR_API_KEY_HERE"

def log_to_api(stack, level, package, message):
    """
    Sends log data to a specified external API endpoint.
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
        "Authorization": f"Bearer {LOG_API_TOKEN}" # Added authorization header
    }
    try:
        response = requests.post(LOG_API_URL, json=log_payload, headers=headers)
        if response.status_code != 200:
            print(f"Failed to log to API: {response.status_code} - {response.text}")
        else:
            print("Successfully logged to API.")
    except requests.exceptions.RequestException as e:
        print(f"Logging failed due to network error: {e}")