import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.ar_model import AutoReg

def create_dataset(period):
    data = yf.download("AAPL", period=period, auto_adjust=False)
    df = pd.DataFrame(data)
    df = df.drop(columns=["Adj Close", "High","Low", "Open", "Volume"])
    return df

def normalize_data(df):
    num_cols = ['Close']
    
    row_sum = df[num_cols].sum(axis=1)
    
    df[num_cols] = df[num_cols].div(row_sum, axis=0)
    
    return df

def test_today(df):
    today = df["Close"].iloc[-1].item()
    df = df.iloc[:-1]

    values = df['Close'].values
    lags = max(1, len(values)//4)
    model = AutoReg(values, lags=lags)
    model_fit = model.fit()

    next_day_pred = model_fit.predict(start=len(values), end=len(values))[0]

    return today, next_day_pred

def estimate_new(df, numdays=1):
    predictions = []

    for _ in range(numdays):
        values = df['Close'].values
        lags = max(1, len(values)//4)  # automatically choose lag
        model = AutoReg(values, lags=lags)
        model_fit = model.fit()

        # Predict next day
        next_day_pred = model_fit.predict(start=len(values), end=len(values))[0]
        next_date = df.index[-1] + pd.Timedelta(days=1)

        # Add prediction to DataFrame
        df.loc[next_date] = next_day_pred

        # Keep track of predictions
        predictions.append(next_day_pred)

    return next_day_pred

        

if __name__ == "__main__":
    dataset = create_dataset('10y')
    numdays = 31
    #next_day_estimate = estimate_new(dataset, numdays)
    #print(dataset.tail(10+numdays))
    #print(next_day_estimate)
    test = test_today(dataset)
    print("Expected: {}, Actual: {}".format(test[0], test[1]))

