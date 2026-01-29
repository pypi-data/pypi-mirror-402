"""Tests for the tree-sitter C/C++ parser."""

from pathlib import Path

from kontexto.parsers.c_cpp_parser import CCppParser


class TestCCppParser:
    """Test suite for CCppParser."""

    def setup_method(self) -> None:
        self.parser = CCppParser()

    def test_config(self) -> None:
        """Test parser configuration."""
        assert self.parser.config.name == "c_cpp"
        assert ".c" in self.parser.config.extensions
        assert ".h" in self.parser.config.extensions
        assert ".cpp" in self.parser.config.extensions
        assert ".hpp" in self.parser.config.extensions

    def test_supports_file(self, tmp_path: Path) -> None:
        """Test file support detection."""
        c_file = tmp_path / "main.c"
        c_file.touch()
        cpp_file = tmp_path / "main.cpp"
        cpp_file.touch()
        py_file = tmp_path / "main.py"
        py_file.touch()

        assert self.parser.supports_file(c_file)
        assert self.parser.supports_file(cpp_file)
        assert not self.parser.supports_file(py_file)

    def test_parse_c_function(self, tmp_path: Path) -> None:
        """Test parsing a C function."""
        code = """// Say hello to someone
void hello(const char* name) {
    printf("Hello, %s!\\n", name);
}
"""
        file_path = tmp_path / "hello.c"
        file_path.write_text(code)

        entities, line_count = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "hello"
        assert entities[0].type == "function"
        assert entities[0].language == "c"
        assert "Say hello" in (entities[0].docstring or "")

    def test_parse_c_function_with_return_type(self, tmp_path: Path) -> None:
        """Test parsing a C function with return type."""
        code = """int add(int a, int b) {
    return a + b;
}
"""
        file_path = tmp_path / "math.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "add"
        assert "int" in entities[0].signature

    def test_parse_struct(self, tmp_path: Path) -> None:
        """Test parsing a struct."""
        code = """/* Represents a point in 2D space */
struct Point {
    int x;
    int y;
};
"""
        file_path = tmp_path / "point.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        struct_entity = next((e for e in entities if e.type == "struct"), None)
        assert struct_entity is not None
        assert struct_entity.name == "Point"
        assert "struct Point" in struct_entity.signature
        assert "Represents a point" in (struct_entity.docstring or "")

    def test_parse_enum(self, tmp_path: Path) -> None:
        """Test parsing an enum."""
        code = """enum Color {
    RED,
    GREEN,
    BLUE
};
"""
        file_path = tmp_path / "color.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        enum_entity = next((e for e in entities if e.type == "enum"), None)
        assert enum_entity is not None
        assert enum_entity.name == "Color"
        assert "enum Color" in enum_entity.signature

    def test_parse_typedef(self, tmp_path: Path) -> None:
        """Test parsing a typedef."""
        code = """typedef unsigned int uint32;
"""
        file_path = tmp_path / "types.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        typedef_entity = next((e for e in entities if e.type == "type"), None)
        assert typedef_entity is not None
        assert typedef_entity.name == "uint32"

    def test_parse_cpp_class(self, tmp_path: Path) -> None:
        """Test parsing a C++ class."""
        code = """/// Represents a user
class User {
public:
    void greet() {
        std::cout << "Hello!" << std::endl;
    }
};
"""
        file_path = tmp_path / "user.cpp"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next((e for e in entities if e.type == "class"), None)
        assert class_entity is not None
        assert class_entity.name == "User"
        assert class_entity.language == "cpp"
        assert "Represents a user" in (class_entity.docstring or "")

        # Check for method
        method = next((e for e in entities if e.type == "method"), None)
        assert method is not None
        assert method.name == "greet"

    def test_parse_cpp_class_with_inheritance(self, tmp_path: Path) -> None:
        """Test parsing a C++ class with inheritance."""
        code = """class Admin : public User {
public:
    void deleteUser() {
        // Admin can delete users
    }
};
"""
        file_path = tmp_path / "admin.cpp"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next((e for e in entities if e.type == "class"), None)
        assert class_entity is not None
        assert class_entity.name == "Admin"
        assert "User" in class_entity.base_classes
        assert ": User" in class_entity.signature

    def test_parse_cpp_constructor(self, tmp_path: Path) -> None:
        """Test parsing a C++ constructor."""
        code = """class Person {
public:
    Person(const std::string& name) {
        this->name = name;
    }
private:
    std::string name;
};
"""
        file_path = tmp_path / "person.cpp"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        # Constructor should be extracted as a method
        methods = [e for e in entities if e.type == "method"]
        assert len(methods) >= 1

    def test_parse_header_file(self, tmp_path: Path) -> None:
        """Test parsing a header file."""
        code = """#ifndef USER_H
#define USER_H

struct User {
    char name[100];
    int age;
};

void greet_user(struct User* user);

#endif
"""
        file_path = tmp_path / "user.h"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        # Should find the struct
        struct_entity = next((e for e in entities if e.type == "struct"), None)
        assert struct_entity is not None
        assert struct_entity.name == "User"

    def test_extract_calls(self, tmp_path: Path) -> None:
        """Test extraction of function calls."""
        code = """void process() {
    int result = helper();
    save(result);
}
"""
        file_path = tmp_path / "process.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        calls = entities[0].calls
        assert "helper" in calls
        assert "save" in calls

    def test_parse_multiple_functions(self, tmp_path: Path) -> None:
        """Test parsing multiple functions."""
        code = """int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}
"""
        file_path = tmp_path / "math.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 3
        names = [e.name for e in entities]
        assert "add" in names
        assert "subtract" in names
        assert "multiply" in names

    def test_line_count(self, tmp_path: Path) -> None:
        """Test that line count is returned correctly."""
        code = """int main() {
    printf("Hello");
    return 0;
}
"""
        file_path = tmp_path / "main.c"
        file_path.write_text(code)

        _, line_count = self.parser.parse_file(file_path)

        assert line_count == 5

    def test_parse_encoding_error(self, tmp_path: Path) -> None:
        """Test handling of encoding errors."""
        file_path = tmp_path / "binary.c"
        file_path.write_bytes(b"\x80\x81\x82")

        entities, line_count = self.parser.parse_file(file_path)
        assert entities == []
        assert line_count is None

    def test_entity_ids(self, tmp_path: Path) -> None:
        """Test that entity IDs are correctly formatted."""
        code = """class User {
public:
    void greet() {
    }
};
"""
        file_path = tmp_path / "user.cpp"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        method_entity = next(e for e in entities if e.type == "method")

        assert str(file_path) in class_entity.id
        assert class_entity.id in method_entity.parent_id

    def test_parse_static_function(self, tmp_path: Path) -> None:
        """Test parsing a static function."""
        code = """static int helper() {
    return 42;
}
"""
        file_path = tmp_path / "helper.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "helper"
        assert "static" in entities[0].signature

    def test_parse_pointer_return_type(self, tmp_path: Path) -> None:
        """Test parsing a function with pointer return type."""
        code = """char* get_string() {
    return "hello";
}
"""
        file_path = tmp_path / "string.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "get_string"

    def test_parse_cpp_namespace(self, tmp_path: Path) -> None:
        """Test parsing code in a namespace."""
        code = """namespace MyApp {
    class Service {
    public:
        void run() {
        }
    };
}
"""
        file_path = tmp_path / "service.cpp"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next((e for e in entities if e.type == "class"), None)
        assert class_entity is not None
        assert class_entity.name == "Service"

    def test_parse_doxygen_comment(self, tmp_path: Path) -> None:
        """Test parsing doxygen-style comments."""
        code = """/**
 * Calculate the sum of two numbers.
 * @param a First number
 * @param b Second number
 * @return The sum
 */
int sum(int a, int b) {
    return a + b;
}
"""
        file_path = tmp_path / "sum.c"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert "Calculate the sum" in (entities[0].docstring or "")

    def test_parse_c_vs_cpp_language_detection(self, tmp_path: Path) -> None:
        """Test that .c files are parsed as C and .cpp as C++."""
        c_code = """void hello() {
    printf("Hello");
}
"""
        cpp_code = """void hello() {
    std::cout << "Hello";
}
"""
        c_file = tmp_path / "hello.c"
        c_file.write_text(c_code)
        cpp_file = tmp_path / "hello.cpp"
        cpp_file.write_text(cpp_code)

        c_entities, _ = self.parser.parse_file(c_file)
        cpp_entities, _ = self.parser.parse_file(cpp_file)

        assert c_entities[0].language == "c"
        assert cpp_entities[0].language == "cpp"
