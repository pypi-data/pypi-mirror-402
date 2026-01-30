# hurdat2py/errors.py
class Hurdat2Error(Exception):
    """Base exception for the hurdat2py package."""
    pass

class InvalidDataEntryError(Hurdat2Error):
    """Raised when a specific data line cannot be parsed due to incorrect format."""
    pass

class DataDownloadError(Hurdat2Error):
    """Raised when data download fails."""
    pass

class DataParseError(Hurdat2Error):
    """Raised when data parsing fails."""
    pass
    
class StormNotFoundError(Hurdat2Error):
    """Raised when a specific storm cannot be found."""
    pass