import requests
from typing import Dict, Any, Optional

class PicknSDK:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.pickn.fr/v1"
        self.session = requests.Session()
        
    def config(self, api_key: str, environment: str = "test"):
        self.api_key = api_key
        if environment == "test":
            self.base_url = "https://api-test.pickn.fr/v1"
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    class Payments:
        def __init__(self, sdk):
            self.sdk = sdk
            
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
            response = self.sdk.session.post(f"{self.sdk.base_url}/payments", json=data)
            return response.json()
            
        def retrieve(self, payment_id: str) -> Dict[str, Any]:
            response = self.sdk.session.get(f"{self.sdk.base_url}/payments/{payment_id}")
            return response.json()

    class Deliveries:
        def __init__(self, sdk):
            self.sdk = sdk
            
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
            response = self.sdk.session.post(f"{self.sdk.base_url}/deliveries", json=data)
            return response.json()
            
        def retrieve(self, delivery_id: str) -> Dict[str, Any]:
            response = self.sdk.session.get(f"{self.sdk.base_url}/deliveries/{delivery_id}")
            return response.json()

    class Refunds:
        def __init__(self, sdk):
            self.sdk = sdk
            
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
            response = self.sdk.session.post(f"{self.sdk.base_url}/refunds", json=data)
            return response.json()

    @property
    def payments(self):
        return self.Payments(self)
        
    @property
    def deliveries(self):
        return self.Deliveries(self)
        
    @property
    def refunds(self):
        return self.Refunds(self)
