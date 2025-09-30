# To run this file, you need to install Flask, Flask-CORS, and requests:
# pip install Flask Flask-CORS requests
import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow
# your React front end to make requests to this server.
CORS(app)

# Retrieve your Alpha Vantage API key from an environment variable for security
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


# Define an API endpoint to get stock data
@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker.
    It fetches live data from the Alpha Vantage API and formats it
    for the frontend.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return jsonify({"error": "API key not configured."}), 500

    # --- Fetching Live Data ---
    # We will use two Alpha Vantage functions:
    # 1. OVERVIEW: To get company name, market cap, P/E ratio, etc.
    # 2. GLOBAL_QUOTE: To get the latest price, change, and percent change.

    # Parameters for the Company Overview API call
    overview_params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    # Parameters for the Global Quote API call
    quote_params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        # Make the API requests
        overview_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=overview_params)
        overview_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        overview_data = overview_response.json()

        quote_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=quote_params)
        quote_response.raise_for_status()
        quote_data = quote_response.json().get("Global Quote", {})

        # --- Data Validation and Formatting ---
        # Check if the API returned valid data. An empty response means the ticker is likely invalid.
        if not overview_data or not quote_data or not overview_data.get("Symbol"):
            return jsonify({"error": "Invalid ticker symbol or no data available"}), 404

        # Check for API rate limiting message
        if "Note" in overview_data or "Note" in quote_data:
            return jsonify({"error": "API rate limit reached. Please wait a minute and try again."}), 429

        # Combine the data from both API calls into the structure our frontend expects
        formatted_data = {
            "symbol": overview_data.get("Symbol"),
            "companyName": overview_data.get("Name"),
            "price": float(quote_data.get("05. price", 0)),
            "change": float(quote_data.get("09. change", 0)),
            "changePercent": float(quote_data.get("10. change percent", "0%").replace('%', '')),
            "marketCap": f"{int(overview_data.get('MarketCapitalization', 0)) / 1_000_000_000_000:.2f}T" if int(
                overview_data.get('MarketCapitalization',
                                  0)) > 1_000_000_000_000 else f"{int(overview_data.get('MarketCapitalization', 0)) / 1_000_000_000:.2f}B",
            "peRatio": float(overview_data.get("PERatio", 0)),
            "week52High": float(overview_data.get("52WeekHigh", 0)),
            "week52Low": float(overview_data.get("52WeekLow", 0)),
        }

        return jsonify(formatted_data)

    except requests.exceptions.RequestException as e:
        # Handle network errors
        return jsonify({"error": f"Network error: {e}"}), 500
    except (KeyError, ValueError) as e:
        # Handle issues with parsing the API response (e.g., unexpected format)
        return jsonify({"error": f"Error parsing API response: {e}"}), 500


# This block allows you to run the server directly from the command line
if __name__ == '__main__':
    # Runs the Flask app on localhost, port 5001, with debug mode on.
    app.run(debug=True, port=5001)
