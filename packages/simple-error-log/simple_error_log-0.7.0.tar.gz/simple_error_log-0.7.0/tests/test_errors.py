import re
import time
from simple_error_log.errors import Errors
from simple_error_log.error import Error
from simple_error_log.error_location import ErrorLocation


def fix_timestamp(data: str) -> str:
    timestamp_pattern = r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{6})"
    return re.sub(timestamp_pattern, "YYYY-MM-DD HH:MM:SS.nnnnnn", data)


class MockErrorLocation(ErrorLocation):
    """
    Mock error location
    """

    def to_dict(self):
        return {"mock_key": "mock_value"}


def test_errors_initialization():
    """
    Test the errors initialization
    """
    errors: Errors = Errors()
    assert errors.count() == 0


def test_errors_add():
    """
    Test the errors add method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.add("Test error", location, "test_error_type", Error.ERROR)
    assert errors.count() == 1


def test_errors_clear():
    """
    Test the errors clear method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.add("Test error", location, "test_error_type", Error.ERROR)
    errors.clear()
    assert errors.count() == 0


def test_errors_to_dict():
    """
    Test the errors dump method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.add("Test error 1", location, "warning_type", Error.WARNING)
    errors.add("Test error 2", location, "error_type", Error.ERROR)

    # With the new logic, dump(Error.WARNING) returns errors with level >= WARNING
    # So it should include both ERROR and WARNING levels
    dumped_errors = errors.to_dict(Error.WARNING)
    assert len(dumped_errors) == 2

    # dump(Error.ERROR) returns errors with level >= ERROR
    # So it should include only the ERROR level
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 1

    # Test the default parameter (ERROR)
    dumped_errors = errors.to_dict()
    assert len(dumped_errors) == 1


def test_errors_dump():
    """
    Test the errors str method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.add("Test error 1\nLine2\nline3", location, "warning_type", Error.WARNING)
    errors.add("Test error 2", location, "error_type", Error.ERROR)
    errors.add("Test error 3\n-\nExtra line", location, "error_type", Error.ERROR)
    raw_result = errors.dump(Error.WARNING)
    fixed_result = fix_timestamp(raw_result)  # Timestamps are dynamic
    assert (
        fixed_result
        == """- Warning, type: 'warning_type', @ YYYY-MM-DD HH:MM:SS.nnnnnn, location: {'mock_key': 'mock_value'}
  Test error 1
  Line2
  line3

- Error, type: 'error_type', @ YYYY-MM-DD HH:MM:SS.nnnnnn, location: {'mock_key': 'mock_value'}
  Test error 2

- Error, type: 'error_type', @ YYYY-MM-DD HH:MM:SS.nnnnnn, location: {'mock_key': 'mock_value'}
  Test error 3
  -
  Extra line

"""
    )


def test_errors_error():
    """
    Test the error method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.error("Test error message", location)

    assert errors.count() == 1

    # Get the error and verify its properties
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 1

    error = dumped_errors[0]
    assert error["message"] == "Test error message"
    assert error["level"] == "Error"
    assert error["location"] == {"mock_key": "mock_value"}


def test_errors_info():
    """
    Test the info method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.info("Test info message", location)

    assert errors.count() == 1

    # With the new logic, INFO level errors are only included when dumping with level <= INFO
    # INFO level errors should not be included when dumping with ERROR or WARNING levels
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 0

    dumped_errors = errors.to_dict(Error.WARNING)
    assert len(dumped_errors) == 0

    # But they should be included when dumping with INFO or DEBUG levels
    dumped_errors = errors.to_dict(Error.INFO)
    assert len(dumped_errors) == 1

    error = dumped_errors[0]
    assert error["message"] == "Test info message"
    assert error["level"] == "Info"
    assert error["location"] == {"mock_key": "mock_value"}

    dumped_errors = errors.to_dict(Error.DEBUG)
    assert len(dumped_errors) == 1


