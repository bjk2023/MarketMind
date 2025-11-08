from model import create_dataset, try_today, estimate_this_week, estimate_new, good_model
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import yfinance as yf

#Sample data for testing
@pytest.fixture
def sample_data():
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "Close": [100.0, 101.0, 102.0, 103.0, 104.0],
    }, index=dates)
    return df

#Sample data for testing
@pytest.fixture
def messy_data():
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "Close": [222.0, 302.0, 1.0, 736.0, 2.0],
    }, index=dates)
    return df

@patch("yfinance.download")
def test_create_dataset(mock_download, sample_data):
    #Valid ticker test
    mock_download.return_value = sample_data
    df = create_dataset('AAPL', '1y')

    assert df is not None, "Returned value should not be None"
    assert not df.empty, "Dataset should not be empty"
    assert 'Close' in df.columns, "Dataset should contain 'Close' column"

    #Invalid ticker test
    mock_download.side_effect = Exception("Data not found")
    result = create_dataset("FAKE", "1y")

    assert result.empty 

@patch("yfinance.download")
def test_try_today(mock_download, sample_data):
    mock_download.return_value = sample_data
    df = create_dataset('AAPL', '1y')
    result = try_today(df)

    assert not result.empty, "Result should not be empty"
    assert 'Predicted' in result.columns, "Result should contain 'Predicted' column"
    assert len(result) == 1, "Result should contain exactly one row"

@patch("yfinance.download")
def test_estimate_this_week(mock_download, sample_data):
    mock_download.return_value = sample_data
    df = sample_data
    result = estimate_this_week(df)

    assert not result.empty, "Result should not be empty"
    assert 'Predicted' in result.columns, "Result should contain 'Predicted' column"
    assert len(result['Predicted']) == 7, "Predicted result should have exactly 7 non-NA values"

@patch("yfinance.download")
def test_estimate_new(mock_download, sample_data):
    mock_download.return_value = sample_data
    df = sample_data
    start_date = df.index[-2]
    result = estimate_new(df, start_date, numdays=2)

    assert not result.empty, "Result should not be empty"
    assert 'Predicted' in result.columns, "Result should contain 'Predicted' column"
    assert len(result['Predicted'].dropna()) >= 2, "There should be at least 2 predicted values"

@patch("yfinance.download")
def test_good_model_good(mock_download, sample_data):
    mock_download.return_value = sample_data
    df_actual = sample_data

    df_predicted = estimate_new(df_actual, df_actual.index[3], numdays=12)

    print(df_actual)
    print("_______")
    print(df_predicted)

    is_good = good_model(df_actual, df_predicted)
    assert isinstance(is_good, bool), "The result should be a boolean value"
    assert is_good, "The model should be considered good with low MAE"

@patch("yfinance.download")
def test_good_model_bad(mock_download, messy_data):
    mock_download.return_value = messy_data
    df_actual = messy_data

    df_predicted = estimate_new(df_actual, df_actual.index[3], numdays=12)

    print(df_actual)
    print("_______")
    print(df_predicted)

    is_good = good_model(df_actual, df_predicted)
    assert isinstance(is_good, bool), "The result should be a boolean value"
    assert not is_good, "The model should be considered bad with high MAE"

if __name__ == "__main__":
    test_create_dataset()
    test_try_today()