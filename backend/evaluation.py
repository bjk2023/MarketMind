import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from ensemble_model import (
    linear_regression_predict,
    random_forest_predict,
    xgboost_predict,
    ensemble_predict
)
import warnings
warnings.filterwarnings('ignore')


def backtest_model(ticker, model_func, model_name, days_back=30, prediction_days=1):
    """
    Backtest a prediction model on historical data
    
    Args:
        ticker: Stock ticker symbol
        model_func: Function that returns predictions
        model_name: Name of the model
        days_back: How many days in the past to test
        prediction_days: How many days ahead to predict (simplified to 1)
    
    Returns:
        Dictionary with backtest results
    """
    try:
        # Download historical data - get more data for training
        df = yf.download(ticker, period="1y", auto_adjust=False, progress=False)[['Close']].copy()
        
        if df.empty or len(df) < 100:  # Need sufficient history
            print(f"Insufficient data: got {len(df)} days")
            return None
        
        predictions = []
        actuals = []
        dates = []
        
        # Use the most recent days_back days for testing
        # Train on everything before that
        test_start_idx = len(df) - days_back
        
        if test_start_idx < 50:  # Need at least 50 days for training
            print(f"Not enough training data: test starts at {test_start_idx}")
            return None
        
        # Predict every 3 days to balance accuracy and speed
        step_size = 3
        for i in range(test_start_idx, len(df) - prediction_days, step_size):
            train_data = df.iloc[:i]
            
            # Make prediction
            try:
                if model_name == "ensemble":
                    pred, _ = model_func(train_data, days_ahead=prediction_days)
                else:
                    pred = model_func(train_data, days_ahead=prediction_days)
                
                if pred is None or len(pred) == 0:
                    continue
                
                # Get actual values for the prediction period
                end_idx = min(i + prediction_days, len(df))
                actual_values = df.iloc[i:end_idx]['Close'].values[1:]  # Skip current day
                
                # Match lengths
                min_len = min(len(pred), len(actual_values))
                if min_len == 0:
                    continue
                
                predictions.extend(pred[:min_len])
                actuals.extend(actual_values[:min_len])
                dates.extend(df.index[i+1:i+1+min_len])
            except Exception as e:
                print(f"Prediction error at iteration {i}: {e}")
                continue
        
        print(f"Collected {len(predictions)} predictions")
        
        if len(predictions) < 5:  # Need at least a few predictions
            print(f"Too few predictions: {len(predictions)}")
            return None
        
        # Calculate metrics
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mape = mean_absolute_percentage_error(actuals, predictions) * 100
        
        # Directional accuracy (did we predict up/down correctly?)
        actual_direction = np.diff(actuals) > 0
        pred_direction = np.diff(predictions) > 0
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100 if len(actual_direction) > 0 else 0
        
        return {
            'model_name': model_name,
            'ticker': ticker,
            'predictions': predictions.tolist(),
            'actuals': actuals.tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'metrics': {
                'mae': round(float(mae), 2),
                'rmse': round(float(rmse), 2),
                'mape': round(float(mape), 2),
                'directional_accuracy': round(float(directional_accuracy), 2)
            }
        }
    
    except Exception as e:
        print(f"Backtest error for {model_name}: {e}")
        return None


def calculate_cumulative_returns(predictions, actuals, initial_capital=10000):
    """
    Calculate cumulative returns if you traded based on predictions
    
    Strategy: Buy if we predict price will go up, sell/stay out if down
    
    Args:
        predictions: Array of predicted prices
        actuals: Array of actual prices
        initial_capital: Starting capital ($)
    
    Returns:
        Dictionary with return metrics
    """
    try:
        if len(predictions) < 2 or len(actuals) < 2:
            return None
        
        capital = initial_capital
        shares = 0
        trades = []
        portfolio_values = [initial_capital]
        
        for i in range(len(predictions) - 1):
            # Predict direction
            predicted_return = (predictions[i + 1] - predictions[i]) / predictions[i]
            actual_price = actuals[i]
            next_actual_price = actuals[i + 1]
            
            # Trading logic
            if predicted_return > 0.01:  # Predict > 1% increase, buy
                if shares == 0 and capital > 0:
                    shares = capital / actual_price
                    capital = 0
                    trades.append({
                        'action': 'BUY',
                        'price': actual_price,
                        'shares': shares
                    })
            
            elif predicted_return < -0.01:  # Predict > 1% decrease, sell
                if shares > 0:
                    capital = shares * actual_price
                    trades.append({
                        'action': 'SELL',
                        'price': actual_price,
                        'shares': shares,
                        'capital': capital
                    })
                    shares = 0
            
            # Calculate portfolio value
            if shares > 0:
                portfolio_value = shares * next_actual_price
            else:
                portfolio_value = capital
            
            portfolio_values.append(portfolio_value)
        
        # Final liquidation
        if shares > 0:
            capital = shares * actuals[-1]
            shares = 0
        
        final_value = capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Buy and hold comparison
        buy_hold_shares = initial_capital / actuals[0]
        buy_hold_final = buy_hold_shares * actuals[-1]
        buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100
        
        return {
            'initial_capital': initial_capital,
            'final_value': round(float(final_value), 2),
            'total_return': round(float(total_return), 2),
            'buy_hold_return': round(float(buy_hold_return), 2),
            'outperformance': round(float(total_return - buy_hold_return), 2),
            'num_trades': len(trades),
            'portfolio_values': [round(float(v), 2) for v in portfolio_values]
        }
    
    except Exception as e:
        print(f"Cumulative return calculation error: {e}")
        return None


