class VerbexError(Exception):
    """Base SDK error."""


class VerbexAPIError(VerbexError):
    def __init__(
        self, status_code: int, message: str, response_text: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
