from model import create_dataset, test_today, estimate_new, good_model
import pytest

def test_create_dataset():
    # Test for a valid stock symbol
    df = create_dataset('AAPL', '1y')
    assert df is not None, "Returned value should not be None"
    assert not df.empty, "Dataset should not be empty"
    assert 'Close' in df.columns, "Dataset should contain 'Close' column"

    # Test for an invalid or non-existent stock symbol
    df = create_dataset('INVALIDTICKER123', '1y')
    assert df is not None, "Returned value should not be None"
    assert df.empty, "Dataset should be empty for an invalid ticker"

if __name__ == "__main__":
    test_create_dataset()