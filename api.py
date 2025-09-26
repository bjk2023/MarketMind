# To run this file, you need to install Flask and Flask-CORS:
# pip install Flask Flask-CORS

from flask import Flask, jsonify
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow
# your React front end to make requests to this server.
CORS(app)

# --- Mock Stock Data ---
# In a real application, this data would come from a database
# or a live financial data service (like Alpha Vantage, IEX Cloud, etc.)
mock_stock_data = {
    "AAPL": {
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "price": 172.50,
        "change": 2.75,
        "changePercent": 1.62,
        "marketCap": "2.81T",
        "peRatio": 28.5,
        "week52High": 198.23,
        "week52Low": 148.96,
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "companyName": "Alphabet Inc.",
        "price": 135.99,
        "change": -1.50,
        "changePercent": -1.09,
        "marketCap": "1.72T",
        "peRatio": 25.8,
        "week52High": 142.15,
        "week52Low": 101.36,
    },
    "TSLA": {
        "symbol": "TSLA",
        "companyName": "Tesla, Inc.",
        "price": 254.50,
        "change": 5.10,
        "changePercent": 2.04,
        "marketCap": "808.5B",
        "peRatio": 78.3,
        "week52High": 299.29,
        "week52Low": 152.37,
    }
}

# Define an API endpoint to get stock data
@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker.
    It looks up the ticker in our mock data and returns it as JSON.
    """
    # Convert ticker to uppercase to match our data keys
    formatted_ticker = ticker.upper()
    data = mock_stock_data.get(formatted_ticker)

    if data:
        # If data is found, return it with a 200 OK status
        return jsonify(data)
    else:
        # If data is not found, return an error with a 404 Not Found status
        return jsonify({"error": "Ticker not found"}), 404

# This block allows you to run the server directly from the command line
if __name__ == '__main__':
    # Runs the Flask app on localhost, port 5001, with debug mode on.
    # Debug mode provides helpful error messages and auto-reloads the server on changes.
    app.run(debug=True, port=5001)
