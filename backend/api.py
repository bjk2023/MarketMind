# To run this file, you need to install Flask, Flask-CORS, yfinance, pandas, scikit-learn, and numpy
# pip install Flask Flask-CORS yfinance pandas scikit-learn numpy

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- In-memory storage ---
watchlist = set()
paper_portfolio = {
    "cash": 100000.0,
    "positions": {}
}


# --- Watchlist Endpoints ---
@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    return jsonify(list(watchlist))


@app.route('/watchlist/<string:ticker>', methods=['POST'])
def add_to_watchlist(ticker):
    ticker = ticker.upper()
    watchlist.add(ticker)
    return jsonify({"message": f"{ticker} added to watchlist."}), 201


@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    ticker = ticker.upper()
    watchlist.discard(ticker)
    return jsonify({"message": f"{ticker} removed from watchlist."})


# --- Stock Data Endpoints ---
@app.route('/stock/<string:ticker>')
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if info.get('regularMarketPrice') is None:
            return jsonify({"error": f"Invalid ticker: '{ticker}'."}), 404

        price = info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', price)
        change = price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0

        market_cap = info.get('marketCap', 0)
        if market_cap >= 1e12:
            market_cap_fmt = f"{market_cap / 1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_fmt = f"{market_cap / 1e9:.2f}B"
        else:
            market_cap_fmt = "N/A"

        return jsonify({
            "symbol": info.get('symbol', ticker.upper()), "companyName": info.get('longName', 'N/A'),
            "price": price, "change": change, "changePercent": change_percent,
            "marketCap": market_cap_fmt, "peRatio": info.get('trailingPE') or "N/A",
            "week52High": info.get('fiftyTwoWeekHigh', 0), "week52Low": info.get('fiftyTwoWeekLow', 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    period = request.args.get('period', '6mo')
    intervals = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d"}
    interval = intervals.get(period)
    if not interval: return jsonify({"error": "Invalid time frame."}), 400

    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if hist.empty: return jsonify({"error": "No time series data."}), 404
        return jsonify([
            {"date": index.strftime('%Y-%m-%d %H:%M:%S'), "open": r['Open'], "high": r['High'], "low": r['Low'],
             "close": r['Close']}
            for index, r in hist.iterrows()
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- NEW: Prediction Endpoint ---
@app.route('/predict/<string:ticker>')
def predict_stock(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="1y")
        if hist.empty or len(hist) < 10:
            return jsonify({"error": "Not enough data to predict."}), 404

        hist = hist.reset_index()
        hist['Date'] = pd.to_datetime(hist['Date'].dt.date)
        hist['Date_ordinal'] = hist['Date'].apply(lambda x: x.toordinal())
        X = np.array(hist['Date_ordinal']).reshape(-1, 1)
        y = np.array(hist['Close']).reshape(-1, 1)

        model = LinearRegression().fit(X, y)

        future_date = hist['Date'].iloc[-1] + timedelta(days=7)
        prediction = model.predict(np.array([[future_date.toordinal()]]))

        return jsonify({
            "ticker": ticker.upper(),
            "prediction_for_date": future_date.strftime('%Y-%m-%d'),
            "predicted_price": prediction[0][0]
        })
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# --- Paper Trading Endpoints ---
@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    # ... (code is unchanged, but kept for completeness)
    total_positions_value = 0
    total_daily_pl = 0
    positions_data = []
    tickers_to_fetch = list(paper_portfolio["positions"].keys())
    if tickers_to_fetch:
        data = yf.download(tickers_to_fetch, period="2d", auto_adjust=True)
        for ticker, pos in paper_portfolio["positions"].items():
            price_val, prev_close_val, company_name = 0, 0, ticker
            try:
                price_series = data['Close'][ticker] if len(tickers_to_fetch) > 1 else data['Close']
                if not price_series.empty:
                    price_val = price_series.iloc[-1]
                    prev_close_val = price_series.iloc[-2] if len(price_series) > 1 else price_val
                company_name = yf.Ticker(ticker).info.get('longName', ticker)
            except (KeyError, IndexError):
                price_val = prev_close_val = pos["avg_cost"]

            price, prev_close = float(price_val), float(prev_close_val)
            current_value = pos["shares"] * price
            daily_pl = pos["shares"] * (price - prev_close)
            total_pl = current_value - (pos["shares"] * pos["avg_cost"])
            total_positions_value += current_value
            total_daily_pl += daily_pl
            positions_data.append({
                "ticker": ticker, "companyName": company_name, "shares": pos["shares"], "avg_cost": pos["avg_cost"],
                "current_price": price, "current_value": current_value, "daily_pl": daily_pl, "total_pl": total_pl
            })
    account_value = paper_portfolio["cash"] + total_positions_value
    total_gain_loss = account_value - 100000.0
    return jsonify({
        "cash": paper_portfolio["cash"], "account_value": account_value,
        "total_gain_loss": total_gain_loss, "daily_gain_loss": total_daily_pl,
        "positions": positions_data
    })


@app.route('/paper/buy', methods=['POST'])
def buy_stock():
    # ... (code is unchanged, but kept for completeness)
    data = request.get_json()
    ticker, shares = data.get('ticker', '').upper(), int(data.get('shares', 0))
    if shares <= 0: return jsonify({"error": "Shares must be positive"}), 400
    try:
        price = float(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1])
    except IndexError:
        return jsonify({"error": f"Invalid ticker: {ticker}"}), 404
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
    # ... (code is unchanged, but kept for completeness)
    data = request.get_json()
    ticker, shares = data.get('ticker', '').upper(), int(data.get('shares', 0))
    if shares <= 0: return jsonify({"error": "Shares must be positive"}), 400
    pos = paper_portfolio["positions"].get(ticker)
    if not pos or pos["shares"] < shares: return jsonify({"error": "Not enough shares"}), 400
    try:
        price = float(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1])
    except IndexError:
        return jsonify({"error": f"Invalid ticker: {ticker}"}), 404
    pos["shares"] -= shares
    if pos["shares"] == 0: del paper_portfolio["positions"][ticker]
    paper_portfolio["cash"] += (shares * price)
    return jsonify({"message": f"Sold {shares} {ticker} at ${price:.2f}"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)

