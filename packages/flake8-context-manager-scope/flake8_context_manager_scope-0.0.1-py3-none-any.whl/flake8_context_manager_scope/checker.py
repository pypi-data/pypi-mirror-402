"""
Flake8 plugin to detect context manager variables used outside their scope.

This catches bugs like:
    async with get_async_session() as session:
        result = await session.execute(query)

    # BUG: session used after context manager closed
    await session.execute(another_query)

Error codes:
    CMS001: Variable from context manager used outside its scope
"""

import ast
from typing import Any, ClassVar, Generator

__version__ = "0.0.1"


class ContextManagerScope:
    """Tracks a context manager's variable and its valid scope."""

    def __init__(
        self,
        var_name: str,
        context_manager: str,
        start_line: int,
        end_line: int,
    ):
        self.var_name = var_name
        self.context_manager = context_manager
        self.start_line = start_line
        self.end_line = end_line


class ContextManagerScopeChecker:
    """
    Flake8 plugin that detects variables from context managers used outside their scope.
    """

    name = "flake8-context-manager-scope"
    version = __version__

    # Class-level option for tracked context managers
    tracked_context_managers: ClassVar[set[str]] = set()

    def __init__(self, tree: ast.AST):
        self.tree = tree
        self.violations: list[tuple[int, int, str]] = []
        self.active_scopes: list[ContextManagerScope] = []
        self.exited_scopes: dict[str, ContextManagerScope] = {}

    @classmethod
    def add_options(cls, parser: Any) -> None:
        """Add plugin options to flake8."""
        parser.add_option(
            "--context-manager-scope-functions",
            default="",
            parse_from_config=True,
            comma_separated_list=True,
            help="Comma-separated list of context manager functions to track",
        )

    @classmethod
    def parse_options(cls, options: Any) -> None:
        """Parse plugin options."""
        if hasattr(options, "context_manager_scope_functions"):
            cls.tracked_context_managers = set(options.context_manager_scope_functions)

    def run(self) -> Generator[tuple[int, int, str, type], None, None]:
        """Run the checker and yield violations."""
        visitor = ContextManagerScopeVisitor(self.tracked_context_managers)
        visitor.visit(self.tree)

        for line, col, msg in visitor.violations:
            yield (line, col, msg, type(self))


class ContextManagerScopeVisitor(ast.NodeVisitor):
    """AST visitor that detects context manager scope violations."""

    def __init__(self, tracked_context_managers: set[str]):
        self.tracked_context_managers = tracked_context_managers
        self.violations: list[tuple[int, int, str]] = []
        self.active_scopes: list[ContextManagerScope] = []
        self.exited_scopes: dict[str, ContextManagerScope] = {}

    def _get_context_manager_name(self, node: ast.expr) -> str | None:
        """Extract the context manager function name from a with item."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        return None

    def _get_target_names(self, target: ast.expr | None) -> list[str]:
        """Extract variable names from a with target (handles tuple unpacking)."""
        if target is None:
            return []
        if isinstance(target, ast.Name):
            return [target.id]
        elif isinstance(target, ast.Tuple):
            names = []
            for elt in target.elts:
                names.extend(self._get_target_names(elt))
            return names
        return []

    def _get_node_end_line(self, node: ast.AST) -> int:
        """Get the end line of a node."""
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            return node.end_lineno
        max_line = getattr(node, "lineno", 0)
        for child in ast.walk(node):
            child_line = getattr(child, "lineno", 0)
            if child_line > max_line:
                max_line = child_line
        return max_line

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function boundaries to reset scope tracking."""
        old_exited = self.exited_scopes.copy()
        self.exited_scopes = {}
        self.generic_visit(node)
        self.exited_scopes = old_exited

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function boundaries to reset scope tracking."""
        old_exited = self.exited_scopes.copy()
        self.exited_scopes = {}
        self.generic_visit(node)
        self.exited_scopes = old_exited

    def _visit_with(self, node: ast.With | ast.AsyncWith) -> None:
        """Common logic for With and AsyncWith nodes."""
        tracked_vars: list[ContextManagerScope] = []

        for item in node.items:
            cm_name = self._get_context_manager_name(item.context_expr)
            if cm_name in self.tracked_context_managers:
                var_names = self._get_target_names(item.optional_vars)
                for var_name in var_names:
                    scope = ContextManagerScope(
                        var_name=var_name,
                        context_manager=cm_name,
                        start_line=node.lineno,
                        end_line=self._get_node_end_line(node),
                    )
                    tracked_vars.append(scope)
                    self.active_scopes.append(scope)
                    self.exited_scopes.pop(var_name, None)

        # Visit the body
        for child in node.body:
            self.visit(child)

        # After visiting body, these scopes are no longer active
        for scope in tracked_vars:
            self.active_scopes.remove(scope)
            self.exited_scopes[scope.var_name] = scope

    def visit_With(self, node: ast.With) -> None:
        self._visit_with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_with(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Check if a variable name references an exited context manager scope."""
        var_name = node.id

        if var_name in self.exited_scopes:
            scope = self.exited_scopes[var_name]

            if node.lineno > scope.end_line:
                if isinstance(node.ctx, ast.Load):
                    msg = (
                        f"CMS001 Variable '{var_name}' from {scope.context_manager}() "
                        f"(line {scope.start_line}) used outside its context manager scope"
                    )
                    self.violations.append((node.lineno, node.col_offset, msg))
                elif isinstance(node.ctx, ast.Store):
                    del self.exited_scopes[var_name]

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Handle assignments that might shadow exited context variables."""
        for target in node.targets:
            for name in self._get_target_names(target):
                self.exited_scopes.pop(name, None)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Handle annotated assignments."""
        if node.target:
            for name in self._get_target_names(node.target):
                self.exited_scopes.pop(name, None)
        self.generic_visit(node)
