import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import warnings
warnings.filterwarnings('ignore')


def simple_backtest(ticker, days_back=30):
    """
    Simple backtest: Train models on all data ONCE, then test on recent history
    This avoids feature shape mismatches from retraining
    
    Returns actual vs predicted comparison
    """
    try:
        # Get full historical data
        df_full = yf.download(ticker, period="1y", auto_adjust=False, progress=False)[['Close']].copy()
        
        if df_full.empty or len(df_full) < days_back + 30:
            return None
        
        # Split: everything except last days_back is training, last days_back is testing
        test_start = len(df_full) - days_back
        test_data = df_full.iloc[test_start:]
        
        # Import prediction functions
        from model import create_dataset, estimate_week
        
        # Get predictions from the main model (AutoReg based)
        # This is what we're currently using in production
        train_df = create_dataset(ticker, period="1y")
        
        if train_df.empty:
            return None
        
        # Use the existing estimate_week function which predicts 7 days
        # We'll do this multiple times to cover the test period
        all_predictions = []
        all_actuals = []
        all_dates = []
        
        # Predict in weekly chunks
        current_date = test_data.index[0]
        while current_date < test_data.index[-1]:
            # Get data up to current_date for prediction
            historical = df_full[df_full.index < current_date]
            
            if len(historical) < 30:
                break
            
            try:
                # Use existing model to predict next 7 days
                predicted_df = estimate_week(historical)
                pred_values = predicted_df["Predicted"].dropna().values
                
                # Get actual values for comparison
                future_dates = test_data[test_data.index >= current_date].index[:len(pred_values)]
                actual_values = test_data.loc[future_dates, 'Close'].values
                
                min_len = min(len(pred_values), len(actual_values))
                if min_len > 0:
                    all_predictions.extend(pred_values[:min_len])
                    all_actuals.extend(actual_values[:min_len])
                    all_dates.extend(future_dates[:min_len])
                
                # Move forward by 7 days
                current_date = current_date + pd.Timedelta(days=7)
            except Exception as e:
                print(f"Prediction error: {e}")
                break
        
        if len(all_predictions) < 5:
            return None
        
        # Calculate metrics
        predictions = np.array(all_predictions)
        actuals = np.array(all_actuals)
        
        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mape = mean_absolute_percentage_error(actuals, predictions) * 100
        
        # Directional accuracy
        if len(predictions) > 1:
            pred_direction = np.diff(predictions) > 0
            actual_direction = np.diff(actuals) > 0
            directional_accuracy = np.mean(pred_direction == actual_direction) * 100
        else:
            directional_accuracy = 0
        
        # Calculate returns
        returns_data = calculate_simple_returns(predictions, actuals)
        
        return {
            'ticker': ticker,
            'model_name': 'autoregressive',
            'predictions': predictions.tolist(),
            'actuals': actuals.tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in all_dates],
            'metrics': {
                'mae': round(float(mae), 2),
                'rmse': round(float(rmse), 2),
                'mape': round(float(mape), 2),
                'directional_accuracy': round(float(directional_accuracy), 2)
            },
            'returns': returns_data
        }
    
    except Exception as e:
        print(f"Backtest error: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_simple_returns(predictions, actuals, initial_capital=10000):
    """
    Calculate trading returns based on predictions
    """
    try:
        if len(predictions) < 2:
            return None
        
        capital = initial_capital
        shares = 0
        portfolio_values = [initial_capital]
        
        for i in range(len(predictions) - 1):
            # Trading logic based on prediction
            pred_return = (predictions[i + 1] - predictions[i]) / predictions[i]
            actual_price = actuals[i]
            next_price = actuals[i + 1] if i + 1 < len(actuals) else actuals[i]
            
            # Buy if predict >0.5% increase
            if pred_return > 0.005 and shares == 0:
                shares = capital / actual_price
                capital = 0
            # Sell if predict >0.5% decrease
            elif pred_return < -0.005 and shares > 0:
                capital = shares * actual_price
                shares = 0
            
            # Portfolio value
            portfolio_value = capital + (shares * next_price)
            portfolio_values.append(portfolio_value)
        
        # Final liquidation
        if shares > 0:
            capital = shares * actuals[-1]
        
        total_return = ((capital - initial_capital) / initial_capital) * 100
        
        # Buy and hold
        buy_hold_final = (initial_capital / actuals[0]) * actuals[-1]
        buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100
        
        return {
            'initial_capital': initial_capital,
            'final_value': round(float(capital), 2),
            'total_return': round(float(total_return), 2),
            'buy_hold_return': round(float(buy_hold_return), 2),
            'outperformance': round(float(total_return - buy_hold_return), 2),
            'portfolio_values': [round(float(v), 2) for v in portfolio_values]
        }
    
    except Exception as e:
        print(f"Returns calculation error: {e}")
        return None


if __name__ == "__main__":
    # Test
    result = simple_backtest("AAPL", days_back=30)
    if result:
        print(f"\n=== Backtest Results for AAPL ===")
        print(f"MAE: ${result['metrics']['mae']}")
        print(f"MAPE: {result['metrics']['mape']}%")
        print(f"Directional Accuracy: {result['metrics']['directional_accuracy']}%")
        if result['returns']:
            print(f"Total Return: {result['returns']['total_return']}%")
            print(f"Buy & Hold: {result['returns']['buy_hold_return']}%")
            print(f"Outperformance: {result['returns']['outperformance']}%")
