import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter

def fetch_stock_data(ticker, start_date, end_date):
    """
    Fetch historical stock data using yfinance for a specific date range.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL').
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        
    Returns:
        pd.DataFrame: DataFrame containing the stock data.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval='1d')
        
        # Check if data was returned
        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
            
        # Clean the data
        df = df.dropna()
        
        # Ensure we have enough data points
        if len(df) < 5:
            raise ValueError(f"Insufficient data points for analysis. Only {len(df)} days of data available.")
            
        return df
        
    except Exception as e:
        raise Exception(f"Error fetching data for {ticker}: {str(e)}")

def create_stock_chart(ticker, start_date, end_date):
    """
    Create an interactive stock price chart for a specific date range.
    
    Args:
        ticker (str): Stock ticker symbol.
        start_date (str): Start date for the data.
        end_date (str): End date for the data.
    """
    df = fetch_stock_data(ticker, start_date, end_date)
    
    # Add smoothed price line using Savitzky-Golay filter
    window_size = min(30, len(df))  # Ensure window size is not larger than data
    if window_size > 4:  # Need at least 5 points for smoothing
        df['Close_Smooth'] = savgol_filter(df['Close'], 
                                         window_length=window_size, 
                                         polyorder=2, 
                                         mode='nearest')
    
    # Create figure with secondary y-axis for volume
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} Stock Price', 'Trading Volume')
    )
    
    # Candlestick chart with smoother appearance
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#2ecc71',  # Green for up
            decreasing_line_color='#e74c3c',  # Red for down
            increasing_fillcolor='rgba(46, 204, 113, 0.4)',
            decreasing_fillcolor='rgba(231, 76, 60, 0.4)',
            line=dict(width=0.8),
            opacity=0.9
        ),
        row=1, col=1
    )
    
    # Add smoothed price line
    if 'Close_Smooth' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Close_Smooth'],
                name='Trend',
                line=dict(color='#3498db', width=3),
                opacity=0.8,
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Smoothed volume with gradient
    colors = ['#2ecc71' if close >= open_ else '#e74c3c' 
              for close, open_ in zip(df['Close'], df['Open'])]
    
    # Add volume bars with hover info
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6,
            marker_line_width=0,
            hovertemplate='Volume: %{y:,.0f}<extra></extra>',
            hoverlabel=dict(bgcolor='rgba(0,0,0,0.8)')
        ),
        row=2, col=1
    )
    
    # Add smoothed volume line
    if len(df) > 5:  # Ensure enough points for smoothing
        df['Volume_Smooth'] = savgol_filter(df['Volume'], 
                                          window_length=min(15, len(df)), 
                                          polyorder=2,
                                          mode='nearest')
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Volume_Smooth'],
                name='Volume Trend',
                line=dict(color='#9b59b6', width=2),
                opacity=0.8,
                hovertemplate='%{y:,.0f}<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )
    
    # Update layout with smoother transitions and better styling
    fig.update_layout(
        title=dict(
            text=f'<b>{ticker}</b> Stock Analysis ({start_date} to {end_date})',
            font=dict(size=20, family='Arial, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        template='plotly_dark',
        showlegend=False,
        height=850,
        hovermode='x unified',
        xaxis2_rangeslider_visible=False,
        xaxis2_type='date',
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        paper_bgcolor='rgba(0,0,0,0.9)',
        plot_bgcolor='rgba(0,0,0,0.1)',
        margin=dict(l=60, r=40, t=100, b=60),
        transition_duration=500,
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.8)',
            font_size=12,
            font_family='Arial, sans-serif'
        ),
        updatemenus=[
            dict(
                type='buttons',
                showactive=False,
                x=1.1,
                y=1.15,
                xanchor='right',
                yanchor='top',
                buttons=[
                    dict(
                        label='Play',
                        method='animate',
                        args=[None, {
                            'frame': {'duration': 100, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 100}
                        }]
                    )
                ]
            )
        ],
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#2c3e50',
            rangeslider_visible=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#2c3e50',
            showline=True,
            linewidth=1,
            linecolor='#2c3e50',
            title='Price ($)'
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#2c3e50',
            title='Volume'
        )
    )
    
    # Add moving averages with better styling
    ma_windows = [20, 50, 200]  # Common moving average periods
    ma_colors = ['#f1c40f', '#e67e22', '#e74c3c']  # Yellow, Orange, Red
    
    for window, color in zip(ma_windows, ma_colors):
        if len(df) >= window:  # Only add if enough data points
            df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[f'SMA_{window}'],
                    name=f'SMA {window}',
                    line=dict(
                        width=2.5,
                        dash='solid' if window == 200 else 'dash',
                        color=color
                    ),
                    opacity=0.9,
                    hovertemplate=f'SMA {window}: %{{y:.2f}}<extra></extra>',
                    visible='legendonly' if window != 20 else True
                ),
                row=1, col=1
            )
    
    # Add volume moving average
    df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Volume_MA20'],
            name='Volume MA 20',
            line=dict(color='#3498db', width=1.5),
            opacity=0.8
        ),
        row=2, col=1
    )
    
    # Enhanced range selector with more options
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='#2c3e50',
            borderwidth=1,
            buttons=list([
                dict(count=1, label='1M', step='month', stepmode='backward'),
                dict(count=3, label='3M', step='month', stepmode='backward'),
                dict(count=6, label='6M', step='month', stepmode='backward'),
                dict(count=1, label='YTD', step='year', stepmode='todate'),
                dict(count=1, label='1Y', step='year', stepmode='backward'),
                dict(count=2, label='2Y', step='year', stepmode='backward'),
                dict(count=5, label='5Y', step='year', stepmode='backward'),
                dict(step='all', label='ALL')
            ]),
            font=dict(color='#ecf0f1'),
            activecolor='#3498db',
            y=1.1
        )
    )
    
    # Add range slider at the bottom
    fig.update_layout(
        xaxis2=dict(
            rangeselector=dict(visible=False),
            rangeslider=dict(
                visible=True,
                thickness=0.05,
                bgcolor='rgba(52, 152, 219, 0.2)',
                bordercolor='#2c3e50',
                borderwidth=1
            ),
            type='date'
        )
    )
    
    return fig

if __name__ == "__main__":
    # Example usage with error handling
    try:
        ticker = "AAPL"  # You can change this to any stock symbol
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        print(f"Fetching {ticker} data from {start_date} to {end_date}...")
        fig = create_stock_chart(ticker, start_date=start_date, end_date=end_date)
        
        # Show the figure
        fig.show(config={
            'scrollZoom': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': [
                'select2d',
                'lasso2d',
                'zoomIn',
                'zoomOut',
                'autoScale',
                'resetScale',
                'toImage',
                'toggleSpikelines',
                'hoverClosestCartesian',
                'hoverCompareCartesian'
            ]
        })
        
        print("Visualization complete! Check your default web browser.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your internet connection and try again.")
