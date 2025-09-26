import yfinance as yf
import requests
from datetime import datetime
# --- Step 1: Get current stock price ---
def get_stock_price(ticker: str):
    stock = yf.Ticker(ticker)
    current_price = stock.history(period="1d")["Close"].iloc[-1]
    return current_price

# --- Step 2: Get latest inflation rate ---
def get_inflation_rate():
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-type": "application/json"}

    # Replace with your key if you have one
    payload = {
        "seriesid": ["CUSR0000SA0"],
        "startyear": str(datetime.now().year - 1),
        "endyear": str(datetime.now().year),
        "registrationkey": "bf711ecb4dfd45019ccf1d4d48a052e6"  # optional
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    series_data = data["Results"]["series"][0]["data"]

    # Latest month
    latest = float(series_data[0]["value"])
    latest_month = series_data[0]["periodName"], series_data[0]["year"]

    # Same month last year
    for entry in series_data:
        if entry["periodName"] == series_data[0]["periodName"] and entry["year"] == str(datetime.now().year - 1):
            prev_year = float(entry["value"])
            break

    # Compute YoY inflation
    inflation_rate = (latest - prev_year) / prev_year * 100
    return inflation_rate

# --- Step 3: Predict next month price ---
def predict_next_month_price(current_price, inflation_rate):
    # Simplified model: adjust proportionally by monthly inflation
    monthly_inflation = inflation_rate / 12 / 100
    predicted_price = current_price * (1 + monthly_inflation)
    return predicted_price

# --- Example run ---
if __name__ == "__main__":
    stock=input("Enter stock ticker: ")
    ticker = "AAPL"  # Example: Apple
    current_price = get_stock_price(stock)
    inflation_rate = get_inflation_rate()
    predicted_price = predict_next_month_price(current_price, inflation_rate)
    print("inflation_rate", inflation_rate)
    print("current_price", current_price)
    print(f"Current {stock} Price: ${current_price:.2f}")
    print(f"Inflation Rate: {inflation_rate:.2f}% annual")
    print(f"Predicted Price in 1 Month: ${predicted_price:.2f}")
    #first step to show graph would be to get more data points/ calulate on smaller incre,=ments but for now this works