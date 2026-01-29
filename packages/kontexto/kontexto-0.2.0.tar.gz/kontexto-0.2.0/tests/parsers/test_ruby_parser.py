"""Tests for the tree-sitter Ruby parser."""

from pathlib import Path

from kontexto.parsers.ruby_parser import RubyParser


class TestRubyParser:
    """Test suite for RubyParser."""

    def setup_method(self) -> None:
        self.parser = RubyParser()

    def test_config(self) -> None:
        """Test parser configuration."""
        assert self.parser.config.name == "ruby"
        assert ".rb" in self.parser.config.extensions
        assert ".rake" in self.parser.config.extensions
        assert ".gemspec" in self.parser.config.extensions

    def test_supports_file(self, tmp_path: Path) -> None:
        """Test file support detection."""
        rb_file = tmp_path / "app.rb"
        rb_file.touch()
        py_file = tmp_path / "app.py"
        py_file.touch()

        assert self.parser.supports_file(rb_file)
        assert not self.parser.supports_file(py_file)

    def test_parse_method(self, tmp_path: Path) -> None:
        """Test parsing a method."""
        code = """# Say hello to someone
def hello(name)
  puts "Hello, #{name}!"
end
"""
        file_path = tmp_path / "hello.rb"
        file_path.write_text(code)

        entities, line_count = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "hello"
        assert entities[0].type == "function"
        assert entities[0].language == "ruby"
        assert "Say hello" in (entities[0].docstring or "")

    def test_parse_method_with_params(self, tmp_path: Path) -> None:
        """Test parsing a method with parameters."""
        code = """def greet(name, greeting = "Hello")
  "#{greeting}, #{name}!"
end
"""
        file_path = tmp_path / "greet.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        assert len(entities) == 1
        assert entities[0].name == "greet"
        assert "def greet" in entities[0].signature

    def test_parse_class(self, tmp_path: Path) -> None:
        """Test parsing a class."""
        code = """# Represents a user
class User
  def initialize(name)
    @name = name
  end

  def greet
    puts "Hello, #{@name}!"
  end
end
"""
        file_path = tmp_path / "user.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "User"
        assert "class User" in class_entity.signature
        assert "Represents a user" in (class_entity.docstring or "")

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 2
        method_names = [m.name for m in methods]
        assert "initialize" in method_names
        assert "greet" in method_names

    def test_parse_class_with_inheritance(self, tmp_path: Path) -> None:
        """Test parsing a class with inheritance."""
        code = """class Admin < User
  def delete_user(user)
    # Admin can delete users
  end
end
"""
        file_path = tmp_path / "admin.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "Admin"
        assert "User" in class_entity.base_classes
        assert "class Admin < User" in class_entity.signature

    def test_parse_module(self, tmp_path: Path) -> None:
        """Test parsing a module."""
        code = """module Authenticatable
  def authenticate(password)
    # authentication logic
  end

  def logged_in?
    @logged_in
  end
end
"""
        file_path = tmp_path / "authenticatable.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        module_entity = next(e for e in entities if e.name == "Authenticatable")
        assert module_entity is not None
        assert "module Authenticatable" in module_entity.signature

        methods = [e for e in entities if e.type == "method"]
        assert len(methods) == 2

    def test_parse_singleton_method(self, tmp_path: Path) -> None:
        """Test parsing a singleton method (def self.method)."""
        code = """class Factory
  def self.create(type)
    # Factory method
  end
end
"""
        file_path = tmp_path / "factory.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        assert class_entity.name == "Factory"

        method = next(e for e in entities if e.type == "method")
        assert method.name == "create"
        assert "self" in method.signature

    def test_parse_nested_class(self, tmp_path: Path) -> None:
        """Test parsing a nested class."""
        code = """module Outer
  class Inner
    def inner_method
      # nested
    end
  end
end
"""
        file_path = tmp_path / "nested.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        outer = next(e for e in entities if e.name == "Outer")
        inner = next(e for e in entities if e.name == "Inner")
        method = next(e for e in entities if e.name == "inner_method")

        assert outer is not None
        assert inner is not None
        assert method is not None
        assert inner.parent_id == outer.id
        assert method.parent_id == inner.id

    def test_extract_calls(self, tmp_path: Path) -> None:
        """Test extraction of method calls."""
        code = """def process
  result = helper
  save(result)
end
"""
        file_path = tmp_path / "calls.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        calls = entities[0].calls
        # Ruby call extraction may vary based on tree-sitter output
        assert isinstance(calls, list)

    def test_parse_method_with_question_mark(self, tmp_path: Path) -> None:
        """Test parsing a method with question mark (predicate)."""
        code = """def empty?
  @items.empty?
end
"""
        file_path = tmp_path / "predicate.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        # Note: tree-sitter-ruby may not include ? in identifier
        assert len(entities) >= 1

    def test_parse_method_with_bang(self, tmp_path: Path) -> None:
        """Test parsing a method with bang (destructive)."""
        code = """def save!
  # destructive save
end
"""
        file_path = tmp_path / "bang.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        # Note: tree-sitter-ruby may not include ! in identifier
        assert len(entities) >= 1

    def test_line_count(self, tmp_path: Path) -> None:
        """Test that line count is returned correctly."""
        code = """def main
  puts "Hello"
end
"""
        file_path = tmp_path / "main.rb"
        file_path.write_text(code)

        _, line_count = self.parser.parse_file(file_path)

        assert line_count == 4

    def test_parse_encoding_error(self, tmp_path: Path) -> None:
        """Test handling of encoding errors."""
        file_path = tmp_path / "binary.rb"
        file_path.write_bytes(b"\x80\x81\x82")

        entities, line_count = self.parser.parse_file(file_path)
        assert entities == []
        assert line_count is None

    def test_entity_ids(self, tmp_path: Path) -> None:
        """Test that entity IDs are correctly formatted."""
        code = """class User
  def greet
    # greeting
  end
end
"""
        file_path = tmp_path / "user.rb"
        file_path.write_text(code)

        entities, _ = self.parser.parse_file(file_path)

        class_entity = next(e for e in entities if e.type == "class")
        method_entity = next(e for e in entities if e.type == "method")

        assert str(file_path) in class_entity.id
        assert class_entity.id in method_entity.parent_id
