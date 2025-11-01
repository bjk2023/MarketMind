from model import create_dataset, try_today, estimate_new, good_model
import yfinance as yf

def test_create_dataset():
    # Test for a valid stock symbol
    df = create_dataset('AAPL', '1y')
    assert df is not None, "Returned value should not be None"
    assert not df.empty, "Dataset should not be empty"
    assert 'Close' in df.columns, "Dataset should contain 'Close' column"

def test_try_today():
    # Create a sample dataset
    df = create_dataset('AAPL', '1y')

    result = try_today(df)
    assert not result.empty, "Result should not be empty"
    assert 'Close' in result.columns, "Result should contain 'Close' column"

def test_good_model():
    df_actual = create_dataset('AAPL', '1y').tail(5)
    df_predicted = df_actual.copy()
    df_predicted['Close'] = df_actual['Close'] * 0.95

    is_good = good_model(df_actual, df_predicted)
    assert isinstance(is_good, bool), "The result should be a boolean value"

if __name__ == "__main__":
    test_create_dataset()
    test_try_today()
    test_good_model()