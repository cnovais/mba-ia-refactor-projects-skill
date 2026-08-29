class ApiError(Exception):
    """A known, expected failure (validation, not-found, conflict) that a controller
    raises to signal exactly which HTTP status/message the client should see.

    Anything that is *not* an ApiError is treated by the centralized error handler as
    an unexpected failure — logged with its full traceback and answered with a
    generic 500, instead of every route/controller repeating its own try/except.
    """

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
