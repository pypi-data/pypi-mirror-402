"""Tests for the tree-sitter C# parser."""

from pathlib import Path

from kontexto.parsers.csharp_parser import CSharpParser


class TestCSharpParser:
    """Test suite for CSharpParser."""

    def setup_method(self) -> None:
        self.parser = CSharpParser()

    def test_config(self) -> None:
        """Test parser configuration."""
        assert self.parser.config.name == "csharp"
        assert ".cs" in self.parser.config.extensions

    def test_supports_file(self, tmp_path: Path) -> None:
        """Test file support detection."""
        cs_file = tmp_path / "Program.cs"
        cs_file.touch()
        py_file = tmp_path / "Program.py"
        py_file.touch()

        assert self.parser.supports_file(cs_file)
        assert not self.parser.supports_file(py_file)

    def test_parse_class(self, tmp_path: Path) -> None:
        """Test parsing a class."""
        code = """/// <summary>
/// Represents a user
/// </summary>
public class User
{
    public string Name { get; set; }

    public void Greet()
    {
        Console.WriteLine("Hello!");
    }
}
"""
        file_path = tmp_path / "User.cs"
        file_path.write_text(code)

        entities, line_count = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "User"
        assert "class User" in class_entity.signature
        assert "public" in class_entity.signature
        assert class_entity.language == "csharp"
        assert "Represents a user" in (class_entity.docstring or "")

    def test_parse_class_with_inheritance(self, tmp_path: Path) -> None:
        """Test parsing a class with inheritance."""
        code = """public class Admin : User
{
    public void DeleteUser(User user)
    {
        // Admin can delete users
    }
}
"""
        file_path = tmp_path / "Admin.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "Admin"
        assert "User" in class_entity.base_classes
        assert ": User" in class_entity.signature

    def test_parse_class_with_interface(self, tmp_path: Path) -> None:
        """Test parsing a class implementing interfaces."""
        code = """public class UserService : IUserService, IDisposable
{
    public User GetUser(int id)
    {
        return new User();
    }
}
"""
        file_path = tmp_path / "UserService.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "UserService"
        assert "IUserService" in class_entity.base_classes or "IDisposable" in class_entity.base_classes

    def test_parse_interface(self, tmp_path: Path) -> None:
        """Test parsing an interface."""
        code = """public interface IUserService
{
    User GetUser(int id);
    void SaveUser(User user);
}
"""
        file_path = tmp_path / "IUserService.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        interface_entity = next(e for e in entities if e.type == "interface")
        assert interface_entity.name == "IUserService"
        assert "interface IUserService" in interface_entity.signature

        methods = [e for e in entities if e.type == "method" and "get;" not in (e.signature or "")]
        assert len(methods) >= 2

    def test_parse_interface_extends(self, tmp_path: Path) -> None:
        """Test parsing an interface that extends another."""
        code = """public interface IAdminService : IUserService
{
    void DeleteUser(int id);
}
"""
        file_path = tmp_path / "IAdminService.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        interface_entity = next(e for e in entities if e.type == "interface")
        assert interface_entity.name == "IAdminService"
        assert "IUserService" in interface_entity.base_classes

    def test_parse_struct(self, tmp_path: Path) -> None:
        """Test parsing a struct."""
        code = """public struct Point
{
    public int X { get; set; }
    public int Y { get; set; }

    public double Distance()
    {
        return Math.Sqrt(X * X + Y * Y);
    }
}
"""
        file_path = tmp_path / "Point.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        struct_entity = next(e for e in entities if e.type == "struct")
        assert struct_entity.name == "Point"
        assert "struct Point" in struct_entity.signature

    def test_parse_enum(self, tmp_path: Path) -> None:
        """Test parsing an enum."""
        code = """public enum Color
{
    Red,
    Green,
    Blue
}
"""
        file_path = tmp_path / "Color.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        enum_entity = next(e for e in entities if e.type == "enum")
        assert enum_entity.name == "Color"
        assert "enum Color" in enum_entity.signature

    def test_parse_method(self, tmp_path: Path) -> None:
        """Test parsing a method."""
        code = """public class Calculator
{
    public int Add(int a, int b)
    {
        return a + b;
    }
}
"""
        file_path = tmp_path / "Calculator.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        method = next(e for e in entities if e.type == "method" and e.name == "Add")
        assert method.name == "Add"
        assert "Add" in method.signature
        assert "int" in method.signature

    def test_parse_constructor(self, tmp_path: Path) -> None:
        """Test parsing a constructor."""
        code = """public class User
{
    public User(string name)
    {
        Name = name;
    }

    public string Name { get; set; }
}
"""
        file_path = tmp_path / "User.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        constructor = next(e for e in entities if e.type == "constructor")
        assert constructor.name == "User"
        assert "User" in constructor.signature

    def test_parse_property(self, tmp_path: Path) -> None:
        """Test parsing a property."""
        code = """public class Person
{
    public string Name { get; set; }
    public int Age { get; private set; }
}
"""
        file_path = tmp_path / "Person.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        properties = [e for e in entities if "get;" in (e.signature or "")]
        assert len(properties) >= 1

    def test_parse_static_method(self, tmp_path: Path) -> None:
        """Test parsing a static method."""
        code = """public class Factory
{
    public static User Create(string name)
    {
        return new User(name);
    }
}
"""
        file_path = tmp_path / "Factory.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        method = next(e for e in entities if e.type == "method")
        assert method.name == "Create"
        assert "static" in method.signature

    def test_parse_async_method(self, tmp_path: Path) -> None:
        """Test parsing an async method."""
        code = """public class Repository
{
    public async Task<User> GetUserAsync(int id)
    {
        return await Task.FromResult(new User());
    }
}
"""
        file_path = tmp_path / "Repository.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        method = next(e for e in entities if e.type == "method")
        assert method.name == "GetUserAsync"
        assert "async" in method.signature

    def test_parse_abstract_class(self, tmp_path: Path) -> None:
        """Test parsing an abstract class."""
        code = """public abstract class BaseModel
{
    public abstract void Save();

    public virtual void Validate()
    {
        // Default validation
    }
}
"""
        file_path = tmp_path / "BaseModel.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "BaseModel"
        assert "abstract" in class_entity.signature

    def test_parse_nested_class(self, tmp_path: Path) -> None:
        """Test parsing a nested class."""
        code = """public class Outer
{
    public class Inner
    {
        public void InnerMethod()
        {
        }
    }
}
"""
        file_path = tmp_path / "Nested.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        outer = next(e for e in entities if e.name == "Outer")
        inner = next(e for e in entities if e.name == "Inner")
        method = next(e for e in entities if e.name == "InnerMethod")

        assert outer is not None
        assert inner is not None
        assert method is not None
        assert inner.parent_id == outer.id
        assert method.parent_id == inner.id

    def test_extract_calls(self, tmp_path: Path) -> None:
        """Test extraction of method calls."""
        code = """public class Processor
{
    public void Process()
    {
        var result = Helper();
        Save(result);
    }

    private int Helper() => 42;
    private void Save(int value) { }
}
"""
        file_path = tmp_path / "Processor.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        process_method = next(e for e in entities if e.name == "Process")
        calls = process_method.calls
        assert "Helper" in calls
        assert "Save" in calls

    def test_line_count(self, tmp_path: Path) -> None:
        """Test that line count is returned correctly."""
        code = """public class Main
{
    static void Main()
    {
        Console.WriteLine("Hello");
    }
}
"""
        file_path = tmp_path / "Program.cs"
        file_path.write_text(code)

        _, line_count = self.parser.parse_file(file_path)

        assert line_count == 8

    def test_parse_encoding_error(self, tmp_path: Path) -> None:
        """Test handling of encoding errors."""
        file_path = tmp_path / "binary.cs"
        file_path.write_bytes(b"\x80\x81\x82")

        entities, line_count = self.parser.parse_file(file_path)
        assert entities == []
        assert line_count is None

    def test_entity_ids(self, tmp_path: Path) -> None:
        """Test that entity IDs are correctly formatted."""
        code = """public class User
{
    public void Greet()
    {
    }
}
"""
        file_path = tmp_path / "User.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        method_entity = next(e for e in entities if e.type == "method")

        assert str(file_path) in class_entity.id
        assert class_entity.id in method_entity.parent_id

    def test_parse_namespace(self, tmp_path: Path) -> None:
        """Test parsing code with namespace."""
        code = """namespace MyApp.Controllers
{
    public class UserController
    {
        public void Index()
        {
        }
    }
}
"""
        file_path = tmp_path / "UserController.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "UserController"

    def test_parse_generic_class(self, tmp_path: Path) -> None:
        """Test parsing a generic class."""
        code = """public class Repository<T> where T : class
{
    public T Find(int id)
    {
        return default;
    }
}
"""
        file_path = tmp_path / "Repository.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        # Should parse without errors
        assert len(entities) >= 1

    def test_parse_partial_class(self, tmp_path: Path) -> None:
        """Test parsing a partial class."""
        code = """public partial class User
{
    public string Name { get; set; }
}
"""
        file_path = tmp_path / "User.cs"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "User"
        assert "partial" in class_entity.signature
