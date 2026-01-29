import logging
import re
from datetime import datetime
from simple_error_log.error import Error
from simple_error_log.error_location import (
    ErrorLocation,
    GridLocation,
    DocumentSectionLocation,
)


class MockErrorLocation(ErrorLocation):
    """
    Mock error location for testing
    """

    def to_dict(self):
        return {"mock_key": "mock_value"}

    def __str__(self):
        return "mock_location"


class TestErrorConstants:
    """Test cases for Error class constants"""

    def test_error_level_constants(self):
        """Test that error level constants match logging levels"""
        assert Error.ERROR == logging.ERROR
        assert Error.WARNING == logging.WARNING
        assert Error.DEBUG == logging.DEBUG
        assert Error.INFO == logging.INFO

    def test_error_label_mapping(self):
        """Test that LABEL mapping is correct"""
        assert Error.LABEL[Error.ERROR] == "error"
        assert Error.LABEL[Error.WARNING] == "warning"
        assert Error.LABEL[Error.DEBUG] == "debug"
        assert Error.LABEL[Error.INFO] == "info"

    def test_all_levels_have_labels(self):
        """Test that all defined levels have corresponding labels"""
        levels = [Error.ERROR, Error.WARNING, Error.DEBUG, Error.INFO]
        for level in levels:
            assert level in Error.LABEL
            assert isinstance(Error.LABEL[level], str)


class TestErrorInitialization:
    """Test cases for Error initialization"""

    def test_error_initialization_all_params(self):
        """Test error initialization with all parameters"""
        location = MockErrorLocation()
        error = Error("Test error message", location, "test_error_type", Error.ERROR)

        assert error.message == "Test error message"
        assert error.location == location
        assert error.level == Error.ERROR
        assert error.error_type == "test_error_type"
        assert isinstance(error.timestamp, datetime)

    def test_error_initialization_default_level(self):
        """Test error initialization with default level"""
        location = MockErrorLocation()
        error = Error("Test message", location, "test_type")

        assert error.level == Error.ERROR  # Default level
        assert error.message == "Test message"
        assert error.location == location
        assert error.error_type == "test_type"

    def test_error_initialization_default_error_type(self):
        """Test error initialization with default error type"""
        location = MockErrorLocation()
        error = Error("Test message", location)

        assert error.error_type == ""  # Default empty string
        assert error.message == "Test message"
        assert error.location == location
        assert error.level == Error.ERROR

    def test_error_initialization_all_levels(self):
        """Test error initialization with different levels"""
        location = MockErrorLocation()
        levels = [Error.ERROR, Error.WARNING, Error.DEBUG, Error.INFO]

        for level in levels:
            error = Error("Test message", location, "test_type", level)
            assert error.level == level

    def test_error_initialization_with_real_locations(self):
        """Test error initialization with real location objects"""
        grid_location = GridLocation(1, 2)
        doc_location = DocumentSectionLocation("1", "Introduction")

        error1 = Error("Grid error", grid_location, "grid_error")
        error2 = Error("Doc error", doc_location, "doc_error")

        assert error1.location == grid_location
        assert error2.location == doc_location

    def test_error_timestamp_creation(self):
        """Test that timestamp is created during initialization"""
        location = MockErrorLocation()
        before = datetime.now()
        error = Error("Test message", location)
        after = datetime.now()

        assert before <= error.timestamp <= after


class TestErrorToDictMethod:
    """Test cases for Error.to_dict() method"""

    def test_error_to_dict_basic(self):
        """Test basic to_dict functionality"""
        location = MockErrorLocation()
        error = Error("Test error message", location, "test_error_type", Error.WARNING)
        result_dict = error.to_dict()

        assert result_dict["location"] == {"mock_key": "mock_value"}
        assert result_dict["message"] == "Test error message"
        assert result_dict["level"] == "Warning"
        assert result_dict["type"] == "test_error_type"
        assert "timestamp" in result_dict

    def test_error_to_dict_all_levels(self):
        """Test to_dict with all error levels"""
        location = MockErrorLocation()
        test_cases = [
            (Error.ERROR, "Error"),
            (Error.WARNING, "Warning"),
            (Error.DEBUG, "Debug"),
            (Error.INFO, "Info"),
        ]

        for level, expected_label in test_cases:
            error = Error("Test message", location, "test_type", level)
            result_dict = error.to_dict()
            assert result_dict["level"] == expected_label

    def test_error_to_dict_timestamp_format(self):
        """Test timestamp format in to_dict"""
        location = MockErrorLocation()
        error = Error("Test message", location)
        result_dict = error.to_dict()

        assert "timestamp" in result_dict
        assert isinstance(result_dict["timestamp"], str)
        # Check timestamp format (YYYY-MM-DD HH:MM:SS.ffffff)
        assert re.match(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}", result_dict["timestamp"]
        )

    def test_error_to_dict_empty_error_type(self):
        """Test to_dict with empty error type"""
        location = MockErrorLocation()
        error = Error("Test message", location, "")
        result_dict = error.to_dict()

        assert result_dict["type"] == ""

    def test_error_to_dict_with_real_locations(self):
        """Test to_dict with real location objects"""
        grid_location = GridLocation(5, 10)
        error = Error("Grid error", grid_location, "grid_error")
        result_dict = error.to_dict()

        assert result_dict["location"] == {"row": 5, "column": 10}

    def test_error_to_dict_multiline_message(self):
        """Test to_dict with multiline message"""
        location = MockErrorLocation()
        multiline_message = "Line 1\nLine 2\nLine 3"
        error = Error(multiline_message, location)
        result_dict = error.to_dict()

        assert result_dict["message"] == multiline_message

    def test_error_to_dict_special_characters(self):
        """Test to_dict with special characters in message"""
        location = MockErrorLocation()
        special_message = "Error with special chars: àáâãäå æç èéêë"
        error = Error(special_message, location, "unicode_test")
        result_dict = error.to_dict()

        assert result_dict["message"] == special_message
        assert result_dict["type"] == "unicode_test"


