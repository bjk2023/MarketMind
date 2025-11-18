# To run this file, you need to install Flask, Flask-CORS, yfinance, and pandas:
# pip install Flask Flask-CORS yfinance pandas
import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from model import create_dataset, estimate_week, try_today, estimate_new, good_model
from news_fetcher import get_general_news
from ensemble_model import ensemble_predict, calculate_metrics
from professional_evaluation import rolling_window_backtest
from forex_fetcher import get_exchange_rate, get_currency_list
from crypto_fetcher import get_crypto_exchange_rate, get_crypto_list, get_target_currencies
from commodities_fetcher import get_commodity_price, get_commodity_list, get_commodities_by_category
from dotenv import load_dotenv
from logger_config import setup_logger, log_api_request, log_api_error, log_data_fetch
from security import (
    setup_rate_limiting, 
    RateLimits,
    validate_ticker, 
    validate_request_json,
    sanitize_ticker
)
from database import db, init_database, create_default_user, update_portfolio_history

load_dotenv()

# Initialize logger
logger = setup_logger('marketmind_api')
logger.info("🚀 MarketMind API Starting...")

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketmind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Setup rate limiting
limiter = setup_rate_limiting(app)
logger.info("🔒 Rate limiting enabled")

# Log Flask initialization
logger.info("✅ Flask app initialized with CORS enabled")

# Initialize database tables
with app.app_context():
    init_database(app)
    logger.info("✅ Database initialized")

# Create default user and data
with app.app_context():
    default_user = create_default_user()
    logger.info(f"✅ Default user ready: {default_user.username if default_user else 'None'}")

# --- Watchlist Endpoints ---

@app.route('/watchlist', methods=['GET'])
@limiter.limit(RateLimits.LIGHT)
def get_watchlist():
    """Returns the list of tickers in the default user's watchlist with stock data."""
    try:
        # Get default user (demo user)
        from database import User, Watchlist
        default_user = User.query.filter_by(username='demo').first()
        
        if not default_user:
            return jsonify({"error": "Default user not found"}), 404
        
        # Get first watchlist or create default
        watchlist = default_user.watchlists[0] if default_user.watchlists else None
        
        if not watchlist:
            # Create default watchlist
            watchlist = Watchlist(
                name='Default Watchlist',
                description='Default watchlist for demo user'
            )
            default_user.watchlists.append(watchlist)
            db.session.commit()
        
        # Get detailed stock data for each ticker
        import yfinance as yf
        import json
        stocks_data = []
        
        # Parse tickers if it's a string
        tickers_list = watchlist.tickers
        if isinstance(tickers_list, str):
            try:
                tickers_list = json.loads(tickers_list)
            except:
                # If parsing fails, try to extract from the string
                tickers_list = [ticker.strip('"[]') for ticker in tickers_list.split(',')]
        
        for ticker in tickers_list:
            ticker = ticker.strip('"[]')
            if not ticker:
                continue
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get current price
                price = info.get('regularMarketPrice', 0)
                if price == 0:
                    price = info.get('previousClose', 0)
                
                # Get previous close for change calculation
                prev_close = info.get('previousClose', price)
                change = price - prev_close
                change_percent = ((change / prev_close) * 100) if prev_close > 0 else 0
                
                stocks_data.append({
                    "symbol": ticker,
                    "name": info.get('longName', ticker),
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": info.get('volume', 0)
                })
            except Exception as e:
                logger.warning(f"Failed to fetch data for {ticker}: {e}")
                continue
        
        log_api_request(logger, '/watchlist', 'GET', status='completed')
        return jsonify(stocks_data)
        
    except Exception as e:
        log_api_error(logger, '/watchlist', e)
        return jsonify({"error": "Failed to fetch watchlist"}), 500

