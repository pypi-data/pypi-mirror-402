from .chat import Chat


class Beaver:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8080"):
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url
        self.chat = Chat(base_url, api_key)
