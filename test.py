import yfinance as yf
import pandas as pd
from statsmodels.tsa.ar_model import AutoReg


#Creating a dataset based on ticker and period
def create_dataset(ticker, period):
    data = yf.download(ticker, period=period, auto_adjust=False)
    df = pd.DataFrame(data)
    df = df.drop(columns=["Adj Close", "High","Low", "Open", "Volume"])
    return df

#Testing model on todays value - removing last row and predicting it to compare
def test_today(df):
    date = df.index[-1]
    today_value = df["Close"].iloc[-1].item()
    df = df.iloc[:-1]

    new_df = estimate_new(df, numdays=1)

    return date, today_value, new_df["Close"].iloc[-1].item()

#Estimating next day(s) value based on previous values
def estimate_new(df, numdays=1):
    predictions = []
    df_new = df.copy()

    for _ in range(numdays):
        values = df_new['Close'].values
        lags = 1
        model = AutoReg(values, lags=lags)
        model_fit = model.fit()

        next_day_pred = model_fit.predict(start=len(values), end=len(values))[0]
        next_date = df_new.index[-1] + pd.Timedelta(days=1)

        df_new.loc[next_date] = next_day_pred

        predictions.append(next_day_pred)

    return df_new

if __name__ == "__main__":
    #Create Dataset
    dataset = create_dataset('AAPL', '100y')
    print(dataset.tail(5))
    print(len(dataset))

    #Test model on todays value based on past 5 days
    data_past_five = dataset.iloc[len(dataset)-5:len(dataset)]
    test = test_today(data_past_five)
    print("Date: {}, Expected: {}, Actual: {}".format(test[0], test[1], test[2]))

    #Test model on todays value based on all previous values
    test = test_today(dataset)
    print("Date: {}, Expected: {}, Actual: {}".format(test[0], test[1], test[2]))

    #Estimate next 5 days based on past 5 days
    new_df = estimate_new(data_past_five, numdays=5)
    print(new_df.iloc[len(new_df)-5:])

    #Estimate next 5 days based on all previous values
    new_df = estimate_new(dataset, numdays=5)
    print(new_df.iloc[len(new_df)-5:])