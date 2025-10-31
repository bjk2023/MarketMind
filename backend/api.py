# To run this file, you need to install Flask, Flask-CORS, yfinance, pandas, scikit-learn, numpy, and requests
# pip install Flask Flask-CORS yfinance pandas scikit-learn numpy requests

import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import sqlite3
import requests  # <-- NEW IMPORT

# --- Initialize the Flask application ---
app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# !!! IMPORTANT: Paste your new API key here !!!
# (For a real app, use environment variables, but this is fine for local)
NEWS_API_KEY = "4f2abfc0913748ee9cedf3b5e5878bcc"

# --- Database Setup ---
DATABASE = 'marketmind.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                portfolio_value REAL NOT NULL
            );
        ''')
        cursor.execute("SELECT COUNT(id) FROM portfolio_history")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO portfolio_history (timestamp, portfolio_value) VALUES (?, ?)",
                           (datetime.now(), 100000.0))
        conn.commit()
        print("Database initialized.")
    except Exception as e:
        print(f"An error occurred during DB initialization: {e}")
    finally:
        if conn:
            conn.close()

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
        market_cap_formatted = "N/A"
        if market_cap_int >= 1_000_000_000_000:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000_000:.2f}T"
        elif market_cap_int > 0:
            market_cap_formatted = f"{market_cap_int / 1_000_000_000:.2f}B"
        
        formatted_data = {
            "symbol": info.get('symbol', ticker.upper()), "companyName": info.get('longName', 'N/A'),
            "price": price, "change": change, "changePercent": change_percent, "marketCap": market_cap_formatted,
            "peRatio": info.get('trailingPE') or "N/A", "week52High": info.get('fiftyTwoWeekHigh', 0),
            "week52Low": info.get('fiftyTwoWeekLow', 0),
        }
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    period = request.args.get('period', '6mo')
    period_interval_map = {
        "1d": {"period": "1d", "interval": "5m"}, "5d": {"period": "5d", "interval": "15m"},
        "1mo": {"period": "1mo", "interval": "1d"}, "6mo": {"period": "6mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1d"},
    }
    params = period_interval_map.get(period)
    if not params:
        return jsonify({"error": "Invalid time frame specified."}), 400
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=params["period"], interval=params["interval"])
        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data."}), 404
        chart_data = [{"date": index.strftime('%Y-%m-%d %H:%M:%S'), "open": row['Open'], "high": row['High'], "low": row['Low'], "close": row['Close'], "volume": row['Volume']} for index, row in hist.iterrows()]
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- NEW: News Endpoint (Using NewsAPI.org) ---
@app.route('/news')
def get_stock_news():
    """Fetches news from NewsAPI.org based on a query parameter."""
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "A search query ('q') is required."}), 400
        
    try:
        # Search for the company name, look in title and description
        url = (f"https://newsapi.org/v2/everything?"
               f"q={query}"
               f"&searchIn=title,description"
               f"&language=en"
               f"&pageSize=8"
               f"&sortBy=relevancy"
               f"&apiKey={NEWS_API_KEY}")
               
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') != 'ok':
            return jsonify({"error": data.get('message', 'Failed to fetch news from NewsAPI')}), 500

        formatted_news = []
        for item in data.get('articles', []):
            formatted_news.append({
                'title': item.get('title'),
                'publisher': item.get('source', {}).get('name', 'N/A'),
                'link': item.get('url'),
                'publishTime': item.get('publishedAt', 'N/A'),
                'thumbnail_url': item.get('urlToImage') # This is the key field!
            })
                
        return jsonify(formatted_news)
    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching news: {str(e)}"}), 500

# --- Prediction Endpoint ---
@app.route('/predict/<string:ticker>')
def predict_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y") 
        if hist.empty or len(hist) < 10: 
            return jsonify({"error": "Not enough historical data to predict."}), 404

        hist = hist.reset_index()
        hist['Date'] = pd.to_datetime(hist['Date'].dt.date)
        hist['Date_ordinal'] = hist['Date'].apply(lambda x: x.toordinal())
        X = np.array(hist['Date_ordinal']).reshape(-1, 1)
        y = np.array(hist['Close']).reshape(-1, 1)
        
        model = LinearRegression()
        model.fit(X, y)
        
        last_date = hist['Date'].iloc[-1]
        future_date = last_date + timedelta(days=7)
        future_date_ordinal = future_date.toordinal()
        prediction = model.predict(np.array([[future_date_ordinal]]))
        
        return jsonify({
            "ticker": ticker.upper(),
            "prediction_for_date": future_date.strftime('%Y-%m-%d'),
            "predicted_price": prediction[0][0]
        })
    except Exception as e:
        return jsonify({"error": f"Prediction model failed: {str(e)}"}), 500

# --- Portfolio History Helper Function ---
def record_portfolio_snapshot():
    total_value = paper_portfolio['cash']
    for ticker, pos in paper_portfolio['positions'].items():
        try:
            stock = yf.Ticker(ticker)
            price = stock.info.get('regularMarketPrice', pos['avg_cost'])
            total_value += pos['shares'] * price
        except Exception:
            total_value += pos['shares'] * pos['avg_cost']

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO portfolio_history (timestamp, portfolio_value) VALUES (?, ?)",
                       (datetime.now(), total_value))
        conn.commit()
    except Exception as e:
        print(f"Failed to record portfolio snapshot: {e}")
    finally:
        if conn:
            conn.close()

# --- Paper Trading Endpoints ---
@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    data = {"cash": paper_portfolio["cash"], "positions": []}
    for ticker, pos in paper_portfolio["positions"].items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('regularMarketPrice', pos['avg_cost'])
            current_value = pos["shares"] * price
            cost_basis = pos["shares"] * pos["avg_cost"]
            total_pl = current_value - cost_basis
            daily_pl = pos["shares"] * (price - info.get('previousClose', price))
            data["positions"].append({"ticker": ticker, "shares": pos["shares"], "avg_cost": pos["avg_cost"], "current_price": price, "daily_pl": daily_pl, "total_pl": total_pl})
        except Exception:
            data["positions"].append({"ticker": ticker, "shares": pos["shares"], "avg_cost": pos["avg_cost"], "current_price": pos["avg_cost"], "daily_pl": 0, "total_pl": 0})
    return jsonify(data)

@app.route('/paper/buy', methods=['POST'])
def buy_stock():
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if not ticker or shares <= 0:
        return jsonify({"error": "Valid ticker and positive shares required."}), 400
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice')
        if price is None:
            return jsonify({"error": f"Cannot find data for ticker '{ticker}'."}), 404
        total_cost = shares * price
        if total_cost > paper_portfolio["cash"]:
            return jsonify({"error": "Insufficient cash to complete this transaction."}), 400
        pos = paper_portfolio["positions"].get(ticker, {"shares": 0, "avg_cost": 0})
        new_total_shares = pos["shares"] + shares
        new_avg_cost = ((pos["avg_cost"] * pos["shares"]) + total_cost) / new_total_shares
        paper_portfolio["positions"][ticker] = {"shares": new_total_shares, "avg_cost": new_avg_cost}
        paper_portfolio["cash"] -= total_cost
        record_portfolio_snapshot()
        return jsonify({"message": f"Successfully bought {shares} shares of {ticker}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the trade: {str(e)}"}), 500

@app.route('/paper/sell', methods=['POST'])
def sell_stock():
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    shares = int(data.get('shares', 0))
    if not ticker or shares <= 0:
        return jsonify({"error": "Valid ticker and positive shares required."}), 400
    pos = paper_portfolio["positions"].get(ticker)
    if not pos or pos["shares"] < shares:
        return jsonify({"error": f"You do not own enough shares of {ticker} to sell."}), 400
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice')
        if price is None:
            return jsonify({"error": f"Cannot find current price for {ticker}."}), 404
        proceeds = shares * price
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del paper_portfolio["positions"][ticker]
        paper_portfolio["cash"] += proceeds
        record_portfolio_snapshot()
        return jsonify({"message": f"Successfully sold {shares} shares of {ticker}."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the trade: {str(e)}"}), 500

# --- Portfolio History Endpoints ---
@app.route('/paper/history', methods=['GET'])
def get_portfolio_history():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, portfolio_value FROM portfolio_history ORDER BY timestamp ASC")
        history = cursor.fetchall()
        history_data = [{"date": row[0], "value": row[1]} for row in history]
        return jsonify(history_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/paper/summary', methods=['GET'])
def get_portfolio_summary():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT portfolio_value FROM portfolio_history ORDER BY timestamp ASC LIMIT 1")
        start_value_row = cursor.fetchone()
        if not start_value_row:
             return jsonify({"error": "No portfolio history found."}), 404
        start_value = start_value_row[0]

        cursor.execute("SELECT portfolio_value, timestamp FROM portfolio_history ORDER BY timestamp DESC LIMIT 1")
        end_record = cursor.fetchone()
        if not end_record:
            return jsonify({"error": "No portfolio history found."}), 404
            
        end_value = end_record[0]
        wealth_generated = end_value - start_value
        cumulative_return_pct = (wealth_generated / start_value) * 100 if start_value != 0 else 0
        
        cursor.execute("SELECT timestamp FROM portfolio_history ORDER BY timestamp ASC LIMIT 1")
        start_date_str = cursor.fetchone()[0]
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')

        try:
            end_date = datetime.strptime(end_record[1], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            end_date = datetime.strptime(end_record[1], '%Y-%m-%d %H:%M:%S')

        years_held = (end_date - start_date).days / 365.25
        annualized_return_pct = 0
        if years_held > 0 and cumulative_return_pct > -100:
            annualized_return_pct = ((1 + (cumulative_return_pct / 100)) ** (1 / years_held) - 1) * 100
        
        summary = {
            "ending_market_value": end_value,
            "wealth_generated": wealth_generated,
            "cumulative_return_pct": cumulative_return_pct,
            "annualized_return_pct": annualized_return_pct
        }
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# --- Main execution ---
if __name__ == '__main__':
    init_db() # Initialize the database on startup
    app.run(debug=True, port=5001)