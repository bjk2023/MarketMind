# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas

import yfinance as yf
from flask import Flask, jsonify
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
        print(f"Fetching stock data for {ticker}...")
        stock = yf.Ticker(ticker)
        info = stock.info

        # A more robust check for a valid ticker.
        # 'regularMarketPrice' is a good indicator of a valid, publicly traded stock.
        if info.get('regularMarketPrice') is None:
            print(f"Error: No data found for ticker {ticker}. It may be invalid.")
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
            "peRatio": info.get('trailingPE') or "N/A",  # Use 'or' for a clean fallback
            "week52High": info.get('fiftyTwoWeekHigh', 0),
            "week52Low": info.get('fiftyTwoWeekLow', 0),
        }
        print(f"Successfully fetched stock data for {ticker}.")
        return jsonify(formatted_data)

    except Exception as e:
        print(f"An exception occurred while fetching stock data for {ticker}: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    """
    This function gets historical data for the chart using yfinance.
    """
    try:
        print(f"Fetching chart data for {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="100d", interval="1d")

        if hist.empty:
            print(f"Error: No historical data found for {ticker}.")
            return jsonify({"error": "Could not retrieve time series data."}), 404

        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d'),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })

        print(f"Successfully fetched chart data for {ticker}.")
        return jsonify(chart_data)

    except Exception as e:
        print(f"An exception occurred while fetching chart data for {ticker}: {e}")
        return jsonify({"error": f"An error occurred while fetching chart data: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)