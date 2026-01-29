from simple_error_log.error_location import (
    ErrorLocation,
    GridLocation,
    DocumentSectionLocation,
    KlassMethodLocation,
)


class TestErrorLocation:
    """Test cases for the base ErrorLocation class"""

    def test_error_location_str(self):
        """Test string representation of ErrorLocation"""
        el = ErrorLocation()
        assert str(el) == ""

    def test_error_location_format(self):
        """Test format method of ErrorLocation"""
        el = ErrorLocation()
        assert el.format() == ""

    def test_error_location_to_dict(self):
        """Test to_dict method of ErrorLocation"""
        el = ErrorLocation()
        assert el.to_dict() == {}

    def test_error_location_inheritance(self):
        """Test that ErrorLocation can be subclassed"""

        class CustomLocation(ErrorLocation):
            def __str__(self):
                return "custom"

        cl = CustomLocation()
        assert str(cl) == "custom"
        assert cl.format() == "custom"


class TestGridLocation:
    """Test cases for GridLocation class"""

    def test_grid_location_basic(self):
        """Test basic GridLocation functionality"""
        gl = GridLocation(1, 2)
        assert str(gl) == "[1, 2]"
        assert gl.to_dict() == {"row": 1, "column": 2}

    def test_grid_location_format(self):
        """Test format method of GridLocation"""
        gl = GridLocation(5, 10)
        assert gl.format() == "[5, 10]"

    def test_grid_location_zero_values(self):
        """Test GridLocation with zero values"""
        gl = GridLocation(0, 0)
        assert str(gl) == "[0, 0]"
        assert gl.to_dict() == {"row": 0, "column": 0}

    def test_grid_location_negative_values(self):
        """Test GridLocation with negative values"""
        gl = GridLocation(-1, -5)
        assert str(gl) == "[-1, -5]"
        assert gl.to_dict() == {"row": -1, "column": -5}

    def test_grid_location_large_values(self):
        """Test GridLocation with large values"""
        gl = GridLocation(1000, 2000)
        assert str(gl) == "[1000, 2000]"
        assert gl.to_dict() == {"row": 1000, "column": 2000}

    def test_grid_location_attributes(self):
        """Test GridLocation attribute access"""
        gl = GridLocation(3, 7)
        assert gl.row == 3
        assert gl.column == 7

    def test_grid_location_inheritance(self):
        """Test that GridLocation inherits from ErrorLocation"""
        gl = GridLocation(1, 2)
        assert isinstance(gl, ErrorLocation)


class TestDocumentSectionLocation:
    """Test cases for DocumentSectionLocation class"""

    def test_document_section_location_basic(self):
        """Test basic DocumentSectionLocation functionality"""
        dsl = DocumentSectionLocation("1", "Introduction")
        assert str(dsl) == "[1 Introduction]"
        assert dsl.to_dict() == {"section_number": "1", "section_title": "Introduction"}

    def test_document_section_location_format(self):
        """Test format method of DocumentSectionLocation"""
        dsl = DocumentSectionLocation("2.1", "Background")
        assert dsl.format() == "[2.1 Background]"

    def test_document_section_location_none_values(self):
        """Test DocumentSectionLocation with None values"""
        dsl = DocumentSectionLocation(None, None)
        assert str(dsl) == "[None None]"
        assert dsl.to_dict() == {"section_number": None, "section_title": None}

    def test_document_section_location_default_values(self):
        """Test DocumentSectionLocation with default parameter values"""
        dsl = DocumentSectionLocation()
        assert str(dsl) == "[None None]"
        assert dsl.to_dict() == {"section_number": None, "section_title": None}

    def test_document_section_location_only_number(self):
        """Test DocumentSectionLocation with only section number"""
        dsl = DocumentSectionLocation("3.2")
        assert str(dsl) == "[3.2 None]"
        assert dsl.to_dict() == {"section_number": "3.2", "section_title": None}

    def test_document_section_location_only_title(self):
        """Test DocumentSectionLocation with only section title"""
        dsl = DocumentSectionLocation(section_title="Conclusion")
        assert str(dsl) == "[None Conclusion]"
        assert dsl.to_dict() == {"section_number": None, "section_title": "Conclusion"}

    def test_document_section_location_empty_strings(self):
        """Test DocumentSectionLocation with empty strings"""
        dsl = DocumentSectionLocation("", "")
        assert str(dsl) == "[ ]"
        assert dsl.to_dict() == {"section_number": "", "section_title": ""}

    def test_document_section_location_special_characters(self):
        """Test DocumentSectionLocation with special characters"""
        dsl = DocumentSectionLocation("A.1.2", "Methods & Results")
        assert str(dsl) == "[A.1.2 Methods & Results]"
        assert dsl.to_dict() == {
            "section_number": "A.1.2",
            "section_title": "Methods & Results",
        }

    def test_document_section_location_attributes(self):
        """Test DocumentSectionLocation attribute access"""
        dsl = DocumentSectionLocation("4", "Discussion")
        assert dsl.section_number == "4"
        assert dsl.section_title == "Discussion"

    def test_document_section_location_inheritance(self):
        """Test that DocumentSectionLocation inherits from ErrorLocation"""
        dsl = DocumentSectionLocation("1", "Test")
        assert isinstance(dsl, ErrorLocation)


