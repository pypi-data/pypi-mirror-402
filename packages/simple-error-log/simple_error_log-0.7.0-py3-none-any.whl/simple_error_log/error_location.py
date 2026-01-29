class ErrorLocation:
    """
    Base class for error locations
    """

    def format(self):
        """
        Format the error location
        """
        return f"{self}"

    def to_dict(self):
        """
        Convert the error location to a dictionary
        """
        return {}

    def __str__(self):
        """
        Convert the error location to a string
        """
        return ""


class GridLocation(ErrorLocation):
    """
    Error location for a grid
    """

    def __init__(self, row: int, column: int):
        """
        Initialize the grid location
        """
        self.row = row
        self.column = column

    def to_dict(self):
        """
        Convert the grid location to a dictionary
        """
        return {"row": self.row, "column": self.column}

    def __str__(self):
        """
        Convert the grid location to a string
        """
        return f"[{self.row}, {self.column}]"


class DocumentSectionLocation(ErrorLocation):
    """
    Error location for a document section
    """

    def __init__(self, section_number: str = None, section_title: str = None):
        """
        Initialize the document section location
        """
        self.section_number = section_number
        self.section_title = section_title

    def to_dict(self):
        """
        Convert the document section location to a dictionary
        """
        return {
            "section_number": self.section_number,
            "section_title": self.section_title,
        }

    def __str__(self):
        """
        Convert the document section location to a string
        """
        return f"[{self.section_number} {self.section_title}]"


class KlassMethodLocation(ErrorLocation):
    """
    Error location for a class method
    """

    def __init__(self, class_name: str, method_name: str):
        """
        Initialize the class method location
        """
        self.class_name = class_name
        self.method_name = method_name

    def to_dict(self):
        """
        Convert the class method location to a dictionary
        """
        return {"class_name": self.class_name, "method_name": self.method_name}

    def __str__(self):
        """
        Convert the class method location to a string
        """
        return f"{self.class_name}.{self.method_name}"