def compare_models(ticker, days_back=30):
    """
    Compare all available models on the same historical data
    
    Returns:
        Dictionary with comparison results for all models
    """
    try:
        # Download data once
        df = yf.download(ticker, period="1y", auto_adjust=False, progress=False)[['Close']].copy()
        
        if df.empty:
            return None
        
        models = [
            ('linear_regression', linear_regression_predict),
            ('random_forest', random_forest_predict),
            ('xgboost', xgboost_predict),
            ('ensemble', ensemble_predict)
        ]
        
        results = {}
        
        for model_name, model_func in models:
            backtest_result = backtest_model(ticker, model_func, model_name, days_back=days_back)
            
            if backtest_result:
                # Calculate returns
                returns = calculate_cumulative_returns(
                    backtest_result['predictions'],
                    backtest_result['actuals']
                )
                
                results[model_name] = {
                    'metrics': backtest_result['metrics'],
                    'returns': returns,
                    'predictions': backtest_result['predictions'],
                    'actuals': backtest_result['actuals'],
                    'dates': backtest_result['dates']
                }
        
        if not results:
            return None
        
        # Determine best model
        best_by_mae = min(results.items(), key=lambda x: x[1]['metrics']['mae'])[0]
        best_by_mape = min(results.items(), key=lambda x: x[1]['metrics']['mape'])[0]
        best_by_returns = max(
            results.items(),
            key=lambda x: x[1]['returns']['total_return'] if x[1]['returns'] else -999
        )[0] if any(r['returns'] for r in results.values()) else None
        
        return {
            'ticker': ticker,
            'models': results,
            'best_model': {
                'by_mae': best_by_mae,
                'by_mape': best_by_mape,
                'by_returns': best_by_returns
            },
            'comparison_period_days': days_back
        }
    
    except Exception as e:
        print(f"Model comparison error: {e}")
        return None


def evaluate_directional_accuracy(predictions, actuals):
    """
    Evaluate if the model correctly predicted the direction (up/down)
    
    Returns:
        Dictionary with directional accuracy metrics
    """
    try:
        if len(predictions) < 2 or len(actuals) < 2:
            return None
        
        # Calculate price changes
        pred_changes = np.diff(predictions)
        actual_changes = np.diff(actuals)
        
        # Direction (1 for up, 0 for down)
        pred_direction = pred_changes > 0
        actual_direction = actual_changes > 0
        
        # Accuracy
        correct = np.sum(pred_direction == actual_direction)
        total = len(pred_direction)
        accuracy = (correct / total) * 100
        
        # Breakdown
        correct_ups = np.sum((pred_direction == True) & (actual_direction == True))
        correct_downs = np.sum((pred_direction == False) & (actual_direction == False))
        false_ups = np.sum((pred_direction == True) & (actual_direction == False))
        false_downs = np.sum((pred_direction == False) & (actual_direction == True))
        
        return {
            'overall_accuracy': round(float(accuracy), 2),
            'correct_predictions': int(correct),
            'total_predictions': int(total),
            'breakdown': {
                'correct_ups': int(correct_ups),
                'correct_downs': int(correct_downs),
                'false_positives': int(false_ups),  # Predicted up, went down
                'false_negatives': int(false_downs)  # Predicted down, went up
            }
        }
    
    except Exception as e:
        print(f"Directional accuracy error: {e}")
        return None


if __name__ == "__main__":
    # Test the evaluation functions
    ticker = "AAPL"
    print(f"Running evaluation for {ticker}...")
    
    # Compare all models
    comparison = compare_models(ticker, days_back=30)
    
    if comparison:
        print("\n=== Model Comparison Results ===")
        for model_name, results in comparison['models'].items():
            print(f"\n{model_name.upper()}:")
            print(f"  MAE: ${results['metrics']['mae']}")
            print(f"  MAPE: {results['metrics']['mape']}%")
            print(f"  Directional Accuracy: {results['metrics']['directional_accuracy']}%")
            if results['returns']:
                print(f"  Total Return: {results['returns']['total_return']}%")
                print(f"  vs Buy & Hold: {results['returns']['buy_hold_return']}%")
        
        print(f"\n=== Best Models ===")
        print(f"Best by MAE: {comparison['best_model']['by_mae']}")
        print(f"Best by MAPE: {comparison['best_model']['by_mape']}")
        print(f"Best by Returns: {comparison['best_model']['by_returns']}")
