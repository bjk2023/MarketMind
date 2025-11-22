import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.ar_model import AutoReg
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


#Creating a dataset based on ticker and period
def create_dataset(ticker, period):
    try:
        data = yf.download(ticker, period=period, auto_adjust=False)
    except Exception as e:
        print(f"[Warning] Could not download data for {ticker}: {e}")
        return pd.DataFrame()
    df = data[['Close']].copy()
    df.index = pd.to_datetime(df.index)
    return df

#Testing model on todays value - removing last row and predicting it to compare
def try_today(df):
    today = pd.Timestamp.today().normalize()
    new_df = estimate_rf_new(df, today - pd.Timedelta(days=1))
    
    return new_df.tail(1)

def estimate_this_week(df):
    last_valid_index = df['Close'].last_valid_index()
    if find_best_model(df) == "rf":
        new_df = estimate_rf_new(df, last_valid_index - pd.Timedelta(days=1), numdays=7)
    else:
        new_df = estimate_ar_new(df, last_valid_index - pd.Timedelta(days=1), numdays=7)
    last_valid_index = new_df['Close'].last_valid_index()

    return new_df.loc[last_valid_index:]

#Estimating next day(s) value based on previous values
def estimate_ar_new(df, startdays, numdays=1):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df["Predicted"] = np.nan
    df_subset = df.loc[:startdays + pd.Timedelta(days=1)]

    for _ in range(numdays):
        values = df_subset["Predicted"].fillna(df_subset["Close"].squeeze()).dropna().values

        lags = 1
        model = AutoReg(values, lags=lags)
        model_fit = model.fit()

        next_day_pred = model_fit.predict(start=len(values), end=len(values))[0]
        next_date = startdays + pd.Timedelta(days=1)

        if next_date in df.index:
            df.loc[next_date, "Predicted"] = next_day_pred
        else:
            df.loc[next_date] = [np.nan, next_day_pred]

        df_subset = df.loc[df.index <= next_date]
        startdays = startdays + pd.Timedelta(days=1)
    return df

def estimate_rf_new(df, startdays, numdays=1): 
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df["Predicted"] = np.nan
    df_subset = df.loc[:startdays]

    for _ in range(numdays):
        values = df_subset["Predicted"].fillna(df_subset["Close"].squeeze()).dropna().values

        lags = 1

        X_train, y_train = [], []
        for i in range(lags, len(values)):
            X_train.append(values[i-lags:i])
            y_train.append(values[i])
        X_train, y_train = np.array(X_train), np.array(y_train)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train) 

        last_values = values[-lags:].reshape(1, -1)
        next_day_pred = model.predict(last_values)[0]
        next_date = df_subset.index[-1] + pd.Timedelta(days=1)

        if next_date in df.index:
            df.loc[next_date, "Predicted"] = next_day_pred
        else:
            df.loc[next_date] = [np.nan, next_day_pred]

        df_subset = df.loc[df.index <= next_date]
        startdays = startdays + pd.Timedelta(days=1)
    return df

def find_best_model(df):
    df = df.copy()
    today = pd.Timestamp.today().normalize()
    rf_df = estimate_rf_new(df, today - pd.Timedelta(days=1)).loc[today]
    ar_df = estimate_ar_new(df, today - pd.Timedelta(days=1)).loc[today]

    rf_difference = abs(rf_df['Close'].values[0] - rf_df['Predicted'].values[0])
    ar_difference = abs(ar_df['Close'].values[0] - ar_df['Predicted'].values[0])

    if rf_difference < ar_difference:
        return "rf"
    else:
        return "ar"


#Evaluating the model using Mean Absolute Error (MAE)
def good_model(df_predicted):
    mae = (df_predicted['Close'] - df_predicted['Predicted']).abs().mean().item()
    avg_daily_change = df_predicted['Close'].dropna().diff().abs().mean().item()
    print("Mean Absolute Error (MAE): ", mae)
    print("Average Daily Change: ", avg_daily_change)
    if mae < avg_daily_change:
        return True
    return False

if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"
    period = "1mo"
    df = create_dataset(ticker, period)
    df1 = estimate_this_week(df)
    print(df1)
    print(df1.tail(7))
    last_valid_index = df['Close'].last_valid_index()
    print(df1.loc[last_valid_index]['Close'].item())
    print(df1["Predicted"].iloc[0])