class TestErrorStrMethod:
    """Test cases for Error.__str__() method"""

    def test_error_str_basic(self):
        """Test basic string representation"""
        location = MockErrorLocation()
        error = Error("Test message", location, "test_type", Error.ERROR)
        str_repr = str(error)

        assert "Error" in str_repr
        assert "test_type" in str_repr
        assert "Test message" in str_repr
        assert "mock_key" in str_repr

    def test_error_str_all_levels(self):
        """Test string representation with all error levels"""
        location = MockErrorLocation()
        test_cases = [
            (Error.ERROR, "Error"),
            (Error.WARNING, "Warning"),
            (Error.DEBUG, "Debug"),
            (Error.INFO, "Info"),
        ]

        for level, expected_label in test_cases:
            error = Error("Test message", location, "test_type", level)
            str_repr = str(error)
            assert expected_label in str_repr

    def test_error_str_multiline_message(self):
        """Test string representation with multiline message"""
        location = MockErrorLocation()
        multiline_message = "Line 1\nLine 2\nLine 3"
        error = Error(multiline_message, location, "multiline_test")
        str_repr = str(error)

        # Check that newlines are properly indented
        assert "Line 1" in str_repr
        assert "\n  Line 2" in str_repr
        assert "\n  Line 3" in str_repr

    def test_error_str_empty_message(self):
        """Test string representation with empty message"""
        location = MockErrorLocation()
        error = Error("", location, "empty_test")
        str_repr = str(error)

        assert "empty_test" in str_repr
        assert isinstance(str_repr, str)

    def test_error_str_timestamp_format(self):
        """Test that timestamp appears in string representation"""
        location = MockErrorLocation()
        error = Error("Test message", location)
        str_repr = str(error)

        # Should contain a timestamp pattern
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}", str_repr)

    def test_error_str_with_real_locations(self):
        """Test string representation with real location objects"""
        grid_location = GridLocation(3, 7)
        error = Error("Grid error", grid_location, "grid_test")
        str_repr = str(error)

        assert "row" in str_repr
        assert "column" in str_repr
        assert "3" in str_repr
        assert "7" in str_repr


class TestErrorEdgeCases:
    """Test cases for edge cases and error conditions"""

    def test_error_with_none_location_dict(self):
        """Test error with location that returns None from to_dict"""

        class NoneLocation(ErrorLocation):
            def to_dict(self):
                return None

        location = NoneLocation()
        error = Error("Test message", location)
        result_dict = error.to_dict()

        assert result_dict["location"] is None

    def test_error_with_complex_location_dict(self):
        """Test error with location that returns complex dictionary"""

        class ComplexLocation(ErrorLocation):
            def to_dict(self):
                return {
                    "nested": {"key": "value"},
                    "list": [1, 2, 3],
                    "number": 42,
                    "boolean": True,
                }

        location = ComplexLocation()
        error = Error("Test message", location)
        result_dict = error.to_dict()

        expected_location = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42,
            "boolean": True,
        }
        assert result_dict["location"] == expected_location

    def test_error_very_long_message(self):
        """Test error with very long message"""
        location = MockErrorLocation()
        long_message = "A" * 1000  # 1000 character message
        error = Error(long_message, location, "long_test")

        assert error.message == long_message
        assert len(str(error)) > 1000
        assert error.to_dict()["message"] == long_message

    def test_error_message_with_tabs_and_special_whitespace(self):
        """Test error message with tabs and special whitespace"""
        location = MockErrorLocation()
        special_message = "Message\twith\ttabs\r\nand\r\ncarriage\r\nreturns"
        error = Error(special_message, location)

        str_repr = str(error)
        dict_repr = error.to_dict()

        assert dict_repr["message"] == special_message
        assert isinstance(str_repr, str)


class TestErrorIntegration:
    """Integration tests combining multiple Error features"""

    def test_error_complete_workflow(self):
        """Test complete error workflow from creation to string/dict conversion"""
        # Create error with real location
        location = DocumentSectionLocation("2.1", "Methodology")
        error = Error(
            "Invalid data format in methodology section",
            location,
            "validation_error",
            Error.WARNING,
        )

        # Test all methods work together
        str_repr = str(error)
        dict_repr = error.to_dict()

        # Verify string representation
        assert "Warning" in str_repr
        assert "validation_error" in str_repr
        assert "Invalid data format" in str_repr

        # Verify dictionary representation
        assert dict_repr["level"] == "Warning"
        assert dict_repr["type"] == "validation_error"
        assert dict_repr["message"] == "Invalid data format in methodology section"
        assert dict_repr["location"]["section_number"] == "2.1"
        assert dict_repr["location"]["section_title"] == "Methodology"

    def test_multiple_errors_different_timestamps(self):
        """Test that multiple errors have different timestamps"""
        location = MockErrorLocation()

        error1 = Error("First error", location)
        # Small delay to ensure different timestamps
        import time

        time.sleep(0.001)
        error2 = Error("Second error", location)

        assert error1.timestamp != error2.timestamp
        assert error1.timestamp < error2.timestamp
