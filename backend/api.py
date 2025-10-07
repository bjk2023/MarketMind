# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
CORS(app)


@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker using yfinance.
    It fetches company info and formats it for the frontend data card.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if info.get('regularMarketPrice') is None:
            return jsonify({"error": f"Invalid ticker symbol '{ticker}' or no data available."}), 404

        price = info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', price)
        change = price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0

        market_cap_int = info.get('marketCap', 0)
        if market_cap_int >= 1_000_000_000_000:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000_000:.2f}T"
        elif market_cap_int > 0:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000:.2f}B"
        else:
            market_cap_formatted = "N/A"

        formatted_data = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "price": price,
            "change": change,
            "changePercent": change_percent,
            "marketCap": market_cap_formatted,
            "peRatio": info.get('trailingPE') or "N/A",
            "week52High": info.get('fiftyTwoWeekHigh', 0),
            "week52Low": info.get('fiftyTwoWeekLow', 0),
        }
        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    """
    This function gets historical data for the chart using yfinance.
    It now accepts a 'period' query parameter to fetch different time frames.
    """
    # Get the period from the request arguments, default to '6mo'
    period = request.args.get('period', '6mo')

    # Define valid yfinance periods and their corresponding intervals
    # Shorter periods need smaller intervals to show detail
    period_interval_map = {
        "1d": {"period": "1d", "interval": "5m"},
        "5d": {"period": "5d", "interval": "15m"},
        "1mo": {"period": "1mo", "interval": "1d"},
        "6mo": {"period": "6mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1d"},
    }

    params = period_interval_map.get(period)
    if not params:
        return jsonify({"error": "Invalid time frame specified."}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=params["period"], interval=params["interval"])

        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data for the selected period."}), 404

        # Format the data into the structure the frontend expects
        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d %H:%M:%S'),  # Include time for intraday data
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })

        return jsonify(chart_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching chart data: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)

