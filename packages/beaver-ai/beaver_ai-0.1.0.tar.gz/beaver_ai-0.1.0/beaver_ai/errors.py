class BeaverError(Exception):
    def __init__(self, message: str, status: int, code: str | None = None):
        self.message = message
        self.status = status
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        if self.code:
            return f"BeaverError(status={self.status}, code={self.code}): {self.message}"
        return f"BeaverError(status={self.status}): {self.message}"
