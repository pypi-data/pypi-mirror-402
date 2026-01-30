import requests
from typing import Dict, Any

class BaseClient:
    def __init__(self):
        self.base_url = "https://ref.miracle-api.workers.dev/exec"
        self.session = requests.Session()

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to make GET requests to the MIRACLE API.
        """
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {"error": str(e), "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
