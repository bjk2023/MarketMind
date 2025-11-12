import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3

# --- Tazeem's Imports ---
from model import create_dataset, estimate_week, try_today, estimate_new, good_model
from news_fetcher import get_general_news
from ensemble_model import ensemble_predict, calculate_metrics
from professional_evaluation import rolling_window_backtest
from forex_fetcher import get_exchange_rate, get_currency_list
from crypto_fetcher import get_crypto_exchange_rate, get_crypto_list, get_target_currencies
from commodities_fetcher import get_commodity_price, get_commodity_list, get_commodities_by_category
from dotenv import load_dotenv

# --- Alpaca Imports REMOVED ---

load_dotenv() 

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
NEWS_API_KEY = "4f2abfc0913748ee9cedf3b5e5878bcc"
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY') 
# ALPACA KEYS REMOVED

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

# --- Helper function to fix JSON serialization ---
def clean_value(val):
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.int64, np.int32, np.int16, np.int8)):
        return int(val)
    if isinstance(val, (np.float64, np.float32, np.float16)):
        return float(val)
    return val

# --- In-memory storage ---
watchlist = set()

paper_trading_data = {
    "cash": 100000.0,
    "starting_cash": 100000.0,
    "positions": {},
    "options_positions": {},  
    "trade_history": [],
    "portfolio_history": []
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
        sanitized_ticker = ticker.split(':')[0] 
        stock = yf.Ticker(sanitized_ticker)
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
        
        sparkline = []
        try:
            hist = stock.history(period="7d", interval="1d")
            if not hist.empty:
                sparkline = [clean_value(p) for p in hist['Close']]
        except Exception as e:
            print(f"Could not fetch sparkline data: {e}")

        fundamentals = {} 
        if not ALPHA_VANTAGE_API_KEY:
            print("ALPHA_VANTAGE_API_KEY not set. Falling back to yfinance.")
            fundamentals = {
                "peRatio": clean_value(info.get('trailingPE')),
                "week52High": clean_value(info.get('fiftyTwoWeekHigh')),
                "week52Low": clean_value(info.get('fiftyTwoWeekLow')),
                "analystTargetPrice": clean_value(info.get('targetMeanPrice')),
                "recommendationKey": info.get('recommendationKey'),
                "overview": info.get('longBusinessSummary')
            }
        else:
            try:
                url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={sanitized_ticker.upper()}&apikey={ALPHA_VANTAGE_API_KEY}'
                r = requests.get(url)
                data = r.json()
                
                if data and 'Symbol' in data:
                    fundamentals = {
                        "overview": data.get("Description", "N/A"),
                        "peRatio": clean_value(data.get("PERatio")),
                        "forwardPE": clean_value(data.get("ForwardPE")),
                        "pegRatio": clean_value(data.get("PEGRatio")),
                        "dividendYield": clean_value(data.get("DividendYield")),
                        "beta": clean_value(data.get("Beta")),
                        "week52High": clean_value(data.get("52WeekHigh")),
                        "week52Low": clean_value(data.get("52WeekLow")),
                        "analystTargetPrice": clean_value(data.get("AnalystTargetPrice")),
                        "recommendationKey": "N/A" 
                    }
                else:
                    raise Exception("No data from Alpha Vantage")
            except Exception as e:
                print(f"Could not fetch fundamentals from Alpha Vantage: {e}. Falling back to yfinance.")
                fundamentals = {
                    "peRatio": clean_value(info.get('trailingPE')),
                    "week52High": clean_value(info.get('fiftyTwoWeekHigh')),
                    "week52Low": clean_value(info.get('fiftyTwoWeekLow')),
                    "analystTargetPrice": clean_value(info.get('targetMeanPrice')),
                    "recommendationKey": info.get('recommendationKey'),
                    "overview": info.get('longBusinessSummary')
                }

        formatted_data = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "price": clean_value(price),
            "change": clean_value(change),
            "changePercent": clean_value(change_percent),
            "marketCap": market_cap_formatted,
            "sparkline": sparkline,
            "fundamentals": fundamentals
        }
        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    period = request.args.get('period', '6mo')
    sanitized_ticker = ticker.split(':')[0] 
    
    period_interval_map = {
        "1d": {"period": "1d", "interval": "5m"},
        "5d": {"period": "5d", "interval": "15m"},
        "14d": {"period": "14d", "interval": "1d"},
        "1mo": {"period": "1mo", "interval": "1d"},
        "6mo": {"period": "6mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1d"},
    }
    params = period_interval_map.get(period)
    if not params:
        return jsonify({"error": "Invalid time frame specified."}), 400

    try:
        stock = yf.Ticker(sanitized_ticker)
        hist = stock.history(period=params["period"], interval=params["interval"])
        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data."}), 404

        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d %H:%M:%S'),
                "open": clean_value(row['Open']),
                "high": clean_value(row['High']),
                "low": clean_value(row['Low']),
                "close": clean_value(row['Close']),
                "volume": clean_value(row['Volume'])
            })
        
        try:
            predictions = predict_stock(sanitized_ticker).get_json()['predictions']
            for pred in predictions:
                chart_data.append({
                "date": pred["date"] + " 00:00:00",
                "open": None, "high": None, "low": None,
                "close": pred["predictedClose"],
                "volume": None
            })
        except Exception as e:
            print(f"Could not append prediction to chart: {e}")

        return jsonify(chart_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching chart data: {str(e)}"}), 500


# --- Stock-Specific News Endpoint ---
@app.route('/news')
def get_query_news():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "A search query ('q') is required."}), 400
        
    if not NEWS_API_KEY:
        return jsonify({"error": "NewsAPI key is not configured"}), 500
        
    try:
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
                'thumbnail_url': item.get('urlToImage')
            })
                
        return jsonify(formatted_news)
    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching news: {str(e)}"}), 500

