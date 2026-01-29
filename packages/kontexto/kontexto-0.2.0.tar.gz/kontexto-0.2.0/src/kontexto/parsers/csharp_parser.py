"""Tree-sitter based C# parser."""

import logging
from pathlib import Path
from typing import Optional

import tree_sitter_c_sharp as tscs
from tree_sitter import Language, Parser, Node

from kontexto.parsers.base import BaseParser, CodeEntity, LanguageConfig

logger = logging.getLogger(__name__)


class CSharpParser(BaseParser):
    """Tree-sitter based parser for C# source files."""

    def __init__(self) -> None:
        self._language = Language(tscs.language())
        self._parser = Parser(self._language)

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            name="csharp",
            extensions=(".cs",),
            exclude_patterns=("bin", "obj", "packages", ".vs"),
        )

    def parse_file(self, file_path: Path) -> tuple[list[CodeEntity], Optional[int]]:
        """Parse a C# file and extract all entities."""
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
            # Class declarations
            if child.type == "class_declaration":
                class_entities = self._extract_class(child, content, file_path, parent_id)
                entities.extend(class_entities)

            # Interface declarations
            elif child.type == "interface_declaration":
                interface_entities = self._extract_interface(child, content, file_path, parent_id)
                entities.extend(interface_entities)

            # Struct declarations
            elif child.type == "struct_declaration":
                struct_entities = self._extract_struct(child, content, file_path, parent_id)
                entities.extend(struct_entities)

            # Enum declarations
            elif child.type == "enum_declaration":
                enum_entity = self._extract_enum(child, content, file_path)
                if enum_entity:
                    entities.append(enum_entity)

            # Record declarations (C# 9+)
            elif child.type == "record_declaration":
                record_entities = self._extract_record(child, content, file_path, parent_id)
                entities.extend(record_entities)

            # Namespace declarations - recurse into namespace body
            elif child.type == "namespace_declaration":
                body = self._get_child_by_type(child, "declaration_list")
                if body:
                    self._extract_entities(body, content, file_path, entities, parent_id)

            # File-scoped namespace (C# 10+)
            elif child.type == "file_scoped_namespace_declaration":
                self._extract_entities(child, content, file_path, entities, parent_id)

            # Recurse into compilation unit and other containers
            elif child.type in ("compilation_unit", "declaration_list", "global_statement"):
                self._extract_entities(child, content, file_path, entities, parent_id)

    def _extract_class(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a class declaration and its members."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        class_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        base_classes = self._get_base_types(node)
        modifiers = self._get_modifiers(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=class_id,
                name=name,
                type="class",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_class_signature(name, modifiers, base_classes),
                docstring=self._get_xml_doc(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language="csharp",
            )
        )

        # Extract members from class body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            self._extract_class_members(body, content, file_path, entities, class_id)

        return entities

    def _extract_interface(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract an interface declaration and its members."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        interface_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        base_classes = self._get_base_types(node)
        modifiers = self._get_modifiers(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=interface_id,
                name=name,
                type="interface",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_interface_signature(name, modifiers, base_classes),
                docstring=self._get_xml_doc(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language="csharp",
            )
        )

        # Extract members from interface body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            self._extract_class_members(body, content, file_path, entities, interface_id)

        return entities

    def _extract_struct(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a struct declaration and its members."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        struct_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        base_classes = self._get_base_types(node)
        modifiers = self._get_modifiers(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=struct_id,
                name=name,
                type="struct",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_struct_signature(name, modifiers, base_classes),
                docstring=self._get_xml_doc(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language="csharp",
            )
        )

        # Extract members from struct body
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            self._extract_class_members(body, content, file_path, entities, struct_id)

        return entities

    def _extract_record(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
    ) -> list[CodeEntity]:
        """Extract a record declaration (C# 9+)."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return []

        name = name_node.text.decode("utf-8")
        record_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"

        base_classes = self._get_base_types(node)
        modifiers = self._get_modifiers(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=record_id,
                name=name,
                type="class",  # Treat records as classes
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_record_signature(name, modifiers, base_classes),
                docstring=self._get_xml_doc(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language="csharp",
            )
        )

        # Extract members from record body if present
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            self._extract_class_members(body, content, file_path, entities, record_id)

        return entities

    def _extract_enum(
        self,
        node: Node,
        content: bytes,
        file_path: str,
    ) -> Optional[CodeEntity]:
        """Extract an enum declaration."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{file_path}:{name}"
        modifiers = self._get_modifiers(node)

        return CodeEntity(
            id=entity_id,
            name=name,
            type="enum",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_enum_signature(name, modifiers),
            docstring=self._get_xml_doc(node, content),
            language="csharp",
        )

    def _extract_class_members(
        self,
        body: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        parent_id: str,
    ) -> None:
        """Extract members from a class/interface/struct body."""
        for child in body.children:
            # Method declarations
            if child.type == "method_declaration":
                method = self._extract_method(child, content, file_path, parent_id)
                if method:
                    entities.append(method)

            # Constructor declarations
            elif child.type == "constructor_declaration":
                constructor = self._extract_constructor(child, content, file_path, parent_id)
                if constructor:
                    entities.append(constructor)

            # Property declarations
            elif child.type == "property_declaration":
                prop = self._extract_property(child, content, file_path, parent_id)
                if prop:
                    entities.append(prop)

            # Nested classes, interfaces, structs
            elif child.type == "class_declaration":
                nested = self._extract_class(child, content, file_path, parent_id)
                entities.extend(nested)

            elif child.type == "interface_declaration":
                nested = self._extract_interface(child, content, file_path, parent_id)
                entities.extend(nested)

            elif child.type == "struct_declaration":
                nested = self._extract_struct(child, content, file_path, parent_id)
                entities.extend(nested)

    def _extract_method(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: str,
    ) -> Optional[CodeEntity]:
        """Extract a method declaration."""
        # In C#, method_declaration has: modifiers, return_type (identifier), name (identifier), params
        # We need the identifier right before the parameter_list
        name = self._get_method_name(node)
        if not name:
            return None

        entity_id = f"{parent_id}.{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="method",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_method_signature(node),
            docstring=self._get_xml_doc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="csharp",
        )

    def _extract_constructor(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: str,
    ) -> Optional[CodeEntity]:
        """Extract a constructor declaration."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{parent_id}.{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="constructor",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_constructor_signature(node),
            docstring=self._get_xml_doc(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language="csharp",
        )

    def _extract_property(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: str,
    ) -> Optional[CodeEntity]:
        """Extract a property declaration."""
        name_node = self._get_child_by_type(node, "identifier")
        if not name_node or not name_node.text:
            return None

        name = name_node.text.decode("utf-8")
        entity_id = f"{parent_id}.{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="method",  # Treat properties as methods for simplicity
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=self._get_property_signature(node),
            docstring=self._get_xml_doc(node, content),
            parent_id=parent_id,
            language="csharp",
        )

    def _get_base_types(self, node: Node) -> list[str]:
        """Get base classes/interfaces from base_list."""
        base_types: list[str] = []
        base_list = self._get_child_by_type(node, "base_list")
        if base_list:
            for child in base_list.children:
                if child.type in ("identifier", "generic_name", "qualified_name"):
                    if child.text:
                        base_types.append(child.text.decode("utf-8"))
        return base_types

    def _get_modifiers(self, node: Node) -> list[str]:
        """Get modifiers (public, private, static, etc.)."""
        modifiers: list[str] = []
        for child in node.children:
            if child.type == "modifier" and child.text:
                modifiers.append(child.text.decode("utf-8"))
        return modifiers

    def _get_child_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find the first child node of a given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _get_method_name(self, node: Node) -> Optional[str]:
        """Get the method name from a method_declaration node.

        In C#, method_declaration has the pattern: modifiers type name(params)
        The name is the identifier that comes right before the parameter_list.
        """
        # Find the parameter_list and get the identifier before it
        prev_identifier = None
        for child in node.children:
            if child.type == "identifier" and child.text:
                prev_identifier = child.text.decode("utf-8")
            elif child.type == "parameter_list":
                # The identifier just before parameter_list is the method name
                return prev_identifier
        return prev_identifier

    def _get_class_signature(self, name: str, modifiers: list[str], base_classes: list[str]) -> str:
        """Build class signature string."""
        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}class {name}"
        if base_classes:
            signature += f" : {', '.join(base_classes)}"
        return signature.strip()

    def _get_interface_signature(self, name: str, modifiers: list[str], base_classes: list[str]) -> str:
        """Build interface signature string."""
        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}interface {name}"
        if base_classes:
            signature += f" : {', '.join(base_classes)}"
        return signature.strip()

    def _get_struct_signature(self, name: str, modifiers: list[str], base_classes: list[str]) -> str:
        """Build struct signature string."""
        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}struct {name}"
        if base_classes:
            signature += f" : {', '.join(base_classes)}"
        return signature.strip()

    def _get_record_signature(self, name: str, modifiers: list[str], base_classes: list[str]) -> str:
        """Build record signature string."""
        prefix = " ".join(modifiers) + " " if modifiers else ""
        signature = f"{prefix}record {name}"
        if base_classes:
            signature += f" : {', '.join(base_classes)}"
        return signature.strip()

    def _get_enum_signature(self, name: str, modifiers: list[str]) -> str:
        """Build enum signature string."""
        prefix = " ".join(modifiers) + " " if modifiers else ""
        return f"{prefix}enum {name}".strip()

    def _get_method_signature(self, node: Node) -> str:
        """Build method signature string."""
        modifiers = self._get_modifiers(node)

        # Get return type
        return_type = ""
        for child in node.children:
            if child.type in ("predefined_type", "identifier", "generic_name", "nullable_type", "array_type", "void_keyword"):
                if child.text:
                    return_type = child.text.decode("utf-8")
                    break

        name_node = self._get_child_by_type(node, "identifier")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        params = self._get_child_by_type(node, "parameter_list")
        params_text = params.text.decode("utf-8") if params and params.text else "()"

        prefix = " ".join(modifiers) + " " if modifiers else ""
        return f"{prefix}{return_type} {name}{params_text}".strip()

    def _get_constructor_signature(self, node: Node) -> str:
        """Build constructor signature string."""
        modifiers = self._get_modifiers(node)

        name_node = self._get_child_by_type(node, "identifier")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        params = self._get_child_by_type(node, "parameter_list")
        params_text = params.text.decode("utf-8") if params and params.text else "()"

        prefix = " ".join(modifiers) + " " if modifiers else ""
        return f"{prefix}{name}{params_text}".strip()

    def _get_property_signature(self, node: Node) -> str:
        """Build property signature string."""
        modifiers = self._get_modifiers(node)

        # Get type
        prop_type = ""
        for child in node.children:
            if child.type in ("predefined_type", "identifier", "generic_name", "nullable_type", "array_type"):
                if child.text:
                    prop_type = child.text.decode("utf-8")
                    break

        name_node = self._get_child_by_type(node, "identifier")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else ""

        prefix = " ".join(modifiers) + " " if modifiers else ""
        return f"{prefix}{prop_type} {name} {{ get; set; }}".strip()

    def _get_xml_doc(self, node: Node, content: bytes) -> Optional[str]:
        """Extract XML documentation comment before a node."""
        comments: list[str] = []

        sibling = node.prev_sibling
        while sibling:
            if sibling.type == "comment":
                comment = sibling.text.decode("utf-8") if sibling.text else ""
                # Check for XML doc comment (///)
                if comment.strip().startswith("///"):
                    line = comment.strip()[3:].strip()
                    # Extract content from XML tags
                    if line.startswith("<summary>"):
                        line = line[9:]
                    if line.endswith("</summary>"):
                        line = line[:-10]
                    if line and not line.startswith("<") and not line.endswith(">"):
                        comments.insert(0, line.strip())
                sibling = sibling.prev_sibling
            else:
                break

        return " ".join(comments).strip() if comments else None

    def _extract_calls(self, node: Node, content: bytes) -> list[str]:
        """Extract method calls from a node."""
        calls: set[str] = set()

        def walk(n: Node) -> None:
            if n.type == "invocation_expression":
                # Get the method name
                for child in n.children:
                    if child.type == "identifier" and child.text:
                        calls.add(child.text.decode("utf-8"))
                    elif child.type == "member_access_expression":
                        # Get the last identifier (method name)
                        name = self._get_child_by_type(child, "identifier")
                        if name and name.text:
                            calls.add(name.text.decode("utf-8"))

            for child in n.children:
                walk(child)

        # Walk the method body
        body = self._get_child_by_type(node, "block")
        if body:
            walk(body)

        return list(calls)
