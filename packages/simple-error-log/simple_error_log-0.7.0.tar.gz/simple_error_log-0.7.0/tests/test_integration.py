from simple_error_log.error_location import (
    GridLocation,
    DocumentSectionLocation,
)
from simple_error_log.errors import Errors


def test_integration():
    errors = Errors()
    location = DocumentSectionLocation("1", "Introduction")
    errors.add("Test error 1", location, "section_error")
    location = GridLocation(1, 3)
    errors.add("Test error 2", location, "grid_error")
    location = GridLocation(10, 30)
    errors.add("Test error 3", location, "info_error", level=Errors.INFO)
    assert errors.count() == 3

    # Get the dumped errors
    # With the new logic, dump(Errors.ERROR) returns errors with level >= ERROR (only ERROR level errors)
    # dump(Errors.INFO) returns errors with level >= INFO (ERROR, WARNING, and INFO level errors)
    error_dump = errors.to_dict(Errors.ERROR)
    info_dump = errors.to_dict(Errors.INFO)

    # Check the number of errors
    assert len(error_dump) == 2  # Only the ERROR level errors (first two)
    assert len(info_dump) == 3  # All errors (ERROR and INFO levels)

    # Also test with DEBUG level to get all errors
    debug_dump = errors.to_dict(Errors.DEBUG)
    assert len(debug_dump) == 3  # All errors

    # Import re for timestamp validation
    import re

    timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}"

    # Check first error
    assert error_dump[0]["location"] == {
        "section_number": "1",
        "section_title": "Introduction",
    }
    assert error_dump[0]["message"] == "Test error 1"
    assert error_dump[0]["level"] == "Error"
    assert error_dump[0]["type"] == "section_error"
    assert "timestamp" in error_dump[0]
    assert re.match(timestamp_pattern, error_dump[0]["timestamp"])

    # Check second error
    assert error_dump[1]["location"] == {"row": 1, "column": 3}
    assert error_dump[1]["message"] == "Test error 2"
    assert error_dump[1]["level"] == "Error"
    assert error_dump[1]["type"] == "grid_error"
    assert "timestamp" in error_dump[1]
    assert re.match(timestamp_pattern, error_dump[1]["timestamp"])

    # Check the INFO level error in the debug_dump (it won't be in error_dump with the new logic)
    # Find the INFO level error in the dumps
    info_error = None
    for error in debug_dump:
        if error["level"] == "Info":
            info_error = error
            break

    assert info_error is not None
    assert info_error["location"] == {"row": 10, "column": 30}
    assert info_error["message"] == "Test error 3"
    assert info_error["level"] == "Info"
    assert info_error["type"] == "info_error"
    assert "timestamp" in info_error
    assert re.match(timestamp_pattern, info_error["timestamp"])
