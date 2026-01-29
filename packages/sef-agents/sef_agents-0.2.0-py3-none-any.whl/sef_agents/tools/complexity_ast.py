"""AST-based Complexity Analyzer for TypeScript/JavaScript.

Production-grade implementation using tree-sitter for accurate
per-function cognitive complexity calculation.

Implements SonarQube-style cognitive complexity with nesting weights.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

try:
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = None  # type: ignore
    Parser = None  # type: ignore
    logger.warning(
        "tree_sitter_not_available",
        msg="Install: uv add tree-sitter tree-sitter-typescript",
    )


@dataclass
class FunctionComplexity:
    """Per-function complexity metrics.

    Attributes:
        name: Function/method name.
        complexity: Cognitive complexity score.
        line: Starting line number.
        is_method: True if method (inside class).
    """

    name: str
    complexity: int
    line: int
    is_method: bool = False


@dataclass
class ASTComplexityResult:
    """AST-based complexity analysis result.

    Attributes:
        functions: List of per-function complexity.
        file_complexity: Aggregate file complexity.
        classes: Number of classes.
        error: Error message if parsing failed.
    """

    functions: list[FunctionComplexity]
    file_complexity: int
    classes: int
    error: str | None = None


class TypeScriptASTAnalyzer:
    """AST-based TypeScript complexity analyzer with cognitive complexity.

    Uses tree-sitter-typescript for accurate parsing.
    Implements SonarQube cognitive complexity algorithm.
    """

    def __init__(self):
        """Initialize analyzer."""
        self.parser: Parser | None = None
        self.ts_language: Language | None = None

        if TREE_SITTER_AVAILABLE:
            self._init_parser()

    def _init_parser(self) -> None:
        """Initialize tree-sitter parser for TypeScript."""
        try:
            from tree_sitter_typescript import language_typescript, language_tsx  # type: ignore

            # Wrap PyCapsule in Language object
            if Language:
                self.ts_language = Language(language_typescript())
                self.tsx_language = Language(language_tsx())
            else:
                self.ts_language = None
                self.tsx_language = None

            if Parser:
                self.parser = Parser()
            else:
                self.parser = None
        except ImportError as e:
            logger.warning("tree_sitter_init_failed", error=str(e))
            self.parser = None
            self.ts_language = None
            self.tsx_language = None

    def _calculate_cognitive_complexity(self, node: Any, nesting_level: int = 0) -> int:
        """Calculate cognitive complexity for a node (recursive).

        Cognitive complexity weights:
        - Base: +1 per function/method
        - If/else: +1 (not nested), +2 per nesting level
        - Switch: +1 per case (not nested), +2 per nesting level
        - Loops: +1 (not nested), +2 per nesting level
        - Try/catch: +1
        - Ternary: +1
        - Logical operators: +1 per chain

        Args:
            node: tree-sitter node.
            nesting_level: Current nesting depth.

        Returns:
            Cognitive complexity score.
        """
        if not node or not hasattr(node, "type"):
            return 0

        complexity = 0
        node_type = node.type

        # Base complexity for control flow
        if node_type in ("if_statement", "else_clause"):
            complexity += 1 + nesting_level
        elif node_type == "switch_statement":
            complexity += 1 + nesting_level
        elif node_type in (
            "for_statement",
            "while_statement",
            "for_in_statement",
            "for_of_statement",
        ):
            complexity += 1 + nesting_level
        elif node_type == "try_statement":
            complexity += 1
        elif node_type == "catch_clause":
            complexity += 1
        elif node_type == "ternary_expression":
            complexity += 1
        elif node_type in ("logical_expression", "binary_expression"):
            # Count logical operators (&&, ||)
            if hasattr(node, "text"):
                text = (
                    node.text.decode("utf-8")
                    if isinstance(node.text, bytes)
                    else str(node.text)
                )
                if "&&" in text or "||" in text:
                    complexity += 1

        # Recurse into children with increased nesting for control flow
        if node_type in (
            "if_statement",
            "for_statement",
            "while_statement",
            "switch_statement",
            "try_statement",
        ):
            next_nesting = nesting_level + 1
        else:
            next_nesting = nesting_level

        if hasattr(node, "children"):
            for child in node.children:
                complexity += self._calculate_cognitive_complexity(child, next_nesting)

        return complexity

    def _extract_functions(
        self, node: Any, functions: list[FunctionComplexity], nesting: int = 0
    ) -> None:
        """Extract function/method definitions from AST.

        Args:
            node: tree-sitter node.
            functions: List to append function complexities.
            nesting: Current nesting level.
        """
        if not node or not hasattr(node, "type"):
            return

        node_type = node.type

        # Function/method declarations
        if node_type in (
            "function_declaration",
            "method_definition",
            "arrow_function",
            "function_expression",
        ):
            func_name = "anonymous"
            func_line = 0
            is_method = node_type == "method_definition"

            # Extract function name
            if hasattr(node, "children"):
                for child in node.children:
                    if child.type == "identifier" and hasattr(child, "text"):
                        func_name = (
                            child.text.decode("utf-8")
                            if isinstance(child.text, bytes)
                            else str(child.text)
                        )
                    elif hasattr(child, "start_point"):
                        func_line = child.start_point[0] + 1

            # Calculate complexity for this function
            func_complexity = 1  # Base complexity
            if hasattr(node, "children"):
                for child in node.children:
                    if child.type == "statement_block" or child.type == "body":
                        func_complexity += self._calculate_cognitive_complexity(
                            child, 0
                        )

            functions.append(
                FunctionComplexity(
                    name=func_name,
                    complexity=func_complexity,
                    line=func_line,
                    is_method=is_method,
                )
            )

        # Recurse into children
        if hasattr(node, "children"):
            for child in node.children:
                self._extract_functions(child, functions, nesting)

    def analyze(self, content: str, is_tsx: bool = False) -> ASTComplexityResult:
        """Analyze TypeScript/TSX file for complexity.

        Args:
            content: File content.
            is_tsx: True if TSX file.

        Returns:
            ASTComplexityResult with per-function and file complexity.
        """
        if not TREE_SITTER_AVAILABLE or not self.parser:
            return ASTComplexityResult(
                functions=[],
                file_complexity=0,
                classes=0,
                error="tree-sitter not available. Install: uv add tree-sitter tree-sitter-typescript",
            )

        try:
            # Select language (tree-sitter uses .language property, not set_language())
            if is_tsx and hasattr(self, "tsx_language") and self.tsx_language:
                self.parser.language = self.tsx_language
            elif self.ts_language:
                self.parser.language = self.ts_language
            else:
                return ASTComplexityResult(
                    functions=[],
                    file_complexity=0,
                    classes=0,
                    error="TypeScript language not loaded",
                )

            # Parse
            tree = self.parser.parse(content.encode("utf-8"))
            root_node = tree.root_node

            # Extract functions
            functions: list[FunctionComplexity] = []
            self._extract_functions(root_node, functions)

            # Count classes
            classes = 0
            if hasattr(root_node, "children"):
                for child in root_node.children:
                    if child.type == "class_declaration":
                        classes += 1

            # Calculate file-level aggregate
            file_complexity = sum(f.complexity for f in functions)

            return ASTComplexityResult(
                functions=functions,
                file_complexity=file_complexity,
                classes=classes,
                error=None,
            )

        except (AttributeError, ValueError, TypeError) as e:
            logger.warning("ast_parse_failed", error=str(e))
            return ASTComplexityResult(
                functions=[],
                file_complexity=0,
                classes=0,
                error=f"Parse error: {e}",
            )


def analyze_typescript_ast(
    file_path: Path, content: str | None = None
) -> ASTComplexityResult:
    """Analyze TypeScript file using AST.

    Args:
        file_path: Path to TypeScript file.
        content: Optional file content (reads from path if not provided).

    Returns:
        ASTComplexityResult.
    """
    if content is None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            return ASTComplexityResult(
                functions=[],
                file_complexity=0,
                classes=0,
                error=f"Read error: {e}",
            )

    is_tsx = file_path.suffix in (".tsx", ".jsx")
    analyzer = TypeScriptASTAnalyzer()
    return analyzer.analyze(content, is_tsx=is_tsx)
