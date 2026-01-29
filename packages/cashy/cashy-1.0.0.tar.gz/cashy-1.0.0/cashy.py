import requests

class CurrencyConverter:
    """
    Simple currency converter that uses the Frankfurter API to get live exchange rates.
    No API keys needed - just plug and play!
    """
    BASE_URL = "https://api.frankfurter.app"

    def __init__(self):
        # Nothing special to initialize for now
        pass

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Gets the current exchange rate between two currencies.
        
        Args:
            from_currency: Currency code you're converting from (like 'USD')
            to_currency: Currency code you want to convert to (like 'EUR')
            
        Returns:
            The exchange rate as a float
            
        Raises:
            Exception: When something goes wrong with the API or currency codes are invalid
        """
        # Same currency? That's easy - rate is always 1.0
        if from_currency == to_currency:
            return 1.0

        try:
            url = f"{self.BASE_URL}/latest?from={from_currency}&to={to_currency}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Double-check that we got the rate we asked for
            if to_currency not in data.get('rates', {}):
                raise ValueError(f"Couldn't find exchange rate for {to_currency}")
                 
            return data['rates'][to_currency]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch exchange rate: {e}")

    def get_supported_currencies(self) -> dict:
        """
        Grabs all the currencies that Frankfurter supports.
        
        Returns:
            A dict with currency codes as keys and full names as values
        """
        try:
            url = f"{self.BASE_URL}/currencies"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Couldn't fetch supported currencies: {e}")

    def get_latest_rates(self, base_currency: str = 'USD') -> dict:
        """
        Gets exchange rates for all currencies against your chosen base currency.
        
        Args:
            base_currency: The currency to compare everything else to (defaults to USD)
            
        Returns:
            Dictionary with currency codes and their exchange rates
        """
        try:
            url = f"{self.BASE_URL}/latest?from={base_currency}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get('rates', {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"Couldn't get latest rates: {e}")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Does the actual currency conversion.
        
        Args:
            amount: How much money you want to convert
            from_currency: What currency you have
            to_currency: What currency you want
            
        Returns:
            The converted amount
        """
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate