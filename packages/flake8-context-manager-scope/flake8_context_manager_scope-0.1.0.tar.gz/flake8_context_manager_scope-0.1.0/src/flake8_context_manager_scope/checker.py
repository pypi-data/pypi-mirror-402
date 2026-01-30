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
from dataclasses import dataclass
from typing import Any, ClassVar, Generator

__version__ = "0.1.0"


@dataclass
class CMDefinition:
    """A context manager variable definition."""

    var_name: str
    cm_name: str
    node: ast.With | ast.AsyncWith
    path: list[tuple[str, int | None]]
    func_node: ast.FunctionDef | ast.AsyncFunctionDef | None
    terminating_if_path: list[tuple[str, int | None]] | None = None  # Path to containing If that terminates


@dataclass
class VarUse:
    """A variable use (Load context)."""

    var_name: str
    node: ast.Name
    path: list[tuple[str, int | None]]
    func_node: ast.FunctionDef | ast.AsyncFunctionDef | None


class ContextManagerScopeChecker:
    """
    Flake8 plugin that detects variables from context managers used outside their scope.

    Uses path-based analysis to correctly handle mutually exclusive branches
    (if/else, try/except, match/case).
    """

    name = "flake8-context-manager-scope"
    version = __version__

    # Class-level option for tracked context managers
    tracked_context_managers: ClassVar[set[str]] = set()

    def __init__(self, tree: ast.AST):
        self.tree = tree

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
        analyzer = PathBasedAnalyzer(self.tree, self.tracked_context_managers)
        violations = analyzer.analyze()

        for line, col, msg in violations:
            yield (line, col, msg, type(self))


class PathBasedAnalyzer:
    """
    Analyzes context manager scope violations using AST path comparison.

    Key insight: if/else, try/except, and match/case branches are mutually exclusive.
    A CM defined in one branch cannot affect uses in a sibling branch.
    """

    def __init__(self, tree: ast.AST, tracked_cms: set[str]):
        self.tree = tree
        self.tracked_cms = tracked_cms
        self.cm_definitions: list[CMDefinition] = []
        self.var_bindings: list[VarBinding] = []
        self.var_uses: list[VarUse] = []

    def analyze(self) -> list[tuple[int, int, str]]:
        """Run the analysis and return violations."""
        # Pass 1: Collect all CM definitions and variable uses
        self._collect_definitions_and_uses()

        # Pass 2: Check each use against definitions
        violations = []
        for use in self.var_uses:
            violation = self._check_use(use)
            if violation:
                violations.append(violation)

        return violations

    def _collect_definitions_and_uses(self) -> None:
        """Walk the AST and collect CM definitions and variable uses."""
        collector = _NodeCollector(self.tree, self.tracked_cms)
        collector.collect()
        self.cm_definitions = collector.cm_definitions
        self.var_bindings = collector.var_bindings
        self.var_uses = collector.var_uses

    def _check_use(self, use: VarUse) -> tuple[int, int, str] | None:
        """Check if a variable use is a violation."""
        # Find all CM definitions for this variable in the same function
        relevant_cms = [
            cm_def
            for cm_def in self.cm_definitions
            if cm_def.var_name == use.var_name and cm_def.func_node is use.func_node
        ]

        if not relevant_cms:
            return None

        # Find all bindings (including non-tracked CMs) for this variable
        relevant_bindings = [
            binding
            for binding in self.var_bindings
            if binding.var_name == use.var_name and binding.func_node is use.func_node
        ]

        # First pass: if the use is inside ANY binding's scope, it's OK
        # This handles both tracked and non-tracked CMs
        for binding in relevant_bindings:
            if self._is_inside_binding_scope(use.node, binding.node):
                return None  # Use is inside a binding, no violation

        # Second pass: check if any tracked CM could cause a violation
        for cm_def in relevant_cms:
            # Is the use in a mutually exclusive branch? (OK for this CM)
            if not self._paths_are_compatible(cm_def, use.path):
                continue  # Mutually exclusive, this CM doesn't affect this use

            # Use is outside CM scope and paths are compatible = VIOLATION
            msg = (
                f"CMS001 Variable '{use.var_name}' from {cm_def.cm_name}() "
                f"(line {cm_def.node.lineno}) used outside its context manager scope"
            )
            return (use.node.lineno, use.node.col_offset, msg)

        return None

    def _is_inside_cm_scope(self, use_node: ast.Name, cm_node: ast.With | ast.AsyncWith) -> bool:
        """Check if a use is inside the CM's with block."""
        cm_end = cm_node.end_lineno if cm_node.end_lineno else cm_node.lineno
        return use_node.lineno <= cm_end

    def _is_inside_binding_scope(self, use_node: ast.Name, binding_node: ast.AST) -> bool:
        """Check if a use is inside a binding's scope (works for with statements)."""
        if isinstance(binding_node, (ast.With, ast.AsyncWith)):
            end_line = binding_node.end_lineno if binding_node.end_lineno else binding_node.lineno
            return use_node.lineno <= end_line
        return False

    def _paths_are_compatible(
        self, cm_def: CMDefinition, use_path: list[tuple[str, int | None]]
    ) -> bool:
        """
        Check if a definition can reach a use based on AST paths.

        Returns False if they're in mutually exclusive branches (if/else, try/except, etc.)
        """
        def_path = cm_def.path

        # Check for terminating if pattern: if the CM is inside an if body that always
        # terminates (return/raise), and the use is AFTER the if (not in body/orelse),
        # then they're mutually exclusive
        if cm_def.terminating_if_path:
            if_path = cm_def.terminating_if_path
            if_path_len = len(if_path)

            # The use is "after" the if if:
            # 1. The use path shares the same prefix up to but not including the if
            # 2. The use path has a LATER index in the same parent list
            if len(use_path) > if_path_len:
                # Check if use_path matches if_path up to the if's parent
                if use_path[: if_path_len - 1] == if_path[: if_path_len - 1]:
                    # Check if they're in the same parent list but different indices
                    if_idx = if_path[if_path_len - 1]
                    use_branch = use_path[if_path_len - 1]
                    if if_idx[0] == use_branch[0]:  # Same field name (e.g., both "body")
                        if if_idx[1] is not None and use_branch[1] is not None:
                            if use_branch[1] > if_idx[1]:
                                # Use is after the if in the same list - mutually exclusive
                                return False

        # Find common prefix length
        common_len = 0
        for i, (d, u) in enumerate(zip(def_path, use_path)):
            if d == u:
                common_len = i + 1
            else:
                break

        # If paths diverge, check if they diverge at a branch point
        if common_len < len(def_path) and common_len < len(use_path):
            def_branch = def_path[common_len]
            use_branch = use_path[common_len]

            # if/else: body vs orelse are mutually exclusive
            if def_branch[0] == "body" and use_branch[0] == "orelse":
                return False
            if def_branch[0] == "orelse" and use_branch[0] == "body":
                return False

            # try/except: body vs handlers are mutually exclusive
            if def_branch[0] == "body" and use_branch[0] == "handlers":
                return False
            if def_branch[0] == "handlers" and use_branch[0] == "body":
                return False

            # Different except handlers are mutually exclusive
            if def_branch[0] == "handlers" and use_branch[0] == "handlers":
                if def_branch[1] != use_branch[1]:
                    return False

            # match/case: different cases are mutually exclusive
            if def_branch[0] == "cases" and use_branch[0] == "cases":
                if def_branch[1] != use_branch[1]:
                    return False

        return True


@dataclass
class VarBinding:
    """A variable binding (assignment or CM)."""

    var_name: str
    node: ast.AST
    path: list[tuple[str, int | None]]
    func_node: ast.FunctionDef | ast.AsyncFunctionDef | None
    is_tracked_cm: bool  # True if from a tracked CM, False if from other binding


