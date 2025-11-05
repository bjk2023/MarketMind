"""
Commodities data fetcher using Alpha Vantage
Supports oil, natural gas, metals, and agricultural commodities
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


# Commodity info with icons and categories
COMMODITIES_INFO = {
    # Energy
    'WTI': {
        'name': 'WTI Crude Oil',
        'full_name': 'West Texas Intermediate Crude Oil',
        'unit': 'USD per barrel',
        'icon': '🛢️',
        'category': 'Energy'
    },
    'BRENT': {
        'name': 'Brent Crude Oil',
        'full_name': 'Brent Crude Oil',
        'unit': 'USD per barrel',
        'icon': '⛽',
        'category': 'Energy'
    },
    'NATURAL_GAS': {
        'name': 'Natural Gas',
        'full_name': 'Henry Hub Natural Gas Spot Price',
        'unit': 'USD per MMBtu',
        'icon': '🔥',
        'category': 'Energy'
    },
    
    # Metals
    'COPPER': {
        'name': 'Copper',
        'full_name': 'Global Price of Copper',
        'unit': 'USD per metric ton',
        'icon': '🟤',
        'category': 'Metals'
    },
    'ALUMINUM': {
        'name': 'Aluminum',
        'full_name': 'Global Price of Aluminum',
        'unit': 'USD per metric ton',
        'icon': '⚪',
        'category': 'Metals'
    },
    
    # Agriculture
    'WHEAT': {
        'name': 'Wheat',
        'full_name': 'Global Price of Wheat',
        'unit': 'USD per metric ton',
        'icon': '🌾',
        'category': 'Agriculture'
    },
    'CORN': {
        'name': 'Corn',
        'full_name': 'Global Price of Corn',
        'unit': 'USD per metric ton',
        'icon': '🌽',
        'category': 'Agriculture'
    },
    'COTTON': {
        'name': 'Cotton',
        'full_name': 'Global Price of Cotton',
        'unit': 'USD per kilogram',
        'icon': '🌱',
        'category': 'Agriculture'
    },
    'SUGAR': {
        'name': 'Sugar',
        'full_name': 'Global Price of Sugar',
        'unit': 'USD per kilogram',
        'icon': '🍬',
        'category': 'Agriculture'
    },
    'COFFEE': {
        'name': 'Coffee',
        'full_name': 'Global Price of Coffee',
        'unit': 'USD per kilogram',
        'icon': '☕',
        'category': 'Agriculture'
    }
}


def get_commodity_price(commodity_code='WTI', interval='daily'):
    """
    Get commodity price data from Alpha Vantage
    
    Args:
        commodity_code: Commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS')
        interval: 'daily', 'weekly', 'monthly'
    
    Returns:
        Dict with commodity price data
    """
    try:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': commodity_code.upper(),
            'interval': interval,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Check for errors
        if 'Error Message' in data or 'Information' in data or 'Note' in data:
            return None
        
        if 'data' not in data:
            return None
        
        # Get commodity info
        commodity_info = COMMODITIES_INFO.get(commodity_code.upper(), {})
        
        # Get latest price (first item in data array)
        latest = data['data'][0] if data['data'] else None
        
        if not latest:
            return None
        
        # Get previous price for change calculation
        previous = data['data'][1] if len(data['data']) > 1 else None
        
        current_price = float(latest['value'])
        previous_price = float(previous['value']) if previous else current_price
        
        price_change = current_price - previous_price
        price_change_pct = ((price_change / previous_price) * 100) if previous_price != 0 else 0
        
        return {
            'code': commodity_code.upper(),
            'name': commodity_info.get('name', data.get('name', commodity_code)),
            'full_name': commodity_info.get('full_name', data.get('name', commodity_code)),
            'category': commodity_info.get('category', 'Other'),
            'icon': commodity_info.get('icon', '📊'),
            'current_price': round(current_price, 2),
            'previous_price': round(previous_price, 2),
            'price_change': round(price_change, 2),
            'price_change_percent': round(price_change_pct, 2),
            'unit': commodity_info.get('unit', data.get('unit', 'USD')),
            'date': latest['date'],
            'interval': interval,
            'history': [
                {
                    'date': item['date'],
                    'value': float(item['value'])
                }
                for item in data['data'][:30]  # Last 30 data points
            ]
        }
    
    except Exception as e:
        print(f"Error fetching commodity data: {e}")
        return None


def get_all_commodities():
    """
    Get current prices for all commodities
    
    Returns:
        List of commodity data
    """
    commodities = []
    
    for code in COMMODITIES_INFO.keys():
        data = get_commodity_price(code)
        if data:
            commodities.append(data)
    
    return commodities


def get_commodities_by_category():
    """
    Get commodities grouped by category
    """
    commodities = get_all_commodities()
    
    categorized = {
        'Energy': [],
        'Metals': [],
        'Agriculture': []
    }
    
    for commodity in commodities:
        category = commodity.get('category', 'Other')
        if category in categorized:
            categorized[category].append(commodity)
    
    return categorized


def get_commodity_list():
    """
    Get list of available commodities with metadata
    """
    return [
        {
            'code': code,
            'name': info['name'],
            'full_name': info['full_name'],
            'unit': info['unit'],
            'icon': info['icon'],
            'category': info['category']
        }
        for code, info in COMMODITIES_INFO.items()
    ]


if __name__ == "__main__":
    # Test the commodities fetcher
    print("Testing Commodities Fetcher\n")
    
    # Test WTI crude oil
    print("WTI Crude Oil:")
    wti = get_commodity_price('WTI')
    if wti:
        print(f"  {wti['icon']} {wti['name']}")
        print(f"  Current Price: ${wti['current_price']} {wti['unit']}")
        print(f"  Change: ${wti['price_change']} ({wti['price_change_percent']}%)")
        print(f"  Date: {wti['date']}")
    
    print("\nBrent Crude Oil:")
    brent = get_commodity_price('BRENT')
    if brent:
        print(f"  {brent['icon']} {brent['name']}")
        print(f"  Current Price: ${brent['current_price']} {brent['unit']}")
        print(f"  Change: ${brent['price_change']} ({brent['price_change_percent']}%)")
    
    print("\nAvailable Commodities:")
    commodities = get_commodity_list()
    for comm in commodities[:5]:
        print(f"  {comm['icon']} {comm['name']} ({comm['category']})")
