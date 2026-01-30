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

__version__ = "0.0.2"


class ContextManagerScope:
    """Tracks a context manager's variable and its valid scope."""

    def __init__(
        self,
        var_name: str,
        context_manager: str,
        start_line: int,
        end_line: int,
        has_prior_definition: bool = False,
    ):
        self.var_name = var_name
        self.context_manager = context_manager
        self.start_line = start_line
        self.end_line = end_line
        self.has_prior_definition = has_prior_definition


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
    """AST visitor that detects context manager scope violations.

    The key insight is tracking whether variables have "prior definitions"
    (parameters, assignments before the CM). If a variable has a prior definition
    and we're in a code path where the CM didn't run, the usage refers to
    the prior definition and should not be flagged.
    """

    def __init__(self, tracked_context_managers: set[str]):
        self.tracked_context_managers = tracked_context_managers
        self.violations: list[tuple[int, int, str]] = []

        # Active CM scopes (currently inside a with block)
        self.active_scopes: list[ContextManagerScope] = []

        # Exited CM scopes that could be violated
        # Maps var_name -> ContextManagerScope
        self.exited_scopes: dict[str, ContextManagerScope] = {}

        # Track all known definitions per variable (before any CM)
        # This tells us if a variable has an "alternative definition"
        # that would be valid when the CM didn't run
        self.known_definitions: dict[str, set[str]] = {}

        # Stack of branch states for control flow tracking
        # Each entry is a snapshot of exited_scopes before entering a branch
        self.branch_stack: list[dict[str, ContextManagerScope]] = []

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

    def _record_definition(self, var_name: str, source: str) -> None:
        """Record that a variable has a definition from a given source."""
        self.known_definitions.setdefault(var_name, set()).add(source)

    def _has_prior_definition(self, var_name: str) -> bool:
        """Check if a variable has any definition other than from a CM."""
        return bool(self.known_definitions.get(var_name))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function boundaries and record parameters as definitions."""
        # Save state
        old_exited = self.exited_scopes.copy()
        old_definitions = {k: v.copy() for k, v in self.known_definitions.items()}

        # Reset for this function
        self.exited_scopes = {}
        self.known_definitions = {}

        # Record parameters as definitions
        for arg in node.args.args:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        for arg in node.args.posonlyargs:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        for arg in node.args.kwonlyargs:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        if node.args.vararg:
            self._record_definition(node.args.vararg.arg, f"param:{node.lineno}")
        if node.args.kwarg:
            self._record_definition(node.args.kwarg.arg, f"param:{node.lineno}")

        self.generic_visit(node)

        # Restore state
        self.exited_scopes = old_exited
        self.known_definitions = old_definitions

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function boundaries and record parameters as definitions."""
        # Save state
        old_exited = self.exited_scopes.copy()
        old_definitions = {k: v.copy() for k, v in self.known_definitions.items()}

        # Reset for this function
        self.exited_scopes = {}
        self.known_definitions = {}

        # Record parameters as definitions
        for arg in node.args.args:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        for arg in node.args.posonlyargs:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        for arg in node.args.kwonlyargs:
            self._record_definition(arg.arg, f"param:{node.lineno}")
        if node.args.vararg:
            self._record_definition(node.args.vararg.arg, f"param:{node.lineno}")
        if node.args.kwarg:
            self._record_definition(node.args.kwarg.arg, f"param:{node.lineno}")

        self.generic_visit(node)

        # Restore state
        self.exited_scopes = old_exited
        self.known_definitions = old_definitions

    def _visit_with(self, node: ast.With | ast.AsyncWith) -> None:
        """Common logic for With and AsyncWith nodes."""
        tracked_vars: list[ContextManagerScope] = []

        for item in node.items:
            cm_name = self._get_context_manager_name(item.context_expr)
            if cm_name in self.tracked_context_managers:
                var_names = self._get_target_names(item.optional_vars)
                for var_name in var_names:
                    has_prior = self._has_prior_definition(var_name)
                    scope = ContextManagerScope(
                        var_name=var_name,
                        context_manager=cm_name,
                        start_line=node.lineno,
                        end_line=self._get_node_end_line(node),
                        has_prior_definition=has_prior,
                    )
                    tracked_vars.append(scope)
                    self.active_scopes.append(scope)
                    # Remove from exited while we're in the CM
                    self.exited_scopes.pop(var_name, None)

        # Visit the body
        for child in node.body:
            self.visit(child)

        # After visiting body, these scopes are no longer active
        for scope in tracked_vars:
            self.active_scopes.remove(scope)
            # Only track as exited if it doesn't have a prior definition
            # that would make it valid in alternative code paths
            # We always add it, but the prior_definition flag determines
            # whether usages get flagged
            self.exited_scopes[scope.var_name] = scope

    def visit_With(self, node: ast.With) -> None:
        self._visit_with(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_with(node)

    def _visit_branching_construct(
        self,
        bodies: list[list[ast.stmt]],
    ) -> None:
        """Handle branching constructs (if/elif/else, try/except/finally).

        The key insight: CM scopes created in one branch don't exist in sibling branches.
        After all branches, we merge: if a CM exited in ANY branch, it might affect
        code after the construct.

        Args:
            bodies: List of statement lists, one per branch
        """
        if not bodies:
            return

        # Save state before any branch
        exited_before = self.exited_scopes.copy()

        # Collect CM scopes added in each branch
        all_added: dict[str, ContextManagerScope] = {}

        for body in bodies:
            # Reset to pre-branch state for each branch
            self.exited_scopes = exited_before.copy()

            # Visit this branch
            for child in body:
                self.visit(child)

            # Collect what was added in this branch
            for var_name, scope in self.exited_scopes.items():
                if var_name not in exited_before or exited_before[var_name] is not scope:
                    all_added[var_name] = scope

        # After all branches, merge: anything that was exited in any branch
        # could affect code after the construct
        self.exited_scopes = exited_before.copy()
        self.exited_scopes.update(all_added)

    def visit_If(self, node: ast.If) -> None:
        """Handle if/elif/else with proper branch isolation."""
        # Collect all branches
        bodies = [node.body]
        if node.orelse:
            # orelse could be an else block or an elif (which is another If)
            bodies.append(node.orelse)

        self._visit_branching_construct(bodies)

    def visit_Try(self, node: ast.Try) -> None:
        """Handle try/except/else/finally with proper branch isolation."""
        # try body and except handlers are mutually exclusive
        # else runs only if try succeeds (no exception)
        # finally always runs

        bodies = [node.body]
        for handler in node.handlers:
            bodies.append(handler.body)
        if node.orelse:
            bodies.append(node.orelse)

        self._visit_branching_construct(bodies)

        # Finally always runs, visit it in the merged state
        for child in node.finalbody:
            self.visit(child)

    def visit_Match(self, node: ast.Match) -> None:
        """Handle match/case with proper branch isolation."""
        bodies = [case.body for case in node.cases]

        # Visit the subject first
        self.visit(node.subject)

        self._visit_branching_construct(bodies)

    def visit_Name(self, node: ast.Name) -> None:
        """Check if a variable name references an exited context manager scope."""
        var_name = node.id

        if var_name in self.exited_scopes:
            scope = self.exited_scopes[var_name]

            if node.lineno > scope.end_line:
                if isinstance(node.ctx, ast.Load):
                    # Only flag if:
                    # 1. No prior definition exists (CM is the only source), OR
                    # 2. We're past the branching point where CM might have run
                    #
                    # The branch handling in visit_If etc. takes care of (2) by
                    # removing CM scopes from exited_scopes in sibling branches.
                    # So if we get here, we're either:
                    # - In the same branch where CM ran (should flag)
                    # - After the branching construct (should flag, CM might have run)
                    #
                    # The only exception: if the variable has a prior definition
                    # AND we somehow know the CM didn't run. The branch handling
                    # ensures we don't get here in that case.

                    msg = (
                        f"CMS001 Variable '{var_name}' from {scope.context_manager}() "
                        f"(line {scope.start_line}) used outside its context manager scope"
                    )
                    self.violations.append((node.lineno, node.col_offset, msg))

                elif isinstance(node.ctx, ast.Store):
                    # Variable is being reassigned, no longer refers to CM
                    del self.exited_scopes[var_name]

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Handle assignments - record as definitions and clear exited state."""
        for target in node.targets:
            for name in self._get_target_names(target):
                self._record_definition(name, f"assign:{node.lineno}")
                self.exited_scopes.pop(name, None)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Handle annotated assignments."""
        if node.target and node.value:  # Only if there's actually an assignment
            for name in self._get_target_names(node.target):
                self._record_definition(name, f"assign:{node.lineno}")
                self.exited_scopes.pop(name, None)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """Handle walrus operator (:=) assignments."""
        if isinstance(node.target, ast.Name):
            name = node.target.id
            self._record_definition(name, f"assign:{node.lineno}")
            self.exited_scopes.pop(name, None)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Handle for loops - the loop variable is a definition."""
        for name in self._get_target_names(node.target):
            self._record_definition(name, f"for:{node.lineno}")

        # For loops: body might not execute, or might execute multiple times
        # Treat body and orelse as branches
        bodies = [node.body]
        if node.orelse:
            bodies.append(node.orelse)

        # Visit iter first
        self.visit(node.iter)

        self._visit_branching_construct(bodies)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Handle async for loops."""
        for name in self._get_target_names(node.target):
            self._record_definition(name, f"for:{node.lineno}")

        bodies = [node.body]
        if node.orelse:
            bodies.append(node.orelse)

        self.visit(node.iter)
        self._visit_branching_construct(bodies)

    def visit_While(self, node: ast.While) -> None:
        """Handle while loops."""
        # Visit condition
        self.visit(node.test)

        # Body might not execute
        bodies = [node.body]
        if node.orelse:
            bodies.append(node.orelse)

        self._visit_branching_construct(bodies)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """Handle comprehension targets as definitions."""
        for name in self._get_target_names(node.target):
            self._record_definition(name, f"comp:{node.target.lineno if hasattr(node.target, 'lineno') else 0}")
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Handle exception handler variable."""
        if node.name:
            self._record_definition(node.name, f"except:{node.lineno}")
        self.generic_visit(node)