def test_errors_debug():
    """
    Test the debug method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.debug("Test debug message", location)

    assert errors.count() == 1

    # With the new logic, DEBUG level errors are only included when dumping with level <= DEBUG
    # DEBUG level errors should not be included when dumping with ERROR, WARNING, or INFO levels
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 0

    dumped_errors = errors.to_dict(Error.WARNING)
    assert len(dumped_errors) == 0

    dumped_errors = errors.to_dict(Error.INFO)
    assert len(dumped_errors) == 0

    # But they should be included when dumping with DEBUG level
    dumped_errors = errors.to_dict(Error.DEBUG)
    assert len(dumped_errors) == 1

    error = dumped_errors[0]
    assert error["message"] == "Test debug message"
    assert error["level"] == "Debug"
    assert error["location"] == {"mock_key": "mock_value"}


def test_errors_warning():
    """
    Test the warning method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()
    errors.warning("Test warning message", location)

    assert errors.count() == 1

    # With the new logic, WARNING level errors are only included when dumping with level <= WARNING
    # WARNING level errors should not be included when dumping with ERROR level
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 0

    # But they should be included when dumping with WARNING, INFO, or DEBUG levels
    dumped_errors = errors.to_dict(Error.WARNING)
    assert len(dumped_errors) == 1

    error = dumped_errors[0]
    assert error["message"] == "Test warning message"
    assert error["level"] == "Warning"
    assert error["location"] == {"mock_key": "mock_value"}

    dumped_errors = errors.to_dict(Error.INFO)
    assert len(dumped_errors) == 1

    dumped_errors = errors.to_dict(Error.DEBUG)
    assert len(dumped_errors) == 1