# --- Options Endpoints (REVERTED to yfinance) ---
@app.route('/options/stock_price/<string:ticker>')
def get_options_stock_price(ticker):
    """Gets just the current price for a ticker, fast."""
    try:
        sanitized_ticker = ticker.split(':')[0] 
        stock = yf.Ticker(sanitized_ticker)
        info = stock.info
        price = info.get('regularMarketPrice', 0)
        if price == 0:
            price = info.get('previousClose', 0)
        return jsonify({"ticker": sanitized_ticker.upper(), "price": clean_value(price)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/options/<string:ticker>', methods=['GET'])
def get_option_expirations(ticker):
    """Gets all available expiration dates for a given ticker."""
    try:
        sanitized_ticker = ticker.split(':')[0]
        stock = yf.Ticker(sanitized_ticker)
        expirations = stock.options
        if not expirations:
            return jsonify({"error": "No options found for this ticker."}), 404
        return jsonify(list(expirations))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/options/chain/<string:ticker>', methods=['GET'])
def get_option_chain(ticker):
    """
    Gets the full option chain (calls and puts) for a specific expiration date.
    """
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "A date query parameter is required."}), 400
    
    try:
        sanitized_ticker = ticker.split(':')[0]
        stock = yf.Ticker(sanitized_ticker)
        chain = stock.option_chain(date)
        
        # Get stock price for ITM calculation
        info = stock.info
        price = info.get('regularMarketPrice', 0)
        if price == 0:
            price = info.get('previousClose', 0)
        
        # Helper to clean data for JSON
        def format_chain(df):
            cols_to_keep = [
                'contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 
                'volume', 'openInterest', 'impliedVolatility'
            ]
            existing_cols = [col for col in cols_to_keep if col in df.columns]
            df_filtered = df[existing_cols]
            
            df_cleaned = df_filtered.replace({np.nan: None})
            records = df_cleaned.to_dict('records')
            
            for record in records:
                for col in existing_cols:
                    record[col] = clean_value(record.get(col))
            return records

        return jsonify({
            "calls": format_chain(chain.calls),
            "puts": format_chain(chain.puts),
            "stock_price": clean_value(price)
        })
    except Exception as e:
        print(f"Error getting option chain: {e}")
        return jsonify({"error": "Could not retrieve option chain for this date."}), 404

# --- Tazeem's Endpoints (ML, Paper Trading, Other APIs) ---