@app.route('/watchlist/<string:ticker>', methods=['POST'])
@limiter.limit(RateLimits.WRITE)
def add_to_watchlist(ticker):
    """Adds a ticker to the default user's watchlist."""
    try:
        # Validate and sanitize ticker
        is_valid, error = validate_ticker(ticker)
        if not is_valid:
            logger.warning(f"Invalid ticker in watchlist add: {ticker}")
            return jsonify({"error": error}), 400
        
        ticker = sanitize_ticker(ticker)
        
        # Get default user
        from database import User, Watchlist
        default_user = User.query.filter_by(username='demo').first()
        
        if not default_user:
            return jsonify({"error": "Default user not found"}), 404
        
        # Get or create watchlist
        watchlist = default_user.watchlists[0] if default_user.watchlists else None
        
        if not watchlist:
            watchlist = Watchlist(
                name='Default Watchlist',
                description='Default watchlist for demo user'
            )
            watchlist.set_tickers([])
            db.session.add(watchlist)
            default_user.watchlists.append(watchlist)
            db.session.commit()
        
        # Add ticker
        watchlist.add_ticker(ticker)
        db.session.commit()
        
        logger.info(f"Added {ticker} to watchlist")
        log_api_request(logger, f'/watchlist/{ticker}', 'POST', status='completed')
        
        return jsonify({
            "message": f"{ticker} added to watchlist.",
            "watchlist": {
                'id': watchlist.id,
                'name': watchlist.name,
                'tickers': watchlist.get_tickers()
            }
        }), 201
        
    except Exception as e:
        log_api_error(logger, f'/watchlist/{ticker}', e)
        return jsonify({"error": "Failed to add ticker to watchlist"}), 500

@app.route('/watchlist/<string:ticker>', methods=['DELETE'])
@limiter.limit(RateLimits.WRITE)
def remove_from_watchlist(ticker):
    """Removes a ticker from the default user's watchlist."""
    try:
        ticker = sanitize_ticker(ticker)
        
        # Get default user
        from database import User
        default_user = User.query.filter_by(username='demo').first()
        
        if not default_user:
            return jsonify({"error": "Default user not found"}), 404
        
        # Get watchlist
        watchlist = default_user.watchlists[0] if default_user.watchlists else None
        
        if not watchlist:
            return jsonify({"error": "No watchlist found"}), 404
        
        # Remove ticker
        watchlist.remove_ticker(ticker)
        db.session.commit()
        
        logger.info(f"Removed {ticker} from watchlist")
        log_api_request(logger, f'/watchlist/{ticker}', 'DELETE', status='completed')
        
        return jsonify({
            "message": f"{ticker} removed from watchlist.",
            "watchlist": {
                'id': watchlist.id,
                'name': watchlist.name,
                'tickers': watchlist.get_tickers()
            }
        })
        
    except Exception as e:
        log_api_error(logger, f'/watchlist/{ticker}', e)
        return jsonify({"error": "Failed to remove ticker from watchlist"}), 500

# --- Stock Data Endpoints ---

@app.route('/stock/<string:ticker>')
@limiter.limit(RateLimits.STANDARD)
def get_stock_data(ticker):
    """
    This function handles requests for a specific stock ticker using yfinance.
    It fetches company info and formats it for the frontend data card.
    """
    # Validate and sanitize ticker
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        logger.warning(f"Invalid ticker format: {ticker} | Error: {error}")
        return jsonify({"error": error}), 400
    
    ticker = sanitize_ticker(ticker)
    log_api_request(logger, f'/stock/{ticker}', 'GET', status='started')
    
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

