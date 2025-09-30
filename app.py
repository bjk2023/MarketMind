from flask import Flask, render_template, request
from src.stock_visualizer import create_stock_chart
from plotly.utils import PlotlyJSONEncoder
import json
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    graph_json = None
    error_message = None
    ticker = "AAPL"
    start_date = (pd.to_datetime('today') - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    end_date = pd.to_datetime('today').strftime('%Y-%m-%d')

    if request.method == 'POST':
        ticker = request.form.get('ticker')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not ticker:
            error_message = "Please enter a stock ticker."
        else:
            try:
                fig = create_stock_chart(ticker, start_date=start_date, end_date=end_date)
                graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
            except Exception as e:
                error_message = f"Error: Could not retrieve data for '{ticker}'. Please check the ticker and try again."
                print(f"Error generating chart: {e}")

    # For the initial GET request, generate a default chart
    if request.method == 'GET':
        try:
            fig = create_stock_chart(ticker, start_date=start_date, end_date=end_date)
            graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        except Exception as e:
            error_message = "Could not load default chart for AAPL. Please check your connection."
            print(f"Error generating default chart: {e}")

    return render_template('index.html', graph_json=graph_json, error_message=error_message, ticker=ticker, start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    app.run(debug=True)
