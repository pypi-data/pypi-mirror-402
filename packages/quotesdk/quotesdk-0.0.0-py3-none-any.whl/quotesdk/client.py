import requests
import urllib3
from .models import Quote
from .errors import APIError

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class QuoteClient:
    BASE_URL ="https://api.quotable.io"
    def get_random_quote(self):
        try:
            response = requests.get(f"{self.BASE_URL}/random", timeout=5, verify=False)
        except requests.RequestException:
            raise APIError("Network error")

        if response.status_code != 200:
            raise APIError("Failed to fetch quote")

        data = response.json()
        return Quote(
            text=data["content"],
            author=data["author"]
        )
