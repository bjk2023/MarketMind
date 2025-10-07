import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.ar_model import AutoReg


#Creating a dataset based on ticker and period
def create_dataset(ticker, period):
    data = yf.download(ticker, period=period, auto_adjust=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    df = data[['Close']].copy()
    df.index = pd.to_datetime(df.index)
    return df

#Testing model on todays value - removing last row and predicting it to compare
def test_today(df):
    today = pd.Timestamp.today().normalize()
    new_df = estimate_new(df, today - pd.Timedelta(days=1))

    return today, new_df["Close"].iloc[-1].item(), new_df["Predicted"].iloc[-1].item()

#Estimating next day(s) value based on previous values
def estimate_new(df, startdays, numdays=1):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df["Predicted"] = np.nan
    df_subset = df.loc[:startdays + pd.Timedelta(days=1)]

    for _ in range(numdays):
        values = df_subset["Predicted"].fillna(df_subset["Close"]).dropna().values

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

#Evaluating the model using Mean Absolute Error (MAE)
def good_model(df_actual, df_predicted):
    mae = (df_actual['Close'] - df_predicted['Close']).abs().mean().item()
    avg_daily_change = df_actual['Close'].diff().abs().mean().item()
    print("Mean Absolute Error (MAE): ", mae)
    print("Average Daily Change: ", avg_daily_change)
    if mae < avg_daily_change:
        return True
    return False

if __name__ == "__main__":
    #Variables
    tickers = ['GOOGL','AAPL', 'MSFT', 'AMZN']
    period = '5y'

    #Stock loop
    for ticker in tickers:
        #Create Dataset
        dataset = create_dataset(ticker, period)

        print("Stock for {} in {} period: \n".format(ticker, period))

        #Test model on todays value based on past 5 days
        data_past_five = dataset.iloc[len(dataset)-6:]
        df_new = test_today(data_past_five)
        print("Todays estimate based on past 5 days\nDate: {}, Expected: {}, Actual: {}\n".format(df_new[0], df_new[1], df_new[2]))

        """#Test model on todays value based on all previous values
        test = test_today(dataset)
        print("Todays estimate based on all previous values\nDate: {}, Expected: {}, Actual: {}\n".format(test[0], test[1], test[2]))

        #Estimate next 5 days based on past 5 days
        new_df = estimate_new(data_past_five, numdays=5)
        result = new_df.iloc[-5:]
        print("Next 5 days estimate based on past 5 days\n", result)

        #Estimate next 5 days based on all previous values
        new_df = estimate_new(dataset, numdays=5)
        result = new_df.iloc[-5:]
        print("Next 5 days estimate based on all previous values\n", result)

        #Estimate past 5 days based on all previous values and compare
        new_df = estimate_new(dataset.iloc[:-5], numdays=5)
        print("Next 5 days estimate based on all previous values\n")
        print("Estimated Values:\n", new_df.iloc[-5:])
        print("Actual Values:\n", dataset.iloc[-5:])

        #Evaulating the model using Mean Absolute Error (MAE)
        if good_model(dataset.iloc[-5:], new_df.iloc[-5:]):
            print("\nModel is good\n")
        else:
            print("\nModel is not good\n")"""