def test_errors_exception():
    """
    Test the exception method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()

    try:
        # Create an exception
        raise ValueError("Test exception")
    except Exception as e:
        errors.exception("Test exception message", e, location)

    assert errors.count() == 1

    # Get the error and verify its properties
    dumped_errors = errors.to_dict(Error.ERROR)
    assert len(dumped_errors) == 1

    error = dumped_errors[0]
    # Check that the message contains the expected parts
    assert "Test exception message" in error["message"]
    assert "Details" in error["message"]
    assert "ValueError: Test exception" in error["message"]
    assert "Traceback" in error["message"]
    assert error["level"] == "Error"
    assert error["location"] == {"mock_key": "mock_value"}


def test_errors_exception_includes_call_stack():
    """
    Test that exception method includes the full call stack leading to where
    errors.exception() was called, not just the exception traceback.
    """
    errors: Errors = Errors()

    def inner_function():
        raise ValueError("Inner exception")

    def outer_function():
        inner_function()

    def caller_function():
        try:
            outer_function()
        except Exception as e:
            errors.exception("Exception caught", e)

    caller_function()

    assert errors.count() == 1

    dumped_errors = errors.to_dict(Error.ERROR)
    error = dumped_errors[0]
    message = error["message"]

    # Verify the call stack is included (shows where errors.exception was called from)
    assert "caller_function" in message

    # Verify the exception traceback is also included
    assert "outer_function" in message
    assert "inner_function" in message
    assert "ValueError: Inner exception" in message


def test_errors_exception_traceback_shows_full_chain():
    """
    Test that the traceback shows the complete chain from the top-level caller
    down to where the exception was raised.
    """
    errors: Errors = Errors()

    def level_3():
        _ = 10 / 0  # This will raise ZeroDivisionError

    def level_2():
        level_3()

    def level_1():
        level_2()

    def main():
        try:
            level_1()
        except Exception as e:
            errors.exception("Division error", e)

    main()

    assert errors.count() == 1

    dumped_errors = errors.to_dict(Error.ERROR)
    error = dumped_errors[0]
    message = error["message"]

    # Verify the message structure
    assert "Division error" in message
    assert "Details" in message
    assert "division by zero" in message
    assert "Traceback" in message

    # Verify the call stack shows the path to errors.exception()
    assert "main" in message

    # Verify the exception traceback shows all levels
    assert "level_1" in message
    assert "level_2" in message
    assert "level_3" in message
    assert "ZeroDivisionError" in message


def test_errors_with_default_location():
    """
    Test the methods with default location (None)
    """
    errors: Errors = Errors()

    # Test each method with default location
    errors.error("Test error with default location")
    errors.info("Test info with default location")
    errors.debug("Test debug with default location")
    errors.warning("Test warning with default location")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        errors.exception("Test exception with default location", e)

    assert errors.count() == 5

    # Verify that all errors have a default location
    # With the new logic, we need to use the lowest level (DEBUG) to get all errors
    dumped_errors = errors.to_dict(Error.DEBUG)
    assert len(dumped_errors) == 5
    for error in dumped_errors:
        assert "location" in error
        # Default ErrorLocation to_dict() should return an empty dict
        assert isinstance(error["location"], dict)


def test_errors_merge():
    """
    Test the merge method
    """
    # Create first Errors object with some errors
    errors1 = Errors()
    location1 = MockErrorLocation()
    errors1.error("Error 1", location1)

    # Sleep briefly to ensure different timestamps
    time.sleep(0.01)

    # Create second Errors object with some errors
    errors2 = Errors()
    location2 = MockErrorLocation()
    errors2.warning("Warning 1", location2)
    errors2.error("Error 2", location2)

    # Get the initial counts
    assert errors1.count() == 1
    assert errors2.count() == 2

    # Merge errors2 into errors1
    errors1.merge(errors2)

    # Verify the merged count
    assert errors1.count() == 3

    # Dump all errors and verify they're all there
    all_errors = errors1.to_dict(Error.DEBUG)
    assert len(all_errors) == 3

    # Verify the errors are in the correct order (sorted by timestamp)
    # The first error should be "Error 1" since it was created first
    assert all_errors[0]["message"] == "Error 1"
    assert all_errors[0]["level"] == "Error"

    # The next errors should be from errors2, in the order they were created
    assert all_errors[1]["message"] == "Warning 1"
    assert all_errors[1]["level"] == "Warning"

    assert all_errors[2]["message"] == "Error 2"
    assert all_errors[2]["level"] == "Error"

    # Verify timestamps are in ascending order
    timestamp1 = all_errors[0]["timestamp"]
    timestamp2 = all_errors[1]["timestamp"]
    timestamp3 = all_errors[2]["timestamp"]

    assert timestamp1 <= timestamp2 <= timestamp3


def test_errors_merge_empty():
    """
    Test merging with an empty Errors object
    """
    # Create an Errors object with some errors
    errors1 = Errors()
    location = MockErrorLocation()
    errors1.error("Error 1", location)
    errors1.warning("Warning 1", location)

    # Create an empty Errors object
    errors2 = Errors()

    # Get the initial counts
    assert errors1.count() == 2
    assert errors2.count() == 0

    # Merge empty errors2 into errors1
    errors1.merge(errors2)

    # Verify count hasn't changed
    assert errors1.count() == 2

    # Merge errors1 into empty errors2
    errors2.merge(errors1)

    # Verify errors2 now has all the errors
    assert errors2.count() == 2

    # Dump all errors and verify they're all there
    all_errors = errors2.to_dict(Error.DEBUG)
    assert len(all_errors) == 2

    # Verify the errors are in the correct order
    assert all_errors[0]["message"] == "Error 1"
    assert all_errors[0]["level"] == "Error"

    assert all_errors[1]["message"] == "Warning 1"
    assert all_errors[1]["level"] == "Warning"


def test_errors_error_count():
    """
    Test the error_count method
    """
    errors: Errors = Errors()
    location = MockErrorLocation()

    # Initially there should be no errors
    assert errors.error_count() == 0

    # Add errors with different levels
    errors.error("Error 1", location)
    errors.warning("Warning 1", location)
    errors.info("Info 1", location)
    errors.debug("Debug 1", location)

    # Verify total count
    assert errors.count() == 4

    # Verify error_count only counts ERROR level items
    assert errors.error_count() == 1

    # Add another error
    errors.error("Error 2", location)

    # Verify counts again
    assert errors.count() == 5
    assert errors.error_count() == 2

    # Add an error with explicit level
    errors.add("Error 3", location, "test_error_type", Error.ERROR)

    # Verify counts again
    assert errors.count() == 6
    assert errors.error_count() == 3

    # Add an exception (which should be at ERROR level)
    try:
        raise ValueError("Test exception")
    except Exception as e:
        errors.exception("Exception 1", e, location)

    # Verify counts again
    assert errors.count() == 7
    assert errors.error_count() == 4

    # Clear all errors
    errors.clear()

    # Verify counts are reset
    assert errors.count() == 0
    assert errors.error_count() == 0