class TestKlassMethodLocation:
    """Test cases for KlassMethodLocation class"""

    def test_klass_method_location_basic(self):
        """Test basic KlassMethodLocation functionality"""
        kml = KlassMethodLocation("MyClass", "my_method")
        assert str(kml) == "MyClass.my_method"
        assert kml.to_dict() == {"class_name": "MyClass", "method_name": "my_method"}

    def test_klass_method_location_format(self):
        """Test format method of KlassMethodLocation"""
        kml = KlassMethodLocation("TestClass", "test_function")
        assert kml.format() == "TestClass.test_function"

    def test_klass_method_location_empty_strings(self):
        """Test KlassMethodLocation with empty strings"""
        kml = KlassMethodLocation("", "")
        assert str(kml) == "."
        assert kml.to_dict() == {"class_name": "", "method_name": ""}

    def test_klass_method_location_special_characters(self):
        """Test KlassMethodLocation with special characters"""
        kml = KlassMethodLocation("My_Class", "__init__")
        assert str(kml) == "My_Class.__init__"
        assert kml.to_dict() == {"class_name": "My_Class", "method_name": "__init__"}

    def test_klass_method_location_long_names(self):
        """Test KlassMethodLocation with long names"""
        long_class = "VeryLongClassNameForTesting"
        long_method = "very_long_method_name_for_testing_purposes"
        kml = KlassMethodLocation(long_class, long_method)
        expected = f"{long_class}.{long_method}"
        assert str(kml) == expected
        assert kml.to_dict() == {"class_name": long_class, "method_name": long_method}

    def test_klass_method_location_attributes(self):
        """Test KlassMethodLocation attribute access"""
        kml = KlassMethodLocation("Calculator", "add")
        assert kml.class_name == "Calculator"
        assert kml.method_name == "add"

    def test_klass_method_location_inheritance(self):
        """Test that KlassMethodLocation inherits from ErrorLocation"""
        kml = KlassMethodLocation("Test", "method")
        assert isinstance(kml, ErrorLocation)


class TestLocationComparisons:
    """Test cases for comparing different location types"""

    def test_different_location_types_string_comparison(self):
        """Test string representations of different location types"""
        el = ErrorLocation()
        gl = GridLocation(1, 1)
        dsl = DocumentSectionLocation("1", "Test")
        kml = KlassMethodLocation("Class", "method")

        assert str(el) == ""
        assert str(gl) == "[1, 1]"
        assert str(dsl) == "[1 Test]"
        assert str(kml) == "Class.method"

    def test_different_location_types_dict_comparison(self):
        """Test dictionary representations of different location types"""
        el = ErrorLocation()
        gl = GridLocation(2, 3)
        dsl = DocumentSectionLocation("2", "Analysis")
        kml = KlassMethodLocation("Parser", "parse")

        assert el.to_dict() == {}
        assert gl.to_dict() == {"row": 2, "column": 3}
        assert dsl.to_dict() == {"section_number": "2", "section_title": "Analysis"}
        assert kml.to_dict() == {"class_name": "Parser", "method_name": "parse"}

    def test_all_locations_have_format_method(self):
        """Test that all location types have working format method"""
        locations = [
            ErrorLocation(),
            GridLocation(1, 2),
            DocumentSectionLocation("1", "Test"),
            KlassMethodLocation("Class", "method"),
        ]

        for location in locations:
            # Should not raise an exception
            result = location.format()
            assert isinstance(result, str)
            assert result == str(location)
