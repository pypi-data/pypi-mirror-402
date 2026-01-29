import requests
from typing import List, Dict, Any, Optional

class Plutoniium:
    def __init__(self, api_key: str, base_url: str = "https://api.plutoniium.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages
        }

        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        url = f"{self.base_url}/models"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
