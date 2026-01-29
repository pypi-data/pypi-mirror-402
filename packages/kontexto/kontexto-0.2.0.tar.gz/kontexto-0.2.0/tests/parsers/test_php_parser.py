"""Tests for the tree-sitter PHP parser."""

from pathlib import Path

from kontexto.parsers.php_parser import PHPParser


class TestPHPParser:
    """Test suite for PHPParser."""

    def setup_method(self) -> None:
        self.parser = PHPParser()

    def test_config(self) -> None:
        """Test parser configuration."""
        assert self.parser.config.name == "php"
        assert ".php" in self.parser.config.extensions
        assert ".phtml" in self.parser.config.extensions

    def test_supports_file(self, tmp_path: Path) -> None:
        """Test file support detection."""
        php_file = tmp_path / "app.php"
        php_file.touch()
        py_file = tmp_path / "app.py"
        py_file.touch()

        assert self.parser.supports_file(php_file)
        assert not self.parser.supports_file(py_file)

    def test_parse_function(self, tmp_path: Path) -> None:
        """Test parsing a function."""
        code = """<?php
/**
 * Say hello to someone
 */
function hello($name) {
    echo "Hello, $name!";
}
"""
        file_path = tmp_path / "hello.php"
        file_path.write_text(code)

        entities, line_count = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "hello"
        assert entities[0].type == "function"
        assert entities[0].language == "php"
        assert "Say hello" in (entities[0].docstring or "")

    def test_parse_function_with_types(self, tmp_path: Path) -> None:
        """Test parsing a function with type hints."""
        code = """<?php
function greet(string $name, string $greeting = "Hello"): string {
    return "$greeting, $name!";
}
"""
        file_path = tmp_path / "greet.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "greet"
        assert "function greet" in entities[0].signature
        assert "string" in entities[0].signature

    def test_parse_class(self, tmp_path: Path) -> None:
        """Test parsing a class."""
        code = """<?php
/**
 * Represents a user
 */
class User {
    public function __construct($name) {
        $this->name = $name;
    }

    public function greet() {
        echo "Hello, " . $this->name . "!";
    }
}
"""
        file_path = tmp_path / "User.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "User"
        assert "class User" in class_entity.signature
        assert "Represents a user" in (class_entity.docstring or "")

        # Check for constructor
        constructor = next((e for e in entities if e.type == "constructor"), None)
        assert constructor is not None
        assert constructor.name == "__construct"

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 1
        assert methods[0].name == "greet"

    def test_parse_class_with_inheritance(self, tmp_path: Path) -> None:
        """Test parsing a class with inheritance."""
        code = """<?php
class Admin extends User {
    public function deleteUser($user) {
        // Admin can delete users
    }
}
"""
        file_path = tmp_path / "Admin.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "Admin"
        assert "User" in class_entity.base_classes
        assert "extends User" in class_entity.signature

    def test_parse_class_with_implements(self, tmp_path: Path) -> None:
        """Test parsing a class with interface implementation."""
        code = """<?php
class UserService implements UserInterface, Serializable {
    public function getUser($id) {
        return new User($id);
    }
}
"""
        file_path = tmp_path / "UserService.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "UserService"
        assert "UserInterface" in class_entity.base_classes
        assert "implements" in class_entity.signature

    def test_parse_interface(self, tmp_path: Path) -> None:
        """Test parsing an interface."""
        code = """<?php
interface UserInterface {
    public function getUser($id);
    public function saveUser($user);
}
"""
        file_path = tmp_path / "UserInterface.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        interface_entity = next(e for e in entities if e.type == "interface")
        assert interface_entity.name == "UserInterface"
        assert "interface UserInterface" in interface_entity.signature

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 2

    def test_parse_interface_extends(self, tmp_path: Path) -> None:
        """Test parsing an interface that extends another."""
        code = """<?php
interface AdminInterface extends UserInterface {
    public function deleteUser($id);
}
"""
        file_path = tmp_path / "AdminInterface.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        interface_entity = next(e for e in entities if e.type == "interface")
        assert interface_entity.name == "AdminInterface"
        assert "UserInterface" in interface_entity.base_classes
        assert "extends" in interface_entity.signature

    def test_parse_trait(self, tmp_path: Path) -> None:
        """Test parsing a trait."""
        code = """<?php
trait Authenticatable {
    public function authenticate($password) {
        // authentication logic
    }

    public function isLoggedIn() {
        return $this->loggedIn;
    }
}
"""
        file_path = tmp_path / "Authenticatable.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        trait_entity = next(e for e in entities if e.type == "trait")
        assert trait_entity.name == "Authenticatable"
        assert "trait Authenticatable" in trait_entity.signature

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 2

    def test_parse_abstract_class(self, tmp_path: Path) -> None:
        """Test parsing an abstract class."""
        code = """<?php
abstract class BaseModel {
    abstract public function save();

    public function validate() {
        return true;
    }
}
"""
        file_path = tmp_path / "BaseModel.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "BaseModel"
        assert "abstract" in class_entity.signature

    def test_parse_final_class(self, tmp_path: Path) -> None:
        """Test parsing a final class."""
        code = """<?php
final class Singleton {
    private static $instance;

    public static function getInstance() {
        return self::$instance;
    }
}
"""
        file_path = tmp_path / "Singleton.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "Singleton"
        assert "final" in class_entity.signature

    def test_parse_static_method(self, tmp_path: Path) -> None:
        """Test parsing a static method."""
        code = """<?php
class Factory {
    public static function create($type) {
        return new $type();
    }
}
"""
        file_path = tmp_path / "Factory.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        method = next(e for e in entities if e.type == "method")
        assert method.name == "create"
        assert "static" in method.signature

    def test_parse_visibility_modifiers(self, tmp_path: Path) -> None:
        """Test parsing methods with different visibility modifiers."""
        code = """<?php
class Example {
    public function publicMethod() {}
    protected function protectedMethod() {}
    private function privateMethod() {}
}
"""
        file_path = tmp_path / "Example.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 3

        public_method = next(e for e in methods if e.name == "publicMethod")
        assert "public" in public_method.signature

        protected_method = next(e for e in methods if e.name == "protectedMethod")
        assert "protected" in protected_method.signature

        private_method = next(e for e in methods if e.name == "privateMethod")
        assert "private" in private_method.signature

    def test_extract_calls(self, tmp_path: Path) -> None:
        """Test extraction of function/method calls."""
        code = """<?php
function process() {
    $result = helper();
    save($result);
    return $result;
}
"""
        file_path = tmp_path / "calls.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        calls = entities[0].calls
        assert "helper" in calls
        assert "save" in calls

    def test_line_count(self, tmp_path: Path) -> None:
        """Test that line count is returned correctly."""
        code = """<?php
function main() {
    echo "Hello";
}
"""
        file_path = tmp_path / "main.php"
        file_path.write_text(code)

        _, line_count = self.parser.parse_file(file_path)

        assert line_count == 5

    def test_parse_encoding_error(self, tmp_path: Path) -> None:
        """Test handling of encoding errors."""
        file_path = tmp_path / "binary.php"
        file_path.write_bytes(b"\x80\x81\x82")

        entities, line_count = self.parser.parse_file(file_path)
        assert entities == []
        assert line_count is None

    def test_entity_ids(self, tmp_path: Path) -> None:
        """Test that entity IDs are correctly formatted."""
        code = """<?php
class User {
    public function greet() {
        // greeting
    }
}
"""
        file_path = tmp_path / "User.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        method_entity = next(e for e in entities if e.type == "method")

        assert str(file_path) in class_entity.id
        assert class_entity.id in method_entity.parent_id

    def test_parse_namespace(self, tmp_path: Path) -> None:
        """Test parsing code with namespace."""
        code = """<?php
namespace App\\Controllers;

class UserController {
    public function index() {
        return [];
    }
}
"""
        file_path = tmp_path / "UserController.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "UserController"

    def test_parse_method_return_type(self, tmp_path: Path) -> None:
        """Test parsing methods with return types."""
        code = """<?php
class Repository {
    public function find(int $id): ?User {
        return null;
    }

    public function all(): array {
        return [];
    }
}
"""
        file_path = tmp_path / "Repository.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        methods = [e for e in entities if e.type == "method"]
        find_method = next(e for e in methods if e.name == "find")
        all_method = next(e for e in methods if e.name == "all")

        assert "User" in find_method.signature or "?" in find_method.signature
        assert "array" in all_method.signature

    def test_parse_enum(self, tmp_path: Path) -> None:
        """Test parsing an enum (PHP 8.1+)."""
        code = """<?php
enum Status: string {
    case Pending = 'pending';
    case Active = 'active';
    case Inactive = 'inactive';
}
"""
        file_path = tmp_path / "Status.php"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        enum_entity = next((e for e in entities if e.type == "enum"), None)
        assert enum_entity is not None
        assert enum_entity.name == "Status"
        assert "enum Status" in enum_entity.signature
        assert enum_entity.language == "php"
