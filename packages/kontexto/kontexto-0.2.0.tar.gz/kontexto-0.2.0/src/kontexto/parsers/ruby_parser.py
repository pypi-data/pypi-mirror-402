"""Tree-sitter based Ruby parser."""

import logging
from pathlib import Path
from typing import Optional

import tree_sitter_ruby as tsruby
from tree_sitter import Language, Parser, Node

from kontexto.parsers.base import BaseParser, CodeEntity, LanguageConfig

logger = logging.getLogger(__name__)


class RubyParser(BaseParser):
    """Tree-sitter based parser for Ruby source files."""

    def __init__(self) -> None:
        self._language = Language(tsruby.language())
        self._parser = Parser(self._language)

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            name="ruby",
            extensions=(".rb", ".rake", ".gemspec"),
            exclude_patterns=(".bundle", "vendor/bundle", "tmp"),
        )

    def parse_file(self, file_path: Path) -> tuple[list[CodeEntity], Optional[int]]:
        """Parse a Ruby file and extract all entities."""
        try:
            content = file_path.read_bytes()
            text = content.decode("utf-8")
            tree = self._parser.parse(content)
            line_count = text.count("\n") + 1
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error in {file_path}: {e}")
            return [], None
        except Exception as e:
            logger.warning(f"Parse error in {file_path}: {e}")
            return [], None

        entities: list[CodeEntity] = []
        rel_path = str(file_path)

        self._extract_entities(tree.root_node, content, rel_path, entities)

        return entities, line_count

    def _extract_entities(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        parent_id: Optional[str] = None,
    ) -> None:
        """Recursively extract entities from the AST."""
        for child in node.children:
            # Method definitions (def)
            if child.type == "method":
                entity = self._extract_method(child, content, file_path, parent_id)
                if entity:
                    entities.append(entity)

            # Singleton methods (def self.method)
            elif child.type == "singleton_method":
                entity = self._extract_singleton_method(child, content, file_path, parent_id)
                if entity:
                    entities.append(entity)

            # Class definitions
            elif child.type == "class":
                class_entities = self._extract_class(child, content, file_path, parent_id)
                entities.extend(class_entities)

            # Module definitions
            elif child.type == "module":
                module_entities = self._extract_module(child, content, file_path, parent_id)
                entities.extend(module_entities)

            # Singleton class (class << self)
            elif child.type == "singleton_class":
                self._extract_singleton_class(child, content, file_path, entities, parent_id)

            # Recurse into other nodes that might contain definitions
            elif child.type in ("program", "body_statement", "begin"):
                self._extract_entities(child, content, file_path, entities, parent_id)

    def _extract_method(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> Optional[CodeEntity]:
        """Extract a method definition."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_type = "method" if parent_id else "function"
        entity_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type=entity_type,
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_method_signature(node),
            docstring=self._get_ruby_doc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="ruby",
        )

    def _extract_singleton_method(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> Optional[CodeEntity]:
        """Extract a singleton method (def self.method)."""
        # The name is after 'self' or the object
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="method",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_singleton_method_signature(node),
            docstring=self._get_ruby_doc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="ruby",
        )

    def _extract_class(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a class definition and its methods."""
        # Get class name - could be constant or scope_resolution
        name = self._get_class_name(node)
        if not name:
            return []

        class_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"
        base_classes = self._get_superclass(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=class_id,
                name=name,
                type="class",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_class_signature(node, name, base_classes),
                docstring=self._get_ruby_doc(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language="ruby",
            )
        )

        # Extract methods from class body
        body = self._get_child_by_type(node, "body_statement")
        if body:
            self._extract_entities(body, content, file_path, entities, class_id)

        return entities

    def _extract_module(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a module definition and its methods."""
        name = self._get_module_name(node)
        if not name:
            return []

        module_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=module_id,
                name=name,
                type="class",  # Treat modules as classes for hierarchy purposes
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=f"module {name}",
                docstring=self._get_ruby_doc(node, content),
                parent_id=parent_id,
                language="ruby",
            )
        )

        # Extract methods from module body
        body = self._get_child_by_type(node, "body_statement")
        if body:
            self._extract_entities(body, content, file_path, entities, module_id)

        return entities

    def _extract_singleton_class(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        parent_id: Optional[str],
    ) -> None:
        """Extract entities from a singleton class (class << self)."""
        body = self._get_child_by_type(node, "body_statement")
        if body:
            self._extract_entities(body, content, file_path, entities, parent_id)

    def _get_class_name(self, node: Node) -> Optional[str]:
        """Get the class name from a class node."""
        # Could be a constant or scope_resolution (Module::Class)
        for child in node.children:
            if child.type == "constant" and child.text:
                return child.text.decode("utf-8")
            elif child.type == "scope_resolution" and child.text:
                return child.text.decode("utf-8")
        return None

    def _get_module_name(self, node: Node) -> Optional[str]:
        """Get the module name from a module node."""
        for child in node.children:
            if child.type == "constant" and child.text:
                return child.text.decode("utf-8")
            elif child.type == "scope_resolution" and child.text:
                return child.text.decode("utf-8")
        return None

    def _get_superclass(self, node: Node) -> list[str]:
        """Get the superclass from a class node."""
        superclass = self._get_child_by_type(node, "superclass")
        if superclass:
            for child in superclass.children:
                if child.type == "constant" and child.text:
                    return [child.text.decode("utf-8")]
                elif child.type == "scope_resolution" and child.text:
                    return [child.text.decode("utf-8")]
        return []

    def _get_child_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find the first child node of a given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _get_method_signature(self, node: Node) -> str:
        """Build method signature string."""
        name_node = self._get_child_by_type(node, "identifier")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        params = self._get_child_by_type(node, "method_parameters")
        if params and params.text:
            params_text = params.text.decode("utf-8")
            return f"def {name}{params_text}"

        return f"def {name}"

    def _get_singleton_method_signature(self, node: Node) -> str:
        """Build singleton method signature string."""
        name_node = self._get_child_by_type(node, "identifier")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        # Get the object (usually 'self')
        obj = self._get_child_by_type(node, "self")
        obj_name = "self" if obj else ""

        params = self._get_child_by_type(node, "method_parameters")
        if params and params.text:
            params_text = params.text.decode("utf-8")
            return f"def {obj_name}.{name}{params_text}"

        return f"def {obj_name}.{name}"

    def _get_class_signature(self, node: Node, name: str, base_classes: list[str]) -> str:
        """Build class signature string."""
        if base_classes:
            return f"class {name} < {base_classes[0]}"
        return f"class {name}"

    def _get_ruby_doc(self, node: Node, content: bytes) -> Optional[str]:
        """Extract YARD-style documentation comment before a node."""
        comments: list[str] = []

        sibling = node.prev_sibling
        while sibling:
            if sibling.type == "comment":
                comment = sibling.text.decode("utf-8") if sibling.text else ""
                # Strip the # prefix
                if comment.startswith("#"):
                    comment = comment[1:].strip()
                    comments.insert(0, comment)
                sibling = sibling.prev_sibling
            else:
                break

        return " ".join(comments) if comments else None

    def _extract_calls(self, node: Node, content: bytes) -> list[str]:
        """Extract method calls from a node."""
        calls: set[str] = set()

        def walk(n: Node) -> None:
            if n.type == "call":
                # Method call: obj.method or method
                method_node = self._get_child_by_type(n, "identifier")
                if method_node and method_node.text:
                    calls.add(method_node.text.decode("utf-8"))
            elif n.type == "identifier":
                # Could be a bare method call
                parent = n.parent
                if parent and parent.type == "call":
                    if n.text:
                        calls.add(n.text.decode("utf-8"))

            for child in n.children:
                walk(child)

        # Walk the method body
        body = self._get_child_by_type(node, "body_statement")
        if body:
            walk(body)

        return list(calls)
