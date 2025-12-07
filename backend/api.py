from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# Import your LSTM model prediction function
# (You confirmed the name is predict_next_day_price)
from model import predict_next_day_price

app = Flask(__name__)
CORS(app)


# -----------------------------
# Helpers
# -----------------------------

def clean_value(val):
    """Convert numpy values into pure Python floats."""
    try:
        return float(val)
    except:
        return val


# -----------------------------
# Linear Regression Endpoint
# -----------------------------

@app.route('/predict/lr/<string:ticker>')
def predict_stock_lr(ticker):
    """
    Predicts a stock price 7 days into the future using Linear Regression.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty or len(hist) < 10:
            return jsonify({"error": "Not enough historical data to predict."}), 404

        hist = hist.reset_index()
        hist["Date"] = pd.to_datetime(hist["Date"].dt.date)
        hist["Date_ordinal"] = hist["Date"].apply(lambda x: x.toordinal())

        X = np.array(hist["Date_ordinal"]).reshape(-1, 1)
        y = np.array(hist["Close"]).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)

        last_date = hist["Date"].iloc[-1]
        future_date = last_date + timedelta(days=7)
        future_date_ordinal = future_date.toordinal()

        prediction = model.predict(np.array([[future_date_ordinal]]))

        return jsonify({
            "ticker": ticker.upper(),
            "model": "Linear Regression",
            "prediction_for_date": future_date.strftime('%Y-%m-%d'),
            "predicted_price": clean_value(prediction[0][0])
        })

    except Exception as e:
        return jsonify({"error": f"Linear Regression model failed: {str(e)}"}), 500


# -----------------------------
# LSTM / GRU Endpoint
# -----------------------------

@app.route('/predict/lstm/<string:ticker>', methods=['GET'])
def predict_stock_lstm(ticker):
    """
    Predicts the next day's stock price using the LSTM/GRU model.
    """
    try:
        ticker = ticker.upper()

        # Call your LSTM model
        prediction = predict_next_day_price(ticker)

        # Fetch recent close to compare
        data = yf.download(ticker, period="1mo")["Close"].values
        if len(data) == 0:
            return jsonify({"error": f"No recent data found for '{ticker}'"}), 404

        last_close = float(data[-1])

        return jsonify({
            "ticker": ticker,
            "model": "LSTM",
            "last_close": last_close,
            "predicted_next_close": prediction,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Stock Price Endpoint
# -----------------------------

@app.route('/stock/<string:ticker>', methods=['GET'])
def get_stock_price(ticker):
    """
    Fetches comprehensive stock data including price, company info, and metrics.
    """
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        
        # Get historical data
        hist = stock.history(period="1y")
        if hist.empty:
            return jsonify({"error": f"No data found for '{ticker}'"}), 404
        
        # Get current price
        current_price = float(hist["Close"].iloc[-1])
        
        # Calculate price change
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        price_change = current_price - prev_close
        change_percent = (price_change / prev_close * 100) if prev_close != 0 else 0
        
        # Get 52-week high and low
        week_52_high = float(hist["High"].max())
        week_52_low = float(hist["Low"].min())
        
        # Get info
        info = stock.info or {}
        market_cap = info.get('marketCap', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        company_name = info.get('longName', ticker)
        
        return jsonify({
            "ticker": ticker,
            "companyName": company_name,
            "latest_close_price": current_price,
            "price": current_price,
            "change": price_change,
            "change_percent": change_percent,
            "marketCap": market_cap,
            "peRatio": pe_ratio,
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "prevClose": prev_close
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Chart Data Endpoint
# -----------------------------

@app.route('/chart/<string:ticker>', methods=['GET'])
def get_chart_data(ticker):
    """
    Fetches historical chart data for a given period.
    """
    from flask import request
    try:
        period = request.args.get('period', '1mo')  # Default to 1 month
        ticker = ticker.upper()
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({"error": f"No data found for '{ticker}'"}), 404
        
        hist = hist.reset_index()
        hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        
        chart_data = {
            'dates': hist['Date'].tolist(),
            'prices': hist['Close'].tolist(),
            'volumes': hist['Volume'].tolist(),
            'opens': hist['Open'].tolist(),
            'highs': hist['High'].tolist(),
            'lows': hist['Low'].tolist(),
        }
        
        return jsonify(chart_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Prediction Endpoint (Generic)
# -----------------------------

@app.route('/predict/<string:ticker>', methods=['GET'])
def predict_stock(ticker):
    """
    Generic prediction endpoint that returns LSTM prediction.
    """
    try:
        ticker = ticker.upper()
        prediction = predict_next_day_price(ticker)
        
        data = yf.download(ticker, period="1mo")["Close"].values
        if len(data) == 0:
            return jsonify({"error": f"No recent data found for '{ticker}'"}), 404
        
        last_close = float(data[-1])
        
        return jsonify({
            "ticker": ticker,
            "predicted_price": prediction,
            "current_price": last_close,
            "change_percent": ((prediction - last_close) / last_close) * 100
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# News Endpoint
# -----------------------------

@app.route('/news', methods=['GET'])
def get_news():
    """
    Fetches news articles for a given query.
    """
    from flask import request
    query = request.args.get('q', 'stock market')
    
    try:
        # Using yfinance to get news (limited but free)
        ticker = yf.Ticker(query)
        news = ticker.news
        
        if not news:
            return jsonify({"articles": []})
        
        articles = []
        for item in news[:10]:  # Limit to 10 articles
            articles.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'source': item.get('publisher', ''),
                'publishedAt': item.get('providerPublishTime', '')
            })
        
        return jsonify({"articles": articles})
    
    except Exception as e:
        return jsonify({"articles": []})


# -----------------------------
# Watchlist Endpoints
# -----------------------------

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('marketmind.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    """Get all tickers in the watchlist."""
    conn = get_db_connection()
    watchlist = conn.execute('SELECT ticker FROM watchlist').fetchall()
    conn.close()
    return jsonify([row['ticker'] for row in watchlist])


@app.route('/watchlist/<string:ticker>', methods=['POST'])
def add_to_watchlist(ticker):
    """Add a ticker to the watchlist."""
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO watchlist (ticker) VALUES (?)', (ticker.upper(),))
        conn.commit()
        conn.close()
        return jsonify({"message": f"{ticker.upper()} added to watchlist"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Ticker already in watchlist"}), 400


@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist."""
    conn = get_db_connection()
    conn.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker.upper(),))
    conn.commit()
    conn.close()
    return jsonify({"message": f"{ticker.upper()} removed from watchlist"})


