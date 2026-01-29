import logging
from datetime import datetime
from simple_error_log.error_location import ErrorLocation


class Error:
    """
    Base class for errors
    """

    ERROR = logging.ERROR
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    LABEL = {ERROR: "error", WARNING: "warning", DEBUG: "debug", INFO: "info"}

    def __init__(
        self,
        message: str,
        location: ErrorLocation,
        error_type: str = "",
        level: int = ERROR,
    ):
        """
        Initialize the error
        """
        self.location = location
        self.message = message
        self.level = level
        self.error_type = error_type
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """
        Convert the error to a dictionary
        """
        result = {
            "level": self.__class__.LABEL[self.level].capitalize(),
            "message": self.message,
            "type": self.error_type,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "location": self.location.to_dict(),
        }
        return result

    def __str__(self) -> str:
        """
        Convert the error to a string
        """
        message = self.message.replace("\n", "\n  ")
        return f"- {self.__class__.LABEL[self.level].capitalize()}, type: '{self.error_type}', @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}, location: {self.location.to_dict()}\n  {message}"
