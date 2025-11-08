# ===== RANDOM FOREST MODEL - MARKET MIND =====
import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt

# Download Apple stock data
print("Downloading stock data...")
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", auto_adjust=True)
close_prices = data['Close']

# Split into train/test (80/20)
train_size = int(len(close_prices) * 0.8)
train, test = close_prices[:train_size], close_prices[train_size:]

print(f"Train size: {len(train)}, Test size: {len(test)}")

# Create features
def create_features(data, lag=10):
    """Create lagged features and technical indicators"""
    df = pd.DataFrame(data)
    df.columns = ['price']
    
    # Lagged values
    for i in range(1, lag + 1):
        df[f'lag_{i}'] = df['price'].shift(i)
    
    # Moving averages
    df['MA_5'] = df['price'].rolling(window=5).mean()
    df['MA_10'] = df['price'].rolling(window=10).mean()
    df['MA_20'] = df['price'].rolling(window=20).mean()
    
    # Exponential moving average
    df['EMA_5'] = df['price'].ewm(span=5).mean()
    
    # Standard deviation (volatility)
    df['std_5'] = df['price'].rolling(window=5).std()
    df['std_10'] = df['price'].rolling(window=10).std()
    
    # Rate of change
    df['ROC'] = df['price'].pct_change(periods=5)
    
    # Momentum
    df['momentum'] = df['price'] - df['price'].shift(4)
    
    df = df.dropna()
    return df

# Prepare training data
print("\n--- Preparing Features ---")
df_train = create_features(train, lag=10)
X_train = df_train.drop('price', axis=1)
y_train = df_train['price']

# Prepare test data (need overlapping data for lags)
overlap_data = pd.concat([train.tail(20), test])
df_test = create_features(overlap_data, lag=10)
df_test = df_test.iloc[20:]  # Remove overlapping rows

X_test = df_test.drop('price', axis=1)
y_test = df_test['price']

print(f"Training features shape: {X_train.shape}")
print(f"Test features shape: {X_test.shape}")

# Train Random Forest model
print("\n--- Training Random Forest ---")
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

model.fit(X_train, y_train)

# Make predictions
forecast = model.predict(X_test)
forecast = pd.Series(forecast, index=y_test.index)

# Evaluate
rmse = sqrt(mean_squared_error(y_test, forecast))
mae = mean_absolute_error(y_test, forecast)
mape = np.mean(np.abs((y_test - forecast) / y_test)) * 100

# Calculate directional accuracy
actual_direction = np.diff(y_test) > 0
pred_direction = np.diff(forecast) > 0
directional_accuracy = np.mean(actual_direction == pred_direction) * 100

print("\n=== Random Forest Results ===")
print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"MAPE: {mape:.2f}%")
print(f"Directional Accuracy: {directional_accuracy:.2f}%")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n=== Top 10 Most Important Features ===")
print(feature_importance.head(10))

# Plot results
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Forecast plot
axes[0].plot(y_test.index, y_test, label='Actual', linewidth=2)
axes[0].plot(y_test.index, forecast, color='red', label='Random Forest Predicted', linewidth=2)
axes[0].set_title("Apple Stock Forecast - Random Forest Model", fontsize=14, fontweight='bold')
axes[0].set_xlabel("Date")
axes[0].set_ylabel("Price ($)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Feature importance plot
axes[1].barh(feature_importance['feature'][:10], feature_importance['importance'][:10])
axes[1].set_title("Top 10 Feature Importances", fontsize=14, fontweight='bold')
axes[1].set_xlabel("Importance")
axes[1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('random_forest_forecast.png', dpi=300, bbox_inches='tight')
plt.show()

# Save predictions to CSV
results_df = pd.DataFrame({
    'Date': y_test.index,
    'Actual': y_test.values,
    'Predicted': forecast.values
})
results_df.to_csv('random_forest_predictions.csv', index=False)

# Save feature importance
feature_importance.to_csv('random_forest_feature_importance.csv', index=False)

print("\nPredictions saved to 'random_forest_predictions.csv'")
print("Feature importance saved to 'random_forest_feature_importance.csv'")
print("Plot saved to 'random_forest_forecast.png'")