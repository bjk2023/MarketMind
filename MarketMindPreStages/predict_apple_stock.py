from prophet import Prophet #For time series forecasting
import yfinance as yf #For downloading stock data
import pandas as pd #For data manipulation
import matplotlib.pyplot as plt #For plotting

#Download Apple stock data
data = yf.download("AAPL", start="2022-01-01", end="2025-01-01", group_by="ticker", auto_adjust=True)

#Flatten MultiIndex columns
data.columns = ['_'.join(col).strip() for col in data.columns.values]

#Prepare dataframe for Prophet
df = data.reset_index()[['Date', 'AAPL_Close']]
df.rename(columns={'Date': 'ds', 'AAPL_Close': 'y'}, inplace=True)

df['ds'] = pd.to_datetime(df['ds']) #Ensure datetime format
df['y'] = pd.to_numeric(df['y'], errors='coerce') #Ensure numeric format


#Initialize and fit Prophet
model = Prophet(daily_seasonality=True) #Enable daily seasonality
model.fit(df) # Fit model

#Forecast 30 days ahead
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

fig1 = model.plot(forecast)
fig1.savefig("apple_forecast.png")
fig2 = model.plot_components(forecast)
fig2.savefig("apple_forecast_components.png")
forecast.to_csv("apple_forecast.csv", index=False)
