import sys
import os

# Add the parent directory to the path so we can import cashy when running locally
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cashy import CurrencyConverter

def main():
    try:
        converter = CurrencyConverter()
        
        # Let's convert $100 to Indian Rupees
        amount = 100
        from_curr = 'USD'
        to_curr = 'INR'
        
        print(f"Converting ${amount} to Indian Rupees...")
        result = converter.convert(amount, from_curr, to_curr)
        print(f"${amount} USD = ₹{result:.2f} INR")
        
        # Check what the current exchange rate is
        rate = converter.get_exchange_rate(from_curr, to_curr)
        print(f"Exchange rate: 1 USD = {rate} INR")
        
        print("\n" + "="*40)
        print("Getting list of supported currencies...")
        currencies = converter.get_supported_currencies()
        print(f"Found {len(currencies)} currencies available")
        
        # Show a few examples
        print("\nSome examples:")
        for code, name in list(currencies.items())[:5]:
            print(f"  {code} - {name}")

        print("\n" + "="*40)
        print(f"Getting all exchange rates for {from_curr}...")
        all_rates = converter.get_latest_rates(from_curr)
        print(f"Got rates for {len(all_rates)} currencies")
        
        # Show EUR rate as an example
        eur_rate = all_rates.get('EUR')
        if eur_rate:
            print(f"USD to EUR: 1 USD = {eur_rate} EUR")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
