r"""
Module of exceptions.
"""


class CriticalException(Exception):
    r"""
    Critical exception.
    """
    def __init__(self, message: str = ""):
        super().__init__(message)


class InputEmptyError(Exception):
    r"""
    Input empty error.
    """
    def __init__(self, message: str = ""):
        super().__init__(message)
