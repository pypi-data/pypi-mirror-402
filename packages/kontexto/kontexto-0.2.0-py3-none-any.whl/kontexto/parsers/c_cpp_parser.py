"""Tree-sitter based C/C++ parser."""

import logging
from pathlib import Path
from typing import Optional

import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser, Node

from kontexto.parsers.base import BaseParser, CodeEntity, LanguageConfig

logger = logging.getLogger(__name__)


class CCppParser(BaseParser):
    """Tree-sitter based parser for C and C++ source files."""

    def __init__(self) -> None:
        self._c_language = Language(tsc.language())
        self._cpp_language = Language(tscpp.language())
        self._parser = Parser(self._cpp_language)  # Default to C++

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            name="c_cpp",
            extensions=(".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hxx", ".hh"),
            exclude_patterns=("build", "cmake-build-debug", "cmake-build-release"),
        )

    def parse_file(self, file_path: Path) -> tuple[list[CodeEntity], Optional[int]]:
        """Parse a C/C++ file and extract all entities."""
        try:
            content = file_path.read_bytes()
            text = content.decode("utf-8")

            # Use C++ parser for C++ files, C parser for .c files
            ext = file_path.suffix.lower()
            if ext in (".cpp", ".hpp", ".cc", ".cxx", ".hxx", ".hh"):
                self._parser.language = self._cpp_language
                lang = "cpp"
            else:
                # For .c and .h files, use C parser
                self._parser.language = self._c_language
                lang = "c"

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

        self._extract_entities(tree.root_node, content, rel_path, entities, None, lang)

        return entities, line_count

    def _extract_entities(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        parent_id: Optional[str],
        lang: str,
    ) -> None:
        """Recursively extract entities from the AST."""
        for child in node.children:
            # Function definitions
            if child.type == "function_definition":
                entity = self._extract_function(child, content, file_path, parent_id, lang)
                if entity:
                    entities.append(entity)

            # Struct definitions (C and C++)
            elif child.type == "struct_specifier":
                struct_entity = self._extract_struct(child, content, file_path, lang)
                if struct_entity:
                    entities.append(struct_entity)

            # Enum definitions
            elif child.type == "enum_specifier":
                enum_entity = self._extract_enum(child, content, file_path, lang)
                if enum_entity:
                    entities.append(enum_entity)

            # Type definitions (typedef)
            elif child.type == "type_definition":
                typedef_entity = self._extract_typedef(child, content, file_path, lang)
                if typedef_entity:
                    entities.append(typedef_entity)

            # C++ specific: class specifier
            elif child.type == "class_specifier":
                class_entities = self._extract_class(child, content, file_path, parent_id, lang)
                entities.extend(class_entities)

            # C++ specific: namespace definition
            elif child.type == "namespace_definition":
                self._extract_namespace(child, content, file_path, entities, lang)

            # C++ specific: template declaration (wraps functions/classes)
            elif child.type == "template_declaration":
                self._extract_entities(child, content, file_path, entities, parent_id, lang)

            # Declaration (could contain function declarations)
            elif child.type == "declaration":
                # Check if it's a function declaration (forward declaration)
                self._extract_entities(child, content, file_path, entities, parent_id, lang)

            # Recurse into translation unit and preprocessor blocks
            elif child.type in ("translation_unit", "preproc_ifdef", "preproc_if", "preproc_else"):
                self._extract_entities(child, content, file_path, entities, parent_id, lang)

    def _extract_function(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
        lang: str,
    ) -> Optional[CodeEntity]:
        """Extract a function definition."""
        name = self._get_function_name(node)
        if not name:
            return None

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
            docstring=self._get_c_comment(node, content),
            parent_id=parent_id,
            calls=self._extract_calls(node, content),
            language=lang,
        )

    def _extract_struct(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        lang: str,
    ) -> Optional[CodeEntity]:
        """Extract a struct definition."""
        name = self._get_struct_name(node)
        if not name:
            return None

        entity_id = f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="struct",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=f"struct {name}",
            docstring=self._get_c_comment(node, content),
            language=lang,
        )

    def _extract_enum(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        lang: str,
    ) -> Optional[CodeEntity]:
        """Extract an enum definition."""
        name = self._get_enum_name(node)
        if not name:
            return None

        entity_id = f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="enum",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=f"enum {name}",
            docstring=self._get_c_comment(node, content),
            language=lang,
        )

    def _extract_typedef(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        lang: str,
    ) -> Optional[CodeEntity]:
        """Extract a typedef."""
        # Get the name from the type_identifier at the end
        name = None
        for child in node.children:
            if child.type == "type_identifier" and child.text:
                name = child.text.decode("utf-8")

        if not name:
            return None

        entity_id = f"{file_path}:{name}"

        return CodeEntity(
            id=entity_id,
            name=name,
            type="type",
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=f"typedef ... {name}",
            docstring=self._get_c_comment(node, content),
            language=lang,
        )

    def _extract_class(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        parent_id: Optional[str],
        lang: str,
    ) -> list[CodeEntity]:
        """Extract a C++ class and its members."""
        name = self._get_class_name(node)
        if not name:
            return []

        class_id = f"{parent_id}.{name}" if parent_id else f"{file_path}:{name}"
        base_classes = self._get_base_classes(node)

        entities: list[CodeEntity] = []

        entities.append(
            CodeEntity(
                id=class_id,
                name=name,
                type="class",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                signature=self._get_class_signature(name, base_classes),
                docstring=self._get_c_comment(node, content),
                parent_id=parent_id,
                base_classes=base_classes,
                language=lang,
            )
        )

        # Extract methods from class body
        body = self._get_child_by_type(node, "field_declaration_list")
        if body:
            self._extract_class_members(body, content, file_path, entities, class_id, lang)

        return entities

    def _extract_class_members(
        self,
        body: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        parent_id: str,
        lang: str,
    ) -> None:
        """Extract members from a class body."""
        for child in body.children:
            # Function definitions inside class
            if child.type == "function_definition":
                method = self._extract_function(child, content, file_path, parent_id, lang)
                if method:
                    entities.append(method)

            # Access specifier sections (public:, private:, protected:)
            elif child.type == "access_specifier":
                continue

            # Field declarations (might include method declarations)
            elif child.type == "field_declaration":
                # Check if it's a method declaration
                pass

    def _extract_namespace(
        self,
        node: Node,
        content: bytes,
        file_path: str,
        entities: list[CodeEntity],
        lang: str,
    ) -> None:
        """Extract entities from a namespace."""
        # Get the namespace body and recurse
        body = self._get_child_by_type(node, "declaration_list")
        if body:
            self._extract_entities(body, content, file_path, entities, None, lang)

    def _get_function_name(self, node: Node) -> Optional[str]:
        """Get the function name from a function_definition node."""
        # Look for the declarator which contains the function name
        declarator = self._get_child_by_type(node, "function_declarator")
        if not declarator:
            declarator = self._get_child_by_type(node, "pointer_declarator")
            if declarator:
                declarator = self._get_child_by_type(declarator, "function_declarator")

        if declarator:
            # The name is in an identifier or qualified_identifier
            for child in declarator.children:
                if child.type == "identifier" and child.text:
                    return child.text.decode("utf-8")
                elif child.type == "qualified_identifier" and child.text:
                    # Take the last part of the qualified name
                    parts = child.text.decode("utf-8").split("::")
                    return parts[-1]
                elif child.type == "field_identifier" and child.text:
                    return child.text.decode("utf-8")
                elif child.type == "destructor_name" and child.text:
                    return child.text.decode("utf-8")

        return None

    def _get_struct_name(self, node: Node) -> Optional[str]:
        """Get the struct name from a struct_specifier node."""
        for child in node.children:
            if child.type == "type_identifier" and child.text:
                return child.text.decode("utf-8")
        return None

    def _get_enum_name(self, node: Node) -> Optional[str]:
        """Get the enum name from an enum_specifier node."""
        for child in node.children:
            if child.type == "type_identifier" and child.text:
                return child.text.decode("utf-8")
        return None

    def _get_class_name(self, node: Node) -> Optional[str]:
        """Get the class name from a class_specifier node."""
        for child in node.children:
            if child.type == "type_identifier" and child.text:
                return child.text.decode("utf-8")
        return None

    def _get_base_classes(self, node: Node) -> list[str]:
        """Get base classes from a class_specifier node."""
        base_classes: list[str] = []
        base_clause = self._get_child_by_type(node, "base_class_clause")
        if base_clause:
            for child in base_clause.children:
                if child.type == "type_identifier" and child.text:
                    base_classes.append(child.text.decode("utf-8"))
        return base_classes

    def _get_child_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find the first child node of a given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _get_function_signature(self, node: Node) -> str:
        """Build function signature string."""
        # Try to get a clean signature from the node text
        if node.text:
            text = node.text.decode("utf-8")
            # Find the function header (up to the opening brace)
            brace_pos = text.find("{")
            if brace_pos > 0:
                header = text[:brace_pos].strip()
                # Clean up multi-line headers
                header = " ".join(header.split())
                return header

        return "function"

    def _get_class_signature(self, name: str, base_classes: list[str]) -> str:
        """Build class signature string."""
        signature = f"class {name}"
        if base_classes:
            signature += f" : {', '.join(base_classes)}"
        return signature

    def _get_c_comment(self, node: Node, content: bytes) -> Optional[str]:
        """Extract C-style comment before a node."""
        comments: list[str] = []

        sibling = node.prev_sibling
        while sibling:
            if sibling.type == "comment":
                comment = sibling.text.decode("utf-8") if sibling.text else ""
                # Handle // comments
                if comment.startswith("//"):
                    comment = comment[2:].strip()
                    # Handle /// doxygen comments
                    if comment.startswith("/"):
                        comment = comment[1:].strip()
                    comments.insert(0, comment)
                # Handle /* */ comments
                elif comment.startswith("/*"):
                    content_text = comment[2:-2].strip()
                    # Handle /** doxygen comments
                    if content_text.startswith("*"):
                        content_text = content_text[1:].strip()
                    lines = [
                        line.strip().lstrip("*").strip()
                        for line in content_text.split("\n")
                    ]
                    comments.insert(0, " ".join(lines))
                sibling = sibling.prev_sibling
            else:
                break

        return " ".join(comments).strip() if comments else None

    def _extract_calls(self, node: Node, content: bytes) -> list[str]:
        """Extract function calls from a node."""
        calls: set[str] = set()

        def walk(n: Node) -> None:
            if n.type == "call_expression":
                # Get the function name
                func = self._get_child_by_type(n, "identifier")
                if func and func.text:
                    calls.add(func.text.decode("utf-8"))
                else:
                    # Handle method call or qualified call
                    field_expr = self._get_child_by_type(n, "field_expression")
                    if field_expr:
                        field = self._get_child_by_type(field_expr, "field_identifier")
                        if field and field.text:
                            calls.add(field.text.decode("utf-8"))

            for child in n.children:
                walk(child)

        # Walk the function body
        body = self._get_child_by_type(node, "compound_statement")
        if body:
            walk(body)

        return list(calls)