class _NodeCollector(ast.NodeVisitor):
    """Collects CM definitions and variable uses from the AST."""

    def __init__(self, tree: ast.AST, tracked_cms: set[str]):
        self.tree = tree
        self.tracked_cms = tracked_cms
        self.cm_definitions: list[CMDefinition] = []
        self.var_bindings: list[VarBinding] = []  # ALL bindings (for shadowing)
        self.var_uses: list[VarUse] = []
        self._current_path: list[tuple[str, int | None]] = []
        self._current_func: ast.FunctionDef | ast.AsyncFunctionDef | None = None
        self._cm_var_names: set[str] = set()  # Track which vars came from tracked CMs in current func
        self._terminating_if_path: list[tuple[str, int | None]] | None = None  # Path to innermost terminating If

    def collect(self) -> None:
        """Start collection from the tree root."""
        self._visit_children(self.tree, "body")

    def _visit_children(self, node: ast.AST, field_name: str) -> None:
        """Visit children of a node, tracking the path."""
        field = getattr(node, field_name, None)
        if field is None:
            return

        if isinstance(field, list):
            for i, child in enumerate(field):
                if isinstance(child, ast.AST):
                    self._current_path.append((field_name, i))
                    self.visit(child)
                    self._current_path.pop()
        elif isinstance(field, ast.AST):
            self._current_path.append((field_name, None))
            self.visit(field)
            self._current_path.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function scope."""
        old_func = self._current_func
        old_cm_vars = self._cm_var_names.copy()
        self._current_func = node
        self._cm_var_names = set()
        self.generic_visit(node)
        self._current_func = old_func
        self._cm_var_names = old_cm_vars

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function scope."""
        old_func = self._current_func
        old_cm_vars = self._cm_var_names.copy()
        self._current_func = node
        self._cm_var_names = set()
        self.generic_visit(node)
        self._current_func = old_func
        self._cm_var_names = old_cm_vars

    def visit_If(self, node: ast.If) -> None:
        """Track If nodes to detect terminating if bodies."""
        # Visit the test expression
        self._visit_children(node, "test")

        # Check if the if body always terminates
        if_body_terminates = self._body_always_terminates(node.body)

        # Visit the if body, tracking if it's terminating
        old_terminating_if = self._terminating_if_path
        if if_body_terminates and not node.orelse:
            # This if body terminates and has no else - code after is implicit else
            self._terminating_if_path = self._current_path.copy()

        self._visit_children(node, "body")
        self._terminating_if_path = old_terminating_if

        # Visit the else body (not in a terminating context from this if)
        self._visit_children(node, "orelse")

    def _body_always_terminates(self, body: list[ast.stmt]) -> bool:
        """Check if a body always terminates (return/raise)."""
        for stmt in body:
            if isinstance(stmt, (ast.Return, ast.Raise)):
                return True
            if isinstance(stmt, ast.If):
                # If both branches terminate, the if terminates
                if_terminates = self._body_always_terminates(stmt.body)
                else_terminates = self._body_always_terminates(stmt.orelse) if stmt.orelse else False
                if if_terminates and else_terminates:
                    return True
            if isinstance(stmt, (ast.With, ast.AsyncWith)):
                if self._body_always_terminates(stmt.body):
                    return True
            if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
                # Loops might not execute, so they don't guarantee termination
                pass
            if isinstance(stmt, ast.Try):
                # Try terminates if body terminates AND all handlers terminate
                # (simplified - doesn't handle finally)
                pass
        return False

    def visit_With(self, node: ast.With) -> None:
        """Collect CM definitions from with statements."""
        self._handle_with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Collect CM definitions from async with statements."""
        self._handle_with(node)

    def _handle_with(self, node: ast.With | ast.AsyncWith) -> None:
        """Common handler for With and AsyncWith."""
        for item in node.items:
            cm_name = self._get_cm_name(item.context_expr)
            var_names = self._get_target_names(item.optional_vars)

            for var_name in var_names:
                is_tracked = cm_name in self.tracked_cms

                # Record ALL CM bindings for shadowing analysis
                self.var_bindings.append(
                    VarBinding(
                        var_name=var_name,
                        node=node,
                        path=self._current_path.copy(),
                        func_node=self._current_func,
                        is_tracked_cm=is_tracked,
                    )
                )

                if is_tracked:
                    self.cm_definitions.append(
                        CMDefinition(
                            var_name=var_name,
                            cm_name=cm_name,
                            node=node,
                            path=self._current_path.copy(),
                            func_node=self._current_func,
                            terminating_if_path=self._terminating_if_path,
                        )
                    )
                    self._cm_var_names.add(var_name)

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Collect variable uses."""
        if isinstance(node.ctx, ast.Load) and node.id in self._cm_var_names:
            self.var_uses.append(
                VarUse(
                    var_name=node.id,
                    node=node,
                    path=self._current_path.copy(),
                    func_node=self._current_func,
                )
            )
        self.generic_visit(node)

    def _get_cm_name(self, node: ast.expr) -> str | None:
        """Extract the context manager function name."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        return None

    def _get_target_names(self, target: ast.expr | None) -> list[str]:
        """Extract variable names from a with target."""
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

    def generic_visit(self, node: ast.AST) -> None:
        """Visit all children, tracking paths."""
        for field_name, _ in ast.iter_fields(node):
            self._visit_children(node, field_name)
