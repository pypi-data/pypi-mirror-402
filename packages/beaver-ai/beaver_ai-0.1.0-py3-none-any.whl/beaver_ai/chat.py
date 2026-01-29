import requests
from typing import Any
from .errors import BeaverError


class ChatCompletions:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url
        self._api_key = api_key

    def create(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        top_p: float | None = None,
    ) -> dict[str, Any]:
        request_body: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if temperature is not None:
            request_body["temperature"] = temperature
        if max_output_tokens is not None:
            request_body["max_output_tokens"] = max_output_tokens
        if top_p is not None:
            request_body["top_p"] = top_p

        response = requests.post(
            f"{self._base_url}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            json=request_body,
        )

        if not response.ok:
            try:
                error_data = response.json()
                error_code = error_data.get("error", {}).get("type")
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            except Exception:
                error_code = None
                error_message = f"HTTP {response.status_code}"

            raise BeaverError(error_message, response.status_code, error_code)

        return response.json()


class Chat:
    def __init__(self, base_url: str, api_key: str):
        self.completions = ChatCompletions(base_url, api_key)