# -----------------------------
# Paper Trading Endpoints
# -----------------------------

@app.route('/paper/portfolio', methods=['GET'])
def get_portfolio():
    """Get the paper trading portfolio."""
    conn = get_db_connection()
    portfolio = conn.execute('SELECT * FROM portfolio').fetchall()
    conn.close()
    
    holdings = []
    for row in portfolio:
        holdings.append({
            'id': row['id'],
            'ticker': row['ticker'],
            'shares': row['shares'],
            'purchase_price': row['purchase_price'],
            'purchase_date': row['purchase_date']
        })
    
    return jsonify({"holdings": holdings, "cash": 100000.0})  # Default cash balance


@app.route('/paper/buy', methods=['POST'])
def paper_buy():
    """Execute a paper buy order."""
    from flask import request
    data = request.json
    ticker = data.get('ticker', '').upper()
    shares = float(data.get('shares', 0))
    
    try:
        stock_data = yf.download(ticker, period="1d")["Close"].values
        if len(stock_data) == 0:
            return jsonify({"error": "Invalid ticker"}), 404
        
        price = float(stock_data[-1])
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO portfolio (ticker, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)',
            (ticker, shares, price, datetime.now().strftime('%Y-%m-%d'))
        )
        conn.commit()
        conn.close()
        
        return jsonify({"message": f"Bought {shares} shares of {ticker} at ${price}"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/paper/sell', methods=['POST'])
def paper_sell():
    """Execute a paper sell order."""
    from flask import request
    data = request.json
    ticker = data.get('ticker', '').upper()
    shares = float(data.get('shares', 0))
    
    try:
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM portfolio WHERE ticker = ? AND shares <= ?',
            (ticker, shares)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"message": f"Sold {shares} shares of {ticker}"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
