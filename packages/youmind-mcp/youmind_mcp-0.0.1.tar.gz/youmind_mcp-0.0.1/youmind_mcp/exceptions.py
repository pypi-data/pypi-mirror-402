class CraftError(Exception):
    """Base exception for craft-related errors."""
    pass


class CraftNotFoundError(CraftError):
    """Raised when a craft with the given ID is not found."""
    pass


class CraftAccessError(CraftError):
    """Raised when access to a craft is denied (401/403)."""
    pass


class CraftContentError(CraftError):
    """Raised when craft content is missing or malformed."""
    pass

