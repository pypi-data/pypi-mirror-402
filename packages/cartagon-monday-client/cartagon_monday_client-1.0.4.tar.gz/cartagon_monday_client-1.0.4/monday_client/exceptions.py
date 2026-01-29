class MondayAPIError(Exception):
    def __init__(self, error_code: str | int, error_message: str, query: str):
        self.error_code = error_code
        self.error_message = error_message
        self.query = query

        super().__init__(
            f"Monday API Error\n"
            f"Code: {error_code}\n"
            f"Message: {error_message}\n"
            f"Query: {query}"
        )
