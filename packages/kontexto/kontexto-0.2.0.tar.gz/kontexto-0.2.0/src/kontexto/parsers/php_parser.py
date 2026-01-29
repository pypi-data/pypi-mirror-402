"""Tree-sitter based PHP parser."""

import logging
from pathlib import Path
from typing import Optional

import tree_sitter_php as tsphp
from tree_sitter import Language, Parser, Node

from kontexto.parsers.base import BaseParser, CodeEntity, LanguageConfig

logger = logging.getLogger(__name__)


class PHPParser(BaseParser):
    """Tree-sitter based parser for PHP source files."""

    def __init__(self) -> None:
        # Use language_php() for full PHP files (with <?php tag)
        self._language = Language(tsphp.language_php())
        self._parser = Parser(self._language)

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            name="php",
            extensions=(".php", ".phtml"),
            exclude_patterns=("vendor", "cache", "storage"),
        )

    def parse_file(self, file_path: Path) -> tuple[list[CodeEntity], Optional[int]]:
        """Parse a PHP file and extract all entities."""
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
            # Function definitions
            if child.type == "function_definition":
                entity = self._extract_function(child, content, file_path, parent_id)
                if entity:
                    entities.append(entity)

            # Class declarations
            elif child.type == "class_declaration":
                class_entities = self._extract_class(child, content, file_path, parent_id)
                entities.extend(class_entities)

            # Interface declarations
            elif child.type == "interface_declaration":
                interface_entities = self._extract_interface(child, content, file_path, parent_id)
                entities.extend(interface_entities)

            # Trait declarations
            elif child.type == "trait_declaration":
                trait_entities = self._extract_trait(child, content, file_path, parent_id)
                entities.extend(trait_entities)

            # Enum declarations (PHP 8.1+)
            elif child.type == "enum_declaration":
                enum_entity = self._extract_enum(child, content, file_path)
                if enum_entity:
                    entities.append(enum_entity)

            # Namespace declarations - recurse into namespace body
            elif child.type == "namespace_definition":
                body = self._get_child_by_type(child, "compound_statement")
                if body:
                    self._extract_entities(body, content, file_path, entities, parent_id)
                else:
                    # File-level namespace, continue with siblings
                    pass

            # Recurse into program and compound statements
            elif child.type in ("program", "compound_statement", "php_tag"):
                self._extract_entities(child, content, file_path, entities, parent_id)

    def _extract_function(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> Optional[CodeEntity]:
        """Extract a function definition."""
        name_node = self._get_child_by_type(node, "name")
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
            signature=self._get_function_signature(node),
            docstring=self._get_phpdoc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="php",
        )

    def _extract_method(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: str,
    ) -> Optional[CodeEntity]:
        """Extract a method declaration."""
        name_node = self._get_child_by_type(node, "name")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{parent_id}.{name}"

        # Check if it's a constructor
        entity_type = "constructor" if name == "__construct" else "method"

        return CodeEntity(
            id=entity_id,
            name=name,
            type=entity_type,
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_method_signature(node),
            docstring=self._get_phpdoc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="php",
        )

    def _extract_class(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a class declaration and its methods."""
        name_node = self._get_child_by_type(node, "name")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        class_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        base_classes = self._get_base_classes(node)
        interfaces = self._get_interfaces(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=class_id,
                name=name,
                type="class",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_class_signature(node, name, base_classes, interfaces),
                docstring=self._get_phpdoc(node, content),
                parent_id=parent_id,
                base_classes=base_classes + interfaces,
                language="php",
            )
        )

        # Extract methods from class body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            for child in body.children:
                if child.type == "method_declaration":
                    method = self._extract_method(child, content, file_path, class_id)
                    if method:
                        entities.append(method)

        return entities

    def _extract_interface(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract an interface declaration and its methods."""
        name_node = self._get_child_by_type(node, "name")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        interface_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        # Get extended interfaces
        extends = self._get_interface_extends(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=interface_id,
                name=name,
                type="interface",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=f"interface {name}" + (f" extends {', '.join(extends)}" if extends else ""),
                docstring=self._get_phpdoc(node, content),
                parent_id=parent_id,
                base_classes=extends,
                language="php",
            )
        )

        # Extract method signatures from interface body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            for child in body.children:
                if child.type == "method_declaration":
                    method = self._extract_method(child, content, file_path, interface_id)
                    if method:
                        entities.append(method)

        return entities

    def _extract_trait(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a trait declaration and its methods."""
        name_node = self._get_child_by_type(node, "name")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        trait_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=trait_id,
                name=name,
                type="trait",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=f"trait {name}",
                docstring=self._get_phpdoc(node, content),
                parent_id=parent_id,
                language="php",
            )
        )

        # Extract methods from trait body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            for child in body.children:
                if child.type == "method_declaration":
                    method = self._extract_method(child, content, file_path, trait_id)
                    if method:
                        entities.append(method)

        return entities

    def _extract_enum(
        self,
        node: Node,
        content: bytes,
        file_path: str,
    ) -> Optional[CodeEntity]:
        """Extract an enum declaration (PHP 8.1+)."""
        name_node = self._get_child_by_type(node, "name")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="enum",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=f"enum {name}",
            docstring=self._get_phpdoc(node, content),
            language="php",
        )

    def _get_base_classes(self, node: Node) -> list[str]:
        """Get base class from extends clause."""
        base_clause = self._get_child_by_type(node, "base_clause")
        if base_clause:
            for child in base_clause.children:
                if child.type == "name" and child.text:
                    return [child.text.decode("utf-8")]
                elif child.type == "qualified_name" and child.text:
                    return [child.text.decode("utf-8")]
        return []

    def _get_interfaces(self, node: Node) -> list[str]:
        """Get implemented interfaces from implements clause."""
        interfaces: list[str] = []
        class_interface_clause = self._get_child_by_type(node, "class_interface_clause")
        if class_interface_clause:
            for child in class_interface_clause.children:
                if child.type == "name" and child.text:
                    interfaces.append(child.text.decode("utf-8"))
                elif child.type == "qualified_name" and child.text:
                    interfaces.append(child.text.decode("utf-8"))
        return interfaces

    def _get_interface_extends(self, node: Node) -> list[str]:
        """Get extended interfaces from extends clause."""
        extends: list[str] = []
        base_clause = self._get_child_by_type(node, "base_clause")
        if base_clause:
            for child in base_clause.children:
                if child.type == "name" and child.text:
                    extends.append(child.text.decode("utf-8"))
                elif child.type == "qualified_name" and child.text:
                    extends.append(child.text.decode("utf-8"))
        return extends

    def _get_child_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find the first child node of a given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _get_function_signature(self, node: Node) -> str:
        """Build function signature string."""
        name_node = self._get_child_by_type(node, "name")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        params = self._get_child_by_type(node, "formal_parameters")
        params_text = params.text.decode("utf-8") if params and params.text else "()"

        signature = f"function {name}{params_text}"

        # Get return type (can be various type nodes)
        return_type = self._get_return_type(node)
        if return_type:
            signature += f": {return_type}"

        return signature

    def _get_return_type(self, node: Node) -> Optional[str]:
        """Extract return type from a function/method node."""
        for child in node.children:
            if child.type in ("optional_type", "named_type", "primitive_type", "union_type", "intersection_type"):
                if child.text:
                    return child.text.decode("utf-8")
        return None

    def _get_method_signature(self, node: Node) -> str:
        """Build method signature string."""
        # Get visibility and modifiers
        modifiers: list[str] = []
        for child in node.children:
            if child.type in ("visibility_modifier", "static_modifier", "final_modifier", "abstract_modifier"):
                if child.text:
                    modifiers.append(child.text.decode("utf-8"))

        name_node = self._get_child_by_type(node, "name")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        params = self._get_child_by_type(node, "formal_parameters")
        params_text = params.text.decode("utf-8") if params and params.text else "()"

        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}function {name}{params_text}"

        # Get return type
        return_type = self._get_return_type(node)
        if return_type:
            signature += f": {return_type}"

        return signature.strip()

    def _get_class_signature(self, node: Node, name: str, base_classes: list[str], interfaces: list[str]) -> str:
        """Build class signature string."""
        # Check for modifiers
        modifiers: list[str] = []
        for child in node.children:
            if child.type in ("final_modifier", "abstract_modifier"):
                if child.text:
                    modifiers.append(child.text.decode("utf-8"))

        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}class {name}"

        if base_classes:
            signature += f" extends {base_classes[0]}"
        if interfaces:
            signature += f" implements {', '.join(interfaces)}"

        return signature.strip()

    def _get_phpdoc(self, node: Node, content: bytes) -> Optional[str]:
        """Extract PHPDoc comment before a node."""
        sibling = node.prev_sibling
        while sibling:
            if sibling.type == "comment":
                comment = sibling.text.decode("utf-8") if sibling.text else ""
                if comment.startswith("/**"):
                    # PHPDoc block comment
                    lines = comment[3:-2].strip().split("\n")
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith("*"):
                            line = line[1:].strip()
                        # Skip @param, @return, etc. tags for the docstring
                        if not line.startswith("@"):
                            cleaned_lines.append(line)
                    return " ".join(cleaned_lines).strip() or None
                sibling = sibling.prev_sibling
            else:
                break
        return None

    def _extract_calls(self, node: Node, content: bytes) -> list[str]:
        """Extract function/method calls from a node."""
        calls: set[str] = set()

        def walk(n: Node) -> None:
            if n.type == "function_call_expression":
                # Get the function name
                func = self._get_child_by_type(n, "name")
                if func and func.text:
                    calls.add(func.text.decode("utf-8"))
            elif n.type == "member_call_expression":
                # Get the method name
                method = self._get_child_by_type(n, "name")
                if method and method.text:
                    calls.add(method.text.decode("utf-8"))
            elif n.type == "scoped_call_expression":
                # Static method call
                method = self._get_child_by_type(n, "name")
                if method and method.text:
                    calls.add(method.text.decode("utf-8"))

            for child in n.children:
                walk(child)

        # Walk the function/method body
        body = self._get_child_by_type(node, "compound_statement")
        if body:
            walk(body)

        return list(calls)
