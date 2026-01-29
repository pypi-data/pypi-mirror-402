class APIError(Exception):
    def __init__(
            self,
            message: str,
            status: int,
            details: str | None = None,
        ):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details

    def __str__(self):
        if self.details:
            return (
                f'APIError {self.status}: {self.message} '
                f'Details: {self.details}'
            )
        return f'APIError {self.status}: {self.message}'