@app.route('/predict/<string:ticker>')
@limiter.limit(RateLimits.STANDARD)
def predict_stock(ticker):
    """
    Predicts the next day's closing price for a given stock ticker.
    """
    # Validate and sanitize ticker
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        logger.warning(f"Invalid ticker format: {ticker} | Error: {error}")
        return jsonify({"error": error}), 400
    
    ticker = sanitize_ticker(ticker)
    log_api_request(logger, f'/predict/{ticker}', 'GET', status='started')
    try:
        # Create dataset for the last 15 days - predicting today's close using past 14
        stock = yf.Ticker(ticker)
        info = stock.info
        df = create_dataset(ticker, period="15d")
        if df.empty:
            logger.warning(f"No historical data available for {ticker}")
            return jsonify({"error": "No historical data available."}), 404

        # Predict today's closing price
        current_df = estimate_week(df)
        prediction_df = current_df.tail(6)
        
        # Get the most recent actual close price (not NaN)
        recent_close_df = df[df["Close"].notna()].tail(1)
        recent_close = recent_close_df["Close"].iloc[0] if not recent_close_df.empty else 0
        recent_date = recent_close_df.index[0] if not recent_close_df.empty else current_df.index[0]
        
        # Get the first prediction
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

        logger.info(f"✅ Prediction completed for {ticker} | Recent: ${recent_close:.2f} | Predicted: ${recent_predicted:.2f}")
        return jsonify(response)

    except Exception as e:
        log_api_error(logger, f'/predict/{ticker}', e, ticker)
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route('/predict/ensemble/<string:ticker>')
@limiter.limit(RateLimits.STANDARD)
def predict_ensemble(ticker):
    """
    Enhanced prediction using ensemble of multiple ML models (Linear Regression, Random Forest, XGBoost)
    """
    # Validate and sanitize ticker
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        logger.warning(f"Invalid ticker format: {ticker} | Error: {error}")
        return jsonify({"error": error}), 400
    
    ticker = sanitize_ticker(ticker)
    log_api_request(logger, f'/predict/ensemble/{ticker}', 'GET', status='started')
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get more data for ML models (1 year)
        df = create_dataset(ticker, period="1y")
        if df.empty or len(df) < 30:
            return jsonify({"error": "Insufficient historical data for ensemble prediction."}), 404
        
        # Get ensemble predictions
        ensemble_preds, individual_preds = ensemble_predict(df, days_ahead=6)
        
        if ensemble_preds is None:
            return jsonify({"error": "Ensemble prediction failed."}), 500
        
        # Get recent data
        recent_close = float(df["Close"].iloc[-1])
        recent_date = df.index[-1]
        
        # Generate future dates
        future_dates = []
        current_date = recent_date
        for i in range(6):
            current_date = current_date + pd.Timedelta(days=1)
            future_dates.append(current_date)
        
        # Format response
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
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Ensemble prediction failed: {str(e)}"}), 500


