# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- In-memory storage for the watchlist ---
watchlist = set()

# --- In-memory storage for Paper Trading ---
paper_portfolio = {
    "cash": 100000.0,
    "positions": {}  # {ticker: {"shares": 0, "avg_cost": 0}}
}


# --- Watchlist Endpoints ---
@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    return jsonify(list(watchlist))


@app.route('/watchlist/<string:ticker>', methods=['POST'])
def add_to_watchlist(ticker):
    ticker = ticker.upper()
    watchlist.add(ticker)
    return jsonify({"message": f"{ticker} added to watchlist.", "watchlist": list(watchlist)}), 201


@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    ticker = ticker.upper()
    watchlist.discard(ticker)
    return jsonify({"message": f"{ticker} removed from watchlist.", "watchlist": list(watchlist)})


# --- Stock Data Endpoints ---
@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
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

        return jsonify({
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "price": price, "change": change, "changePercent": change_percent,
            "marketCap": market_cap_formatted, "peRatio": info.get('trailingPE') or "N/A",
            "week52High": info.get('fiftyTwoWeekHigh', 0), "week52Low": info.get('fiftyTwoWeekLow', 0),
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    period = request.args.get('period', '6mo')
    period_interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d"}
    interval = period_interval_map.get(period)
    if not interval:
        return jsonify({"error": "Invalid time frame specified."}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data."}), 404

        return jsonify([
            {"date": index.strftime('%Y-%m-%d %H:%M:%S'), "open": row['Open'], "high": row['High'], "low": row['Low'],
             "close": row['Close'], "volume": row['Volume']}
            for index, row in hist.iterrows()
        ])
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# --- Paper Trading Endpoints ---
@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    """Return the current state of the paper trading portfolio with calculated metrics."""
    total_positions_value = 0
    total_daily_pl = 0
    total_cost_basis = 0
    positions_data = []

    tickers_to_fetch = list(paper_portfolio["positions"].keys())
    if tickers_to_fetch:
        # Fetch data for all tickers at once for efficiency
        data = yf.download(tickers_to_fetch, period="2d")

        for ticker, pos in paper_portfolio["positions"].items():
            try:
                # Handle single vs multiple ticker download format
                if len(tickers_to_fetch) > 1:
                    price = data['Close'][ticker].iloc[-1]
                    prev_close = data['Close'][ticker].iloc[-2]
                else:
                    price = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2]

                info = yf.Ticker(ticker).info
                company_name = info.get('longName', ticker)
            except (KeyError, IndexError):
                price = pos["avg_cost"]  # Fallback if live data fails
                prev_close = price
                company_name = ticker

            current_value = pos["shares"] * price
            cost_basis = pos["shares"] * pos["avg_cost"]
            daily_pl = pos["shares"] * (price - prev_close)
            total_pl = current_value - cost_basis

            total_positions_value += current_value
            total_daily_pl += daily_pl
            total_cost_basis += cost_basis

            positions_data.append({
                "ticker": ticker, "companyName": company_name,
                "shares": pos["shares"], "avg_cost": pos["avg_cost"],
                "current_price": price, "current_value": current_value,
                "daily_pl": daily_pl, "total_pl": total_pl
            })

    account_value = paper_portfolio["cash"] + total_positions_value
    total_gain_loss = account_value - 100000.0  # Assuming 100k starting balance

    return jsonify({
        "cash": paper_portfolio["cash"],
        "account_value": account_value,
        "total_gain_loss": total_gain_loss,
        "daily_gain_loss": total_daily_pl,
        "positions": positions_data
    })


@app.route('/paper/buy', methods=['POST'])
def buy_stock():
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if shares <= 0: return jsonify({"error": "Shares must be positive"}), 400

    price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
    if price is None: return jsonify({"error": f"Invalid ticker: {ticker}"}), 404

    total_cost = shares * price
    if total_cost > paper_portfolio["cash"]: return jsonify({"error": "Insufficient cash"}), 400

    pos = paper_portfolio["positions"].get(ticker, {"shares": 0, "avg_cost": 0})
    new_total_shares = pos["shares"] + shares
    new_avg_cost = ((pos["avg_cost"] * pos["shares"]) + total_cost) / new_total_shares

    paper_portfolio["positions"][ticker] = {"shares": new_total_shares, "avg_cost": new_avg_cost}
    paper_portfolio["cash"] -= total_cost

    return jsonify({"message": f"Bought {shares} {ticker} at ${price:.2f}"}), 200


@app.route('/paper/sell', methods=['POST'])
def sell_stock():
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if shares <= 0: return jsonify({"error": "Shares must be positive"}), 400

    pos = paper_portfolio["positions"].get(ticker)
    if not pos or pos["shares"] < shares: return jsonify({"error": "Not enough shares"}), 400

    price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
    proceeds = shares * price

    pos["shares"] -= shares
    if pos["shares"] == 0: del paper_portfolio["positions"][ticker]
    paper_portfolio["cash"] += proceeds

    return jsonify({"message": f"Sold {shares} {ticker} at ${price:.2f}"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)

