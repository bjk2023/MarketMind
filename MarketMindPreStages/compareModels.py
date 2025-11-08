# ===== MODEL COMPARISON - MARKET MIND (EXCLUDING GARCH & XGBoost) =====
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load all prediction results
print("Loading prediction results...")

# Map of model names to their CSV files (excluding GARCH and XGBoost)
model_files = {
    'ARIMA': 'arima_predictions.csv',
    'LSTM': 'lstm_predictions.csv', 
    'Prophet': 'apple_forecast.csv',  # Adjust if needed
    'GRU': 'gru_predictions.csv',
    'Random Forest': 'random_forest_predictions.csv'
}

results = {}

for model_name, filename in model_files.items():
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            results[model_name] = df
            print(f"✓ Loaded {model_name}")
        else:
            print(f"✗ {filename} not found. Run the {model_name} model first.")
    except Exception as e:
        print(f"✗ Error loading {model_name}: {e}")

if not results:
    print("\nError: No prediction files found. Please run individual model scripts first.")
    exit()

# Calculate metrics for each model
print("\n" + "="*80)
print("MODEL COMPARISON RESULTS - MARKET MIND")
print("="*80)

metrics_data = []

for model_name, df in results.items():
    # Find actual and predicted columns
    actual_col = [col for col in df.columns if 'actual' in col.lower() or 'y' == col.lower()]
    pred_col = [col for col in df.columns if 'predict' in col.lower() or 'yhat' in col.lower()]
    
    if not actual_col or not pred_col:
        print(f"⚠ Skipping {model_name}: Cannot find actual/predicted columns")
        print(f"   Columns available: {df.columns.tolist()}")
        continue
    
    actual = df[actual_col[0]].values
    predicted = df[pred_col[0]].values
    
    # Make sure they're the same length
    min_len = min(len(actual), len(predicted))
    actual = actual[:min_len]
    predicted = predicted[:min_len]
    
    # Calculate metrics
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mae = np.mean(np.abs(actual - predicted))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    # Directional accuracy
    if len(actual) > 1:
        actual_direction = np.diff(actual) > 0
        pred_direction = np.diff(predicted) > 0
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
    else:
        directional_accuracy = 0
    
    metrics_data.append({
        'Model': model_name,
        'RMSE': rmse,
        'MAE': mae,
        'MAPE': mape,
        'Directional Accuracy (%)': directional_accuracy
    })

# Create comparison DataFrame
comparison_df = pd.DataFrame(metrics_data)
comparison_df = comparison_df.sort_values('RMSE')

print("\n" + comparison_df.to_string(index=False))
print("\n" + "="*80)

# Find best model for each metric
print("\n🏆 BEST MODELS:")
print(f"Lowest RMSE: {comparison_df.iloc[0]['Model']} ({comparison_df.iloc[0]['RMSE']:.4f})")
print(f"Lowest MAE: {comparison_df.loc[comparison_df['MAE'].idxmin()]['Model']} ({comparison_df['MAE'].min():.4f})")
print(f"Lowest MAPE: {comparison_df.loc[comparison_df['MAPE'].idxmin()]['Model']} ({comparison_df['MAPE'].min():.2f}%)")
print(f"Highest Directional Accuracy: {comparison_df.loc[comparison_df['Directional Accuracy (%)'].idxmax()]['Model']} ({comparison_df['Directional Accuracy (%)'].max():.2f}%)")

# Save comparison results
comparison_df.to_csv('model_comparison_results.csv', index=False)
print(f"\n💾 Comparison saved to 'model_comparison_results.csv'")

# Visualize comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# RMSE Comparison
axes[0, 0].bar(comparison_df['Model'], comparison_df['RMSE'], color='steelblue')
axes[0, 0].set_title('RMSE Comparison (Lower is Better)', fontweight='bold', fontsize=12)
axes[0, 0].set_ylabel('RMSE', fontsize=10)
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].grid(True, alpha=0.3, axis='y')

# MAE Comparison
axes[0, 1].bar(comparison_df['Model'], comparison_df['MAE'], color='coral')
axes[0, 1].set_title('MAE Comparison (Lower is Better)', fontweight='bold', fontsize=12)
axes[0, 1].set_ylabel('MAE', fontsize=10)
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# MAPE Comparison
axes[1, 0].bar(comparison_df['Model'], comparison_df['MAPE'], color='lightgreen')
axes[1, 0].set_title('MAPE Comparison (Lower is Better)', fontweight='bold', fontsize=12)
axes[1, 0].set_ylabel('MAPE (%)', fontsize=10)
axes[1, 0].tick_params(axis='x', rotation=45)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Directional Accuracy Comparison
axes[1, 1].bar(comparison_df['Model'], comparison_df['Directional Accuracy (%)'], color='mediumpurple')
axes[1, 1].set_title('Directional Accuracy (Higher is Better)', fontweight='bold', fontsize=12)
axes[1, 1].set_ylabel('Accuracy (%)', fontsize=10)
axes[1, 1].tick_params(axis='x', rotation=45)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
print("📊 Visualization saved to 'model_comparison.png'")
plt.show()

print("\n✅ Comparison complete!")