@app.route('/chart/<string:ticker>')
def get_chart_data(ticker):
    """
    This function gets historical data for the chart using yfinance.
    It now accepts a 'period' query parameter to fetch different time frames.
    """
    period = request.args.get('period', '6mo')

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
        stock = yf.Ticker(ticker)
        hist = stock.history(period=params["period"], interval=params["interval"])

        if hist.empty:
            return jsonify({"error": "Could not retrieve time series data for the selected period."}), 404

        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d %H:%M:%S'),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })
        predictions = predict_stock(ticker).get_json()['predictions']
        for pred in predictions:
            chart_data.append({
            "date": pred["date"] + " 00:00:00",
            "open": None,
            "high": None,
            "low": None,
            "close": pred["predictedClose"],
            "volume": None
        })

        return jsonify(chart_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred while fetching chart data: {str(e)}"}), 500

# --- Paper Trading Endpoints ---
from datetime import datetime


def get_default_portfolio():
    """Get default user's portfolio"""
    from database import User, Portfolio
    default_user = User.query.filter_by(username='demo').first()
    if not default_user:
        return None
    
    portfolio = default_user.portfolios[0] if default_user.portfolios else None
    if not portfolio:
        # Create default portfolio
        portfolio = Portfolio(
            name='Default Portfolio',
            description='Default portfolio for demo user',
            starting_cash=100000.0,
            current_cash=100000.0,
            user_id=default_user.id
        )
        db.session.add(portfolio)
        db.session.commit()
    
    return portfolio


@app.route('/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    """Return the current state of the paper trading portfolio with full metrics."""
    try:
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        positions_list = []
        
        # Get positions from database
        for position in portfolio.positions:
            try:
                stock = yf.Ticker(position.ticker)
                info = stock.info
                price = info.get('regularMarketPrice', 0)
                if price == 0:
                    price = info.get('previousClose', 0)
                
                prev_close = info.get('previousClose', price)
                company_name = info.get('longName', position.ticker)

                current_value = position.shares * price
                cost_basis = position.get_cost_basis()
                total_pl = current_value - cost_basis
                total_pl_percent = (total_pl / cost_basis * 100) if cost_basis > 0 else 0
                daily_pl = position.shares * (price - prev_close)
                daily_pl_percent = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

                positions_list.append({
                    "ticker": position.ticker,
                    "company_name": company_name,
                    "shares": position.shares,
                    "avg_cost": position.avg_cost,
                    "current_price": price,
                    "prev_close": prev_close,
                    "current_value": current_value,
                    "cost_basis": cost_basis,
                    "total_pl": total_pl,
                    "total_pl_percent": round(total_pl_percent, 2),
                    "daily_pl": round(daily_pl, 2),
                    "daily_pl_percent": round(daily_pl_percent, 2)
                })
            except Exception as e:
                logger.warning(f"Error fetching data for {position.ticker}: {e}")
                # Add position with basic data
                positions_list.append({
                    "ticker": position.ticker,
                    "company_name": position.ticker,
                    "shares": position.shares,
                    "avg_cost": position.avg_cost,
                    "current_price": position.avg_cost,
                    "prev_close": position.avg_cost,
                    "current_value": position.get_cost_basis(),
                    "cost_basis": position.get_cost_basis(),
                    "total_pl": 0,
                    "total_pl_percent": 0,
                    "daily_pl": 0,
                    "daily_pl_percent": 0
                })

        # Calculate portfolio totals
        total_positions_value = sum(pos["current_value"] for pos in positions_list)
        total_cost_basis = sum(pos["cost_basis"] for pos in positions_list)
        total_portfolio_value = portfolio.get_total_value()
        total_cash = portfolio.current_cash
        total_pl = total_portfolio_value - portfolio.starting_cash
        total_pl_percent = (total_pl / portfolio.starting_cash * 100) if portfolio.starting_cash > 0 else 0

        log_api_request(logger, '/paper/portfolio', 'GET', status='completed')
        
        return jsonify({
            "cash": round(total_cash, 2),
            "positions_value": round(total_positions_value, 2),
            "total_value": round(total_portfolio_value, 2),
            "starting_value": portfolio.starting_cash,
            "total_pl": round(total_pl, 2),
            "total_return": round(total_pl_percent, 2),
            "positions": positions_list
        })
        
    except Exception as e:
        log_api_error(logger, '/paper/portfolio', e)
        return jsonify({"error": "Failed to fetch portfolio data"}), 500


@app.route('/paper/buy', methods=['POST'])
@limiter.limit(RateLimits.WRITE)
@validate_request_json(['ticker', 'shares'])
def buy_stock():
    """Simulate buying shares in the paper trading account."""
    try:
        data = request.get_json()
        ticker = sanitize_ticker(data.get('ticker', ''))
        
        # Validate ticker
        is_valid, error = validate_ticker(ticker)
        if not is_valid:
            logger.warning(f"Invalid ticker in buy request: {ticker}")
            return jsonify({"error": error}), 400
        
        shares = float(data.get('shares', 0))
        
        if shares <= 0:
            return jsonify({"error": "Shares must be positive"}), 400

        # Get portfolio
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        # Get current price
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice', 0)
        if price == 0:
            price = info.get('previousClose', 0)
        
        if price == 0:
            return jsonify({"error": f"Could not get price for {ticker}"}), 404

        total_cost = shares * price
        if total_cost > portfolio.current_cash:
            return jsonify({"error": f"Insufficient cash. Need ${total_cost:.2f}, have ${portfolio.current_cash:.2f}"}), 400

        # Update or create position
        from database import Position, Trade
        position = Position.query.filter_by(portfolio_id=portfolio.id, ticker=ticker).first()
        
        if position:
            # Update existing position
            new_total_shares = position.shares + shares
            new_avg_cost = ((position.avg_cost * position.shares) + total_cost) / new_total_shares
            position.shares = new_total_shares
            position.avg_cost = new_avg_cost
        else:
            # Create new position
            position = Position(
                portfolio_id=portfolio.id,
                ticker=ticker,
                shares=shares,
                avg_cost=price
            )
            db.session.add(position)

        # Update cash
        portfolio.current_cash -= total_cost

        # Record trade
        trade = Trade(
            portfolio_id=portfolio.id,
            ticker=ticker,
            trade_type='BUY',
            shares=shares,
            price=price,
            total=total_cost,
            notes=f'Bought {shares} shares at ${price:.2f}'
        )
        db.session.add(trade)

        db.session.commit()

        log_api_request(logger, '/paper/buy', 'POST', status='completed')

        return jsonify({
            "success": True,
            "message": f"Bought {shares} shares of {ticker} at ${price:.2f}",
            "total_cost": round(total_cost, 2),
            "remaining_cash": round(portfolio.current_cash, 2)
        }), 200

    except Exception as e:
        log_api_error(logger, '/paper/buy', e)
        return jsonify({"error": "Failed to execute buy order"}), 500


@app.route('/paper/sell', methods=['POST'])
@limiter.limit(RateLimits.WRITE)
@validate_request_json(['ticker', 'shares'])
def sell_stock():
    """Simulate selling shares."""
    try:
        data = request.get_json()
        ticker = sanitize_ticker(data.get('ticker', ''))
        
        # Validate ticker
        is_valid, error = validate_ticker(ticker)
        if not is_valid:
            logger.warning(f"Invalid ticker in sell request: {ticker}")
            return jsonify({"error": error}), 400
        
        shares = float(data.get('shares', 0))
        
        if shares <= 0:
            return jsonify({"error": "Shares must be positive"}), 400

        # Get portfolio
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        # Get position
        from database import Position, Trade
        position = Position.query.filter_by(portfolio_id=portfolio.id, ticker=ticker).first()
        
        if not position or position.shares < shares:
            available = position.shares if position else 0
            return jsonify({"error": f"Not enough shares. You have {available}, trying to sell {shares}"}), 400

        # Get current price
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('regularMarketPrice', 0)
        if price == 0:
            price = info.get('previousClose', 0)
        if price == 0:
            return jsonify({"error": f"Could not get price for {ticker}"}), 404

        proceeds = shares * price
        profit = proceeds - (shares * position.avg_cost)
        
        # Update position
        position.shares -= shares
        
        # Remove position if no shares left
        if position.shares == 0:
            db.session.delete(position)
        
        # Update cash
        portfolio.current_cash += proceeds

        # Record trade
        trade = Trade(
            portfolio_id=portfolio.id,
            ticker=ticker,
            trade_type='SELL',
            shares=shares,
            price=price,
            total=proceeds,
            notes=f'Sold {shares} shares at ${price:.2f}'
        )
        db.session.add(trade)

        db.session.commit()

        log_api_request(logger, '/paper/sell', 'POST', status='completed')

        return jsonify({
            "success": True,
            "message": f"Sold {shares} shares of {ticker} at ${price:.2f}",
            "proceeds": round(proceeds, 2),
            "profit": round(profit, 2),
            "new_cash": round(portfolio.current_cash, 2)
        }), 200

    except Exception as e:
        log_api_error(logger, '/paper/sell', e)
        return jsonify({"error": "Failed to execute sell order"}), 500


@app.route('/paper/history', methods=['GET'])
def get_trade_history():
    """Get trade history"""
    try:
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        from database import Trade
        
        # Get last 50 trades
        trades = Trade.query.filter_by(portfolio_id=portfolio.id).order_by(Trade.created_at.desc()).limit(50).all()
        
        trades_list = []
        for trade in trades:
            trades_list.append({
                "ticker": trade.ticker,
                "shares": trade.shares,
                "price": trade.price,
                "type": trade.trade_type,  # Changed from trade_type to type
                "total": trade.total,      # Added total field
                "timestamp": trade.created_at.isoformat()
            })

        log_api_request(logger, '/paper/history', 'GET', status='completed')
        
        return jsonify({
            "trades": trades_list
        })
        
    except Exception as e:
        log_api_error(logger, '/paper/history', e)
        return jsonify({"error": "Failed to fetch trade history"}), 500


@app.route('/paper/analytics', methods=['GET'])
def get_portfolio_analytics():
    """Get portfolio performance analytics and history"""
    try:
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        from database import PortfolioHistory
        
        # Get portfolio history (last 30 days)
        history = PortfolioHistory.query.filter_by(portfolio_id=portfolio.id).order_by(PortfolioHistory.date.desc()).limit(30).all()
        
        history_list = []
        for record in history:
            history_list.append({
                "date": record.date.isoformat(),
                "total_value": record.total_value,
                "cash_balance": record.cash_balance,
                "positions_value": record.positions_value,
                "total_pnl": record.total_pnl,
                "pnl_percentage": record.pnl_percentage
            })

        # Calculate performance metrics
        if len(history_list) >= 2:
            current_value = history_list[0]["total_value"]
            previous_value = history_list[1]["total_value"]
            daily_change = current_value - previous_value
            daily_change_percent = (daily_change / previous_value * 100) if previous_value > 0 else 0
            
            # Weekly change (if available)
            weekly_change = 0
            weekly_change_percent = 0
            if len(history_list) >= 7:
                weekly_value = history_list[6]["total_value"]
                weekly_change = current_value - weekly_value
                weekly_change_percent = (weekly_change / weekly_value * 100) if weekly_value > 0 else 0
        else:
            daily_change = 0
            daily_change_percent = 0
            weekly_change = 0
            weekly_change_percent = 0

        # Best and worst performers
        best_performer = None
        worst_performer = None
        best_performance = -float('inf')
        worst_performance = float('inf')
        
        for position in portfolio.positions:
            try:
                stock = yf.Ticker(position.ticker)
                price = stock.info.get('regularMarketPrice', 0)
                if price == 0:
                    price = stock.info.get('previousClose', 0)
                
                if price > 0:
                    performance = ((price - position.avg_cost) / position.avg_cost * 100) if position.avg_cost > 0 else 0
                    
                    if performance > best_performance:
                        best_performance = performance
                        best_performer = {
                            "ticker": position.ticker,
                            "performance": round(performance, 2),
                            "current_price": price,
                            "avg_cost": position.avg_cost
                        }
                    
                    if performance < worst_performance:
                        worst_performance = performance
                        worst_performer = {
                            "ticker": position.ticker,
                            "performance": round(performance, 2),
                            "current_price": price,
                            "avg_cost": position.avg_cost
                        }
            except:
                continue

        # Update portfolio history for today
        from database import update_portfolio_history
        update_portfolio_history(portfolio.id)

        log_api_request(logger, '/paper/analytics', 'GET', status='completed')
        
        return jsonify({
            "history": history_list,
            "performance": {
                "daily_change": round(daily_change, 2),
                "daily_change_percent": round(daily_change_percent, 2),
                "weekly_change": round(weekly_change, 2),
                "weekly_change_percent": round(weekly_change_percent, 2),
                "total_return": round(portfolio.get_pnl_percentage(), 2),
                "total_pnl": round(portfolio.get_total_pnl(), 2)
            },
            "top_performers": {
                "best": best_performer,
                "worst": worst_performer
            },
            "portfolio_stats": {
                "total_value": round(portfolio.get_total_value(), 2),
                "cash_balance": round(portfolio.current_cash, 2),
                "positions_value": round(portfolio.get_total_value() - portfolio.current_cash, 2),
                "num_positions": len(portfolio.positions),
                "num_trades": len(portfolio.trades)
            }
        })
        
    except Exception as e:
        log_api_error(logger, '/paper/analytics', e)
        return jsonify({"error": "Failed to fetch portfolio analytics"}), 500


@app.route('/paper/reset', methods=['POST'])
def reset_portfolio():
    """Reset portfolio to starting state"""
    try:
        portfolio = get_default_portfolio()
        if not portfolio:
            return jsonify({"error": "No default portfolio found"}), 404

        # Delete all positions and trades
        from database import Position, Trade, PortfolioHistory
        Position.query.filter_by(portfolio_id=portfolio.id).delete()
        Trade.query.filter_by(portfolio_id=portfolio.id).delete()
        PortfolioHistory.query.filter_by(portfolio_id=portfolio.id).delete()
        
        # Reset cash
        portfolio.current_cash = portfolio.starting_cash
        
        db.session.commit()

        log_api_request(logger, '/paper/reset', 'POST', status='completed')
        
        return jsonify({
            "success": True,
            "message": "Portfolio reset to starting state",
            "starting_cash": portfolio.starting_cash
        })
        
    except Exception as e:
        log_api_error(logger, '/paper/reset', e)
        return jsonify({"error": "Failed to reset portfolio"}), 500

# --- News Endpoint ---

@app.route('/api/news', methods=['GET'])
def news_api():
    """
    API endpoint to fetch general market news.
    """
    try:
        articles = get_general_news()
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch news: {str(e)}"}), 500


@app.route('/evaluate/<string:ticker>')
@limiter.limit(RateLimits.HEAVY)
def evaluate_models(ticker):
    """
    Professional-grade evaluation with rolling window backtesting
    
    Uses 42 fixed features, multiple ML models, and comprehensive metrics
    Returns predictions vs actuals, all metrics, and trading performance
    """
    # Validate and sanitize ticker
    is_valid, error = validate_ticker(ticker)
    if not is_valid:
        logger.warning(f"Invalid ticker format: {ticker} | Error: {error}")
        return jsonify({"error": error}), 400
    
    ticker = sanitize_ticker(ticker)
    log_api_request(logger, f'/evaluate/{ticker}', 'GET', status='started')
    
    try:
        test_days = int(request.args.get('test_days', 60))
        retrain_frequency = int(request.args.get('retrain_frequency', 5))
        
        print(f"Running professional evaluation for {ticker}...")
        result = rolling_window_backtest(ticker, test_days=test_days, retrain_frequency=retrain_frequency)
        
        if result is None:
            return jsonify({"error": "Insufficient data for evaluation"}), 404
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Evaluation error for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500


@app.route('/forex/convert')
def forex_convert():
    """
    Convert between two currencies using real-time exchange rates
    Query params: from_currency, to_currency
    """
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
    """
    Get list of available currencies
    """
    try:
        currencies = get_currency_list()
        return jsonify(currencies)
    
    except Exception as e:
        print(f"Forex currencies error: {e}")
        return jsonify({"error": f"Failed to fetch currencies: {str(e)}"}), 500


@app.route('/crypto/convert')
def crypto_convert():
    """
    Convert cryptocurrency to fiat currency
    Query params: from (crypto), to (currency)
    """
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
    """
    Get list of available cryptocurrencies
    """
    try:
        cryptos = get_crypto_list()
        return jsonify(cryptos)
    
    except Exception as e:
        print(f"Crypto list error: {e}")
        return jsonify({"error": f"Failed to fetch crypto list: {str(e)}"}), 500


@app.route('/crypto/currencies')
def crypto_target_currencies():
    """
    Get list of target currencies for crypto conversion
    """
    try:
        currencies = get_target_currencies()
        return jsonify(currencies)
    
    except Exception as e:
        print(f"Crypto currencies error: {e}")
        return jsonify({"error": f"Failed to fetch currencies: {str(e)}"}), 500


@app.route('/commodities/price/<string:commodity>')
def commodity_price(commodity):
    """
    Get current price for a specific commodity
    """
    try:
        # Period parameter for yfinance (1d, 5d, 1mo, etc.)
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
    """
    Get list of available commodities
    """
    try:
        commodities = get_commodity_list()
        return jsonify(commodities)
    
    except Exception as e:
        print(f"Commodities list error: {e}")
        return jsonify({"error": f"Failed to fetch commodities: {str(e)}"}), 500


@app.route('/commodities/all')
def commodities_all():
    """
    Get current prices for all commodities grouped by category
    """
    try:
        commodities = get_commodities_by_category()
        return jsonify(commodities)
    
    except Exception as e:
        print(f"Commodities all error: {e}")
        return jsonify({"error": f"Failed to fetch all commodities: {str(e)}"}), 500


# --- Fundamentals Endpoints ---
@app.route('/fundamentals/<string:ticker>')
def get_fundamentals(ticker):
    """
    Get comprehensive fundamental data for a company using Alpha Vantage
    """
    try:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return jsonify({"error": "Alpha Vantage API key not configured"}), 500
        
        # Get company overview from Alpha Vantage
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker.upper()}&apikey={api_key}'
        response = requests.get(url)
        data = response.json()
        
        # Check for errors or empty response
        if not data or 'Symbol' not in data:
            return jsonify({"error": f"No fundamental data found for {ticker}"}), 404
        
        # Parse and format the data
        fundamentals = {
            "symbol": data.get("Symbol", ticker.upper()),
            "name": data.get("Name", "N/A"),
            "description": data.get("Description", "N/A"),
            "exchange": data.get("Exchange", "N/A"),
            "currency": data.get("Currency", "USD"),
            "country": data.get("Country", "N/A"),
            "sector": data.get("Sector", "N/A"),
            "industry": data.get("Industry", "N/A"),
            
            # Market Data
            "market_cap": data.get("MarketCapitalization", "N/A"),
            "pe_ratio": data.get("PERatio", "N/A"),
            "peg_ratio": data.get("PEGRatio", "N/A"),
            "book_value": data.get("BookValue", "N/A"),
            "dividend_per_share": data.get("DividendPerShare", "N/A"),
            "dividend_yield": data.get("DividendYield", "N/A"),
            "eps": data.get("EPS", "N/A"),
            "revenue_per_share_ttm": data.get("RevenuePerShareTTM", "N/A"),
            "profit_margin": data.get("ProfitMargin", "N/A"),
            "operating_margin_ttm": data.get("OperatingMarginTTM", "N/A"),
            "return_on_assets_ttm": data.get("ReturnOnAssetsTTM", "N/A"),
            "return_on_equity_ttm": data.get("ReturnOnEquityTTM", "N/A"),
            "revenue_ttm": data.get("RevenueTTM", "N/A"),
            "gross_profit_ttm": data.get("GrossProfitTTM", "N/A"),
            "diluted_eps_ttm": data.get("DilutedEPSTTM", "N/A"),
            "quarterly_earnings_growth_yoy": data.get("QuarterlyEarningsGrowthYOY", "N/A"),
            "quarterly_revenue_growth_yoy": data.get("QuarterlyRevenueGrowthYOY", "N/A"),
            "analyst_target_price": data.get("AnalystTargetPrice", "N/A"),
            "trailing_pe": data.get("TrailingPE", "N/A"),
            "forward_pe": data.get("ForwardPE", "N/A"),
            "price_to_sales_ratio_ttm": data.get("PriceToSalesRatioTTM", "N/A"),
            "price_to_book_ratio": data.get("PriceToBookRatio", "N/A"),
            "ev_to_revenue": data.get("EVToRevenue", "N/A"),
            "ev_to_ebitda": data.get("EVToEBITDA", "N/A"),
            "beta": data.get("Beta", "N/A"),
            "week_52_high": data.get("52WeekHigh", "N/A"),
            "week_52_low": data.get("52WeekLow", "N/A"),
            "day_50_moving_average": data.get("50DayMovingAverage", "N/A"),
            "day_200_moving_average": data.get("200DayMovingAverage", "N/A"),
            "shares_outstanding": data.get("SharesOutstanding", "N/A"),
            "dividend_date": data.get("DividendDate", "N/A"),
            "ex_dividend_date": data.get("ExDividendDate", "N/A")
        }
        
        return jsonify(fundamentals)
    
    except Exception as e:
        print(f"Fundamentals error for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch fundamentals: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=False, port=5001)

