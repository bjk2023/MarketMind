# To run this file, you need to install Flask, Flask-CORS, and requests:
# pip install Flask Flask-CORS requests
import os
import requests
from flask import Flask, jsonify, request # Make sure to import 'request'
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
# Allow POST and DELETE methods for the watchlist
CORS(app, resources={r"/*": {"origins": "*"}})

# Retrieve your Alpha Vantage API key from an environment variable for security
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# --- NEW: In-memory storage for the watchlist ---
# Using a set to automatically prevent duplicate tickers
watchlist = set()

# --- NEW: Endpoint to get the current watchlist ---
@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    """Returns the list of tickers in the watchlist."""
    return jsonify(list(watchlist))

# --- NEW: Endpoint to add a stock to the watchlist ---
@app.route('/watchlist/<string:ticker>', methods=['POST'])
def add_to_watchlist(ticker):
    """Adds a ticker to the watchlist."""
    ticker = ticker.upper()
    watchlist.add(ticker)
    return jsonify({"message": f"{ticker} added to watchlist.", "watchlist": list(watchlist)}), 201

# --- NEW: Endpoint to remove a stock from the watchlist ---
@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    """Removes a ticker from the watchlist."""
    ticker = ticker.upper()
    watchlist.discard(ticker) # Use discard to avoid errors if ticker not found
    return jsonify({"message": f"{ticker} removed from watchlist.", "watchlist": list(watchlist)})


@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker.
    It fetches live data from the Alpha Vantage API for the main data card.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return jsonify({"error": "API key is missing. Please set the ALPHA_VANTAGE_API_KEY environment variable."}), 500

    overview_params = {"function": "OVERVIEW", "symbol": ticker, "apikey": ALPHA_VANTAGE_API_KEY}
    quote_params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": ALPHA_VANTAGE_API_KEY}

    try:
        overview_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=overview_params)
        overview_response.raise_for_status()
        overview_data = overview_response.json()

        quote_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=quote_params)
        quote_response.raise_for_status()
        quote_data = quote_response.json()

        if "Note" in overview_data or "Note" in quote_data:
            return jsonify(
                {"error": "API rate limit reached (5 calls per minute). Please wait a moment and try again."}), 429

        global_quote = quote_data.get("Global Quote", {})
        if not overview_data or not global_quote or not overview_data.get("Symbol"):
            return jsonify({"error": f"Invalid ticker symbol '{ticker}' or no data available."}), 404

        market_cap_str = overview_data.get('MarketCapitalization', "0")
        market_cap_int = int(market_cap_str)

        if market_cap_int >= 1_000_000_000_000:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000_000:.2f}T"
        else:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000:.2f}B"

        formatted_data = {
            "symbol": overview_data.get("Symbol"),
            "companyName": overview_data.get("Name"),
            "price": float(global_quote.get("05. price", 0)),
            "change": float(global_quote.get("09. change", 0)),
            "changePercent": float(global_quote.get("10. change percent", "0%").replace('%', '')),
            "marketCap": market_cap_formatted,
            "peRatio": float(overview_data.get("PERatio", 0)),
            "week52High": float(overview_data.get("52WeekHigh", 0)),
            "week52Low": float(overview_data.get("52WeekLow", 0)),
        }
        return jsonify(formatted_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {e}"}), 500
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"Error parsing API response: {e}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    """
    This function handles requests for historical chart data.
    It now uses TIME_SERIES_DAILY which is more reliable on the free plan.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return jsonify({"error": "API key is missing. Please set the ALPHA_VANTAGE_API_KEY environment variable."}), 500

    chart_params = {
        # --- THIS IS THE ONLY LINE THAT CHANGED ---
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=chart_params)
        response.raise_for_status()
        data = response.json()

        if "Note" in data:
            return jsonify({"error": "API rate limit reached (5 calls per minute). Please wait and try again."}), 429

        time_series = data.get('Time Series (Daily)')
        if not time_series:
            error_message = data.get("Error Message",
                                     "Could not retrieve time series data. The ticker may be invalid or delisted.")
            return jsonify({"error": error_message}), 404

        chart_data = []
        # NOTE: The keys for raw data are different (e.g., '1. open' vs '1. open')
        # We also need to handle volume key change ('6. volume' to '5. volume')
        for date, values in time_series.items():
            chart_data.append({
                "date": date,
                "open": float(values.get('1. open', 0)),
                "high": float(values.get('2. high', 0)),
                "low": float(values.get('3. low', 0)),
                "close": float(values.get('4. close', 0)),
                "volume": int(values.get('5. volume', 0))  # <-- Volume key is different
            })

        chart_data.reverse()
        return jsonify(chart_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {e}"}), 500
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Error parsing chart API response: {e}"}), 500


if __name__ == '__main__':
    # Using port 5001 to avoid conflicts with other common ports
    app.run(debug=True, port=5001)