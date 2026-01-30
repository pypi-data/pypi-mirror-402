class PgQueryError(Exception):
    def __init__(self, message, query, position):
        super().__init__(message)
        self.query = query
        self.position = position