@app.route('/predict/<string:ticker>')
def predict_stock(ticker):
    try:
        sanitized_ticker = ticker.split(':')[0] 
        stock = yf.Ticker(sanitized_ticker)
        info = stock.info
        df = create_dataset(sanitized_ticker, period="15d")
        if df.empty:
            return jsonify({"error": "No historical data available."}), 404
        current_df = estimate_week(df)
        prediction_df = current_df.tail(6)
        recent_close_df = df[df["Close"].notna()].tail(1)
        recent_close = recent_close_df["Close"].iloc[0] if not recent_close_df.empty else 0
        recent_date = recent_close_df.index[0] if not recent_close_df.empty else current_df.index[0]
        recent_predicted = current_df["Predicted"].iloc[0]
        response = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "recentDate": recent_date.strftime('%Y-%m-%d'),
            "recentClose": round(float(recent_close), 2),
            "recentPredicted": round(float(recent_predicted), 2),
            "predictions": [
                {"date": date.strftime('%Y-%m-%d'), "predictedClose": round(float(pred), 2)}
                for date, pred in zip(prediction_df.index, prediction_df["Predicted"])
            ]
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error predicting stock {ticker}: {e}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route('/predict/ensemble/<string:ticker>')
def predict_ensemble(ticker):
    try:
        sanitized_ticker = ticker.split(':')[0] 
        stock = yf.Ticker(sanitized_ticker)
        info = stock.info
        df = create_dataset(sanitized_ticker, period="1y")
        if df.empty or len(df) < 30:
            return jsonify({"error": "Insufficient historical data for ensemble prediction."}), 404
        ensemble_preds, individual_preds = ensemble_predict(df, days_ahead=6)
        if ensemble_preds is None:
            return jsonify({"error": "Ensemble prediction failed."}), 500
        recent_close = float(df["Close"].iloc[-1])
        recent_date = df.index[-1]
        future_dates = []
        current_date = recent_date
        for i in range(6):
            current_date = current_date + pd.Timedelta(days=1)
            future_dates.append(current_date)
        response = {
            "symbol": info.get('symbol', ticker.upper()),
            "companyName": info.get('longName', 'N/A'),
            "recentDate": recent_date.strftime('%Y-%m-%d'),
            "recentClose": round(recent_close, 2),
            "recentPredicted": round(float(ensemble_preds[0]), 2),
            "predictions": [
                {"date": date.strftime('%Y-%m-%d'), "predictedClose": round(float(pred), 2)}
                for date, pred in zip(future_dates, ensemble_preds)
            ],
            "modelBreakdown": {
                model_name: [round(float(p), 2) for p in preds]
                for model_name, preds in individual_preds.items()
            },
            "modelsUsed": list(individual_preds.keys()),
            "ensembleMethod": "weighted_average",
            "confidence": round(95.0 - (np.std(list(individual_preds.values())) * 2), 1) if len(individual_preds) > 1 else 85.0
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error in ensemble prediction for {ticker}: {e}")
        return jsonify({"error": f"Ensemble prediction failed: {str(e)}"}), 500

# --- Paper Trading ---

def record_portfolio_snapshot():
    # This function no longer records options, as yfinance is unreliable
    total_value = paper_trading_data['cash']
    for ticker, pos in paper_trading_data['positions'].items():
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


@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    positions_list = []
    total_positions_value = 0
    total_cost_basis_stocks = 0

    # --- 1. Process Stock Positions ---
    for ticker, pos in paper_trading_data["positions"].items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('regularMarketPrice', 0)
            if price == 0: price = info.get('previousClose', 0)
            prev_close = info.get('previousClose', price)
            company_name = info.get('longName', ticker)

            current_value = pos["shares"] * price
            cost_basis = pos["shares"] * pos["avg_cost"]
            total_pl = current_value - cost_basis
            total_pl_percent = (total_pl / cost_basis * 100) if cost_basis > 0 else 0
            daily_pl = pos["shares"] * (price - prev_close)
            daily_pl_percent = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            total_positions_value += current_value
            total_cost_basis_stocks += cost_basis

            positions_list.append({
                "ticker": ticker, "company_name": company_name, "shares": pos["shares"],
                "avg_cost": round(pos["avg_cost"], 2), "current_price": round(price, 2),
                "current_value": round(current_value, 2), "cost_basis": round(cost_basis, 2),
                "total_pl": round(total_pl, 2), "total_pl_percent": round(total_pl_percent, 2),
                "daily_pl": round(daily_pl, 2), "daily_pl_percent": round(daily_pl_percent, 2),
                "isOption": False
            })
        except Exception as e:
            print(f"Error getting data for stock {ticker}: {e}")
            continue

    # --- 2. Process Options Positions ---
    # We will just return the stored data, as live data is not reliable
    options_positions_list = []
    total_options_value = 0
    
    for contract_symbol, pos in paper_trading_data["options_positions"].items():
        # This will show the purchase price, not a live price.
        current_price = pos["avg_cost"] 
        current_value = pos["quantity"] * current_price * 100
        cost_basis = pos["quantity"] * pos["avg_cost"] * 100
        total_pl = current_value - cost_basis
        total_pl_percent = 0

        total_options_value += current_value

        options_positions_list.append({
            "ticker": contract_symbol, "company_name": contract_symbol, 
            "shares": pos["quantity"], 
            "avg_cost": round(pos["avg_cost"], 2), 
            "current_price": round(current_price, 2), 
            "current_value": round(current_value, 2),
            "cost_basis": round(cost_basis, 2),
            "total_pl": round(total_pl, 2), "total_pl_percent": round(total_pl_percent, 2),
            "daily_pl": 0, "daily_pl_percent": 0,
            "isOption": True
        })

    # --- 3. Combine Totals ---
    total_portfolio_value = paper_trading_data["cash"] + total_positions_value + total_options_value
    total_pl = total_portfolio_value - paper_trading_data["starting_cash"]
    total_return = (total_pl / paper_trading_data["starting_cash"] * 100) if paper_trading_data["starting_cash"] > 0 else 0

    return jsonify({
        "cash": round(paper_trading_data["cash"], 2),
        "positions_value": round(total_positions_value, 2),
        "options_value": round(total_options_value, 2), 
        "total_value": round(total_portfolio_value, 2),
        "starting_value": paper_trading_data["starting_cash"],
        "total_pl": round(total_pl, 2),
        "total_return": round(total_return, 2),
        "positions": positions_list, 
        "options_positions": options_positions_list
    })


@app.route('/paper/buy', methods=['POST'])
def buy_stock():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        shares = float(data.get('shares', 0))
        if shares <= 0:
            return jsonify({"error": "Shares must be positive"}), 400
        
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice')
        if price is None or price == 0:
            price = info.get('previousClose', 0)
        
        if price is None or price == 0:
            return jsonify({"error": f"Could not get price for {ticker}"}), 404
        
        total_cost = shares * price
        if total_cost > paper_trading_data["cash"]:
            return jsonify({"error": f"Insufficient cash. Need ${total_cost:.2f}, have ${paper_trading_data['cash']:.2f}"}), 400
        pos = paper_trading_data["positions"].get(ticker, {"shares": 0, "avg_cost": 0})
        new_total_shares = pos["shares"] + shares
        new_avg_cost = ((pos["avg_cost"] * pos["shares"]) + total_cost) / new_total_shares
        paper_trading_data["positions"][ticker] = {"shares": new_total_shares, "avg_cost": new_avg_cost}
        paper_trading_data["cash"] -= total_cost
        trade = {
            "type": "BUY", "ticker": ticker, "shares": shares, "price": price,
            "total": total_cost, "timestamp": datetime.now().isoformat()
        }
        paper_trading_data["trade_history"].append(trade)
        record_portfolio_snapshot() # Record snapshot
        return jsonify({
            "success": True, "message": f"Bought {shares} shares of {ticker} at ${price:.2f}",
            "total_cost": round(total_cost, 2), "remaining_cash": round(paper_trading_data["cash"], 2)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/paper/sell', methods=['POST'])
def sell_stock():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        shares = float(data.get('shares', 0))
        if shares <= 0:
            return jsonify({"error": "Shares must be positive"}), 400
        pos = paper_trading_data["positions"].get(ticker)
        if not pos or pos["shares"] < shares:
            available = pos["shares"] if pos else 0
            return jsonify({"error": f"Not enough shares. You have {available}, trying to sell {shares}"}), 400
        
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice')
        if price is None or price == 0:
            price = info.get('previousClose', 0)
        
        if price is None or price == 0:
            return jsonify({"error": f"Could not get price for {ticker}"}), 404
            
        proceeds = shares * price
        profit = proceeds - (shares * pos["avg_cost"])
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del paper_trading_data["positions"][ticker]
        paper_trading_data["cash"] += proceeds
        trade = {
            "type": "SELL", "ticker": ticker, "shares": shares, "price": price,
            "total": proceeds, "profit": profit, "timestamp": datetime.now().isoformat()
        }
        paper_trading_data["trade_history"].append(trade)
        record_portfolio_snapshot() # Record snapshot
        return jsonify({
            "success": True, "message": f"Sold {shares} shares of {ticker} at ${price:.2f}",
            "proceeds": round(proceeds, 2), "profit": round(profit, 2),
            "new_cash": round(paper_trading_data["cash"], 2)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/paper/options/buy', methods=['POST'])
def buy_option():
    try:
        data = request.get_json()
        contract_symbol = data.get('contractSymbol')
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0)) # This is the "ask" price (premium)

        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        # yfinance data is bad, so we use lastPrice if ask is 0
        if price == 0:
            stock = yf.Ticker(contract_symbol)
            price = stock.info.get('lastPrice', 0)
            if price == 0:
                return jsonify({"error": "Could not get a valid price for this contract."}), 400

        total_cost = quantity * price * 100 
        
        if total_cost > paper_trading_data["cash"]:
            return jsonify({"error": f"Insufficient cash. Need ${total_cost:.2f}, have ${paper_trading_data['cash']:.2f}"}), 400

        pos = paper_trading_data["options_positions"].get(contract_symbol, {"quantity": 0, "avg_cost": 0})
        new_total_quantity = pos["quantity"] + quantity
        new_avg_cost = ((pos["avg_cost"] * pos["quantity"]) + (price * quantity)) / new_total_quantity
        
        paper_trading_data["options_positions"][contract_symbol] = {"quantity": new_total_quantity, "avg_cost": new_avg_cost}
        paper_trading_data["cash"] -= total_cost

        trade = {
            "type": "BUY_OPTION", "ticker": contract_symbol, "shares": quantity, "price": price,
            "total": total_cost, "timestamp": datetime.now().isoformat()
        }
        paper_trading_data["trade_history"].append(trade)
        record_portfolio_snapshot() # Record snapshot
        return jsonify({
            "success": True, "message": f"Bought {quantity} {contract_symbol} contract(s) at ${price:.2f}",
            "remaining_cash": round(paper_trading_data["cash"], 2)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/paper/options/sell', methods=['POST'])
def sell_option():
    try:
        data = request.get_json()
        contract_symbol = data.get('contractSymbol')
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0)) # This is the "bid" price (premium)

        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        
        # yfinance data is bad, so we use lastPrice if bid is 0
        if price == 0:
            stock = yf.Ticker(contract_symbol)
            price = stock.info.get('lastPrice', 0)
            if price == 0:
                return jsonify({"error": "Could not get a valid price for this contract."}), 400

        pos = paper_trading_data["options_positions"].get(contract_symbol)
        if not pos or pos["quantity"] < quantity:
            available = pos["quantity"] if pos else 0
            return jsonify({"error": f"Not enough contracts. You have {available}, trying to sell {quantity}"}), 400

        proceeds = quantity * price * 100
        profit = proceeds - (quantity * pos["avg_cost"] * 100)
        
        pos["quantity"] -= quantity
        if pos["quantity"] == 0:
            del paper_trading_data["options_positions"][contract_symbol]
        
        paper_trading_data["cash"] += proceeds

        trade = {
            "type": "SELL_OPTION", "ticker": contract_symbol, "shares": quantity, "price": price,
            "total": proceeds, "profit": profit, "timestamp": datetime.now().isoformat()
        }
        paper_trading_data["trade_history"].append(trade)
        record_portfolio_snapshot() # Record snapshot
        return jsonify({
            "success": True, "message": f"Sold {quantity} {contract_symbol} contract(s) at ${price:.2f}",
            "profit": round(profit, 2), "new_cash": round(paper_trading_data["cash"], 2)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/paper/history', methods=['GET'])
def get_trade_history():
    return jsonify({"trades": paper_trading_data["trade_history"][-50:]})

@app.route('/paper/reset', methods=['POST'])
def reset_portfolio():
    paper_trading_data["cash"] = paper_trading_data["starting_cash"]
    paper_trading_data["positions"] = {}
    paper_trading_data["options_positions"] = {}
    paper_trading_data["trade_history"] = []
    paper_trading_data["portfolio_history"] = []
    return jsonify({
        "success": True, "message": "Portfolio reset to starting state",
        "starting_cash": paper_trading_data["starting_cash"]
    })

@app.route('/api/news', methods=['GET'])
def news_api():
    try:
        articles = get_general_news()
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch news: {str(e)}"}), 500

@app.route('/evaluate/<string:ticker>')
def evaluate_models(ticker):
    try:
        sanitized_ticker = ticker.split(':')[0] 
        test_days = int(request.args.get('test_days', 60))
        retrain_frequency = int(request.args.get('retrain_frequency', 5))
        result = rolling_window_backtest(sanitized_ticker, test_days=test_days, retrain_frequency=retrain_frequency)
        if result is None:
            return jsonify({"error": "Insufficient data for evaluation"}), 404
        return jsonify(result)
    except Exception as e:
        print(f"Evaluation error for {ticker}: {e}")
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500

@app.route('/forex/convert')
def forex_convert():
    try:
        from_currency = request.args.get('from', 'USD').upper()
        to_currency = request.args.get('to', 'EUR').upper()
        rate_data = get_exchange_rate(from_currency, to_currency)
        if rate_data is None:
            return jsonify({"error": "Could not fetch exchange rate"}), 404
        return jsonify(rate_data)
    except Exception as e:
        print(f"Forex convert error: {e}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@app.route('/forex/currencies')
def forex_currencies():
    try:
        currencies = get_currency_list()
        return jsonify(currencies)
    except Exception as e:
        print(f"Forex currencies error: {e}")
        return jsonify({"error": f"Failed to fetch currencies: {str(e)}"}), 500

@app.route('/crypto/convert')
def crypto_convert():
    try:
        from_crypto = request.args.get('from', 'BTC').upper()
        to_currency = request.args.get('to', 'USD').upper()
        rate_data = get_crypto_exchange_rate(from_crypto, to_currency)
        if rate_data is None:
            return jsonify({"error": "Could not fetch crypto exchange rate"}), 404
        return jsonify(rate_data)
    except Exception as e:
        print(f"Crypto convert error: {e}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@app.route('/crypto/list')
def crypto_list():
    try:
        cryptos = get_crypto_list()
        return jsonify(cryptos)
    except Exception as e:
        print(f"Crypto list error: {e}")
        return jsonify({"error": f"Failed to fetch crypto list: {str(e)}"}), 500

@app.route('/crypto/currencies')
def crypto_target_currencies():
    try:
        currencies = get_target_currencies()
        return jsonify(currencies)
    except Exception as e:
        print(f"Crypto currencies error: {e}")
        return jsonify({"error": f"Failed to fetch currencies: {str(e)}"}), 500

@app.route('/commodities/price/<string:commodity>')
def commodity_price(commodity):
    try:
        period = request.args.get('period', '5d')
        data = get_commodity_price(commodity, period)
        if data is None:
            return jsonify({"error": "Could not fetch commodity price"}), 404
        return jsonify(data)
    except Exception as e:
        print(f"Commodity price error: {e}")
        return jsonify({"error": f"Failed to fetch commodity: {str(e)}"}), 500

@app.route('/commodities/list')
def commodities_list():
    try:
        commodities = get_commodity_list()
        return jsonify(commodities)
    except Exception as e:
        print(f"Commodities list error: {e}")
        return jsonify({"error": f"Failed to fetch commodities: {str(e)}"}), 500

@app.route('/commodities/all')
def commodities_all():
    try:
        commodities = get_commodities_by_category()
        return jsonify(commodities)
    except Exception as e:
        print(f"Commodities all error: {e}")
        return jsonify({"error": f"Failed to fetch all commodities: {str(e)}"}), 500

@app.route('/fundamentals/<string:ticker>')
def get_fundamentals(ticker):
    try:
        sanitized_ticker = ticker.split(':')[0] 
        if not ALPHA_VANTAGE_API_KEY:
            return jsonify({"error": "Alpha Vantage API key not configured"}), 500
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={sanitized_ticker.upper()}&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url)
        data = response.json()
        if not data or 'Symbol' not in data:
            return jsonify({"error": f"No fundamental data found for {ticker}"}), 404
        
        fundamentals = {
            "symbol": data.get("Symbol", ticker.upper()), "name": data.get("Name", "N/A"),
            "description": data.get("Description", "N/A"), "exchange": data.get("Exchange", "N/A"),
            "currency": data.get("Currency", "USD"), "country": data.get("Country", "N/A"),
            "sector": data.get("Sector", "N/A"), "industry": data.get("Industry", "N/A"),
            "market_cap": data.get("MarketCapitalization", "N/A"), "pe_ratio": data.get("PERatio", "N/A"),
            "peg_ratio": data.get("PEGRatio", "N/A"), "book_value": data.get("BookValue", "N/A"),
            "dividend_per_share": data.get("DividendPerShare", "N/A"), "dividend_yield": data.get("DividendYield", "N/A"),
            "eps": data.get("EPS", "N/A"), "revenue_per_share_ttm": data.get("RevenuePerShareTTM", "N/A"),
            "profit_margin": data.get("ProfitMargin", "N/A"), "operating_margin_ttm": data.get("OperatingMarginTTM", "N/A"),
            "return_on_assets_ttm": data.get("ReturnOnAssetsTTM", "N/A"), "return_on_equity_ttm": data.get("ReturnOnEquityTTM", "N/A"),
            "revenue_ttm": data.get("RevenueTTM", "N/A"), "gross_profit_ttm": data.get("GrossProfitTTM", "N/A"),
            "diluted_eps_ttm": data.get("DilutedEPSTTM", "N/A"), "quarterly_earnings_growth_yoy": data.get("QuarterlyEarningsGrowthYOY", "N/A"),
            "quarterly_revenue_growth_yoy": data.get("QuarterlyRevenueGrowthYOY", "N/A"), "analyst_target_price": data.get("AnalystTargetPrice", "N/A"),
            "trailing_pe": data.get("TrailingPE", "N/A"), "forward_pe": data.get("ForwardPE", "N/A"),
            "price_to_sales_ratio_ttm": data.get("PriceToSalesRatioTTM", "N/A"), "price_to_book_ratio": data.get("PriceToBookRatio", "N/A"),
            "ev_to_revenue": data.get("EVToRevenue", "N/A"), "ev_to_ebitda": data.get("EVToEBITDA", "N/A"),
            "beta": data.get("Beta", "N/A"), "week_52_high": data.get("52WeekHigh", "N/A"),
            "week_52_low": data.get("52WeekLow", "N/A"), "day_50_moving_average": data.get("50DayMovingAverage", "N/A"),
            "day_200_moving_average": data.get("200DayMovingAverage", "N/A"), "shares_outstanding": data.get("SharesOutstanding", "N/A"),
            "dividend_date": data.get("DividendDate", "N/A"), "ex_dividend_date": data.get("ExDividendDate", "N/A")
        }
        return jsonify(fundamentals)
    except Exception as e:
        print(f"Fundamentals error for {ticker}: {e}")
        return jsonify({"error": f"Failed to fetch fundamentals: {str(e)}"}), 500

# --- Main execution ---
if __name__ == '__main__':
    init_db() # We need to re-enable this!
    app.run(debug=True, port=5001)