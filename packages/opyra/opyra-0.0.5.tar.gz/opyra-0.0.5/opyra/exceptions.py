
class SuperDataError(Exception):
    """Base class for all SuperData exceptions."""
    pass

class ConfigurationError(SuperDataError):
    """Raised when the database URL or driver is missing."""
    pass

class ConnectivityError(SuperDataError):
    """Raised when connection to the database fails."""
    pass

class QueryError(SuperDataError):
    """Raised when a SQL query or Mongo command is invalid."""
    pass

class RecordNotFoundError(SuperDataError):
    """Raised when a generic find operation returns nothing (optional use)."""
    pass

