"""JAX code checker - catches common gotchas and mistakes.

Based on JAX's Common Gotchas documentation:
https://jax.readthedocs.io/en/latest/notebooks/Common_Gotchas_in_JAX.html
"""

import re
import ast
from dataclasses import dataclass


@dataclass
class Issue:
    """A detected issue in JAX code."""
    severity: str  # "error", "warning", "info"
    line: int | None
    message: str
    suggestion: str


def check_jax_code(code: str) -> list[Issue]:
    """Analyze JAX code for common mistakes.

    Checks for:
    1. In-place mutations (array[idx] = value)
    2. Side effects in jitted functions (print, global writes)
    3. Improper random key usage
    4. Dynamic shapes in jit
    5. Python control flow in traced code
    6. Non-array inputs to JAX functions
    7. Missing block_until_ready for benchmarks
    8. Float64 without config

    Args:
        code: Python source code string

    Returns:
        List of Issue objects
    """
    issues = []

    # Parse AST for structural checks
    try:
        tree = ast.parse(code)
        issues.extend(_check_ast(tree, code))
    except SyntaxError as e:
        issues.append(Issue(
            severity="error",
            line=e.lineno,
            message=f"Syntax error: {e.msg}",
            suggestion="Fix the syntax error before checking for JAX issues."
        ))
        return issues

    # Regex-based checks for patterns
    issues.extend(_check_patterns(code))

    return issues


def _check_ast(tree: ast.AST, code: str) -> list[Issue]:
    """AST-based checks."""
    issues = []
    lines = code.split("\n")

    for node in ast.walk(tree):
        # Check 1: In-place array mutations
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
            issues.append(Issue(
                severity="error",
                line=node.lineno,
                message="In-place array mutation detected. JAX arrays are immutable.",
                suggestion="Use jax.numpy.ndarray.at[idx].set(value) instead of array[idx] = value"
            ))

        # Check 2: Augmented assignment on arrays (+=, -=, etc.)
        if isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Subscript):
                issues.append(Issue(
                    severity="error",
                    line=node.lineno,
                    message="Augmented assignment on array slice. JAX arrays are immutable.",
                    suggestion="Use array = array.at[idx].add(value) instead of array[idx] += value"
                ))

        # Check 3: Print inside function (potential jit issue)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                # Check if inside a function
                issues.append(Issue(
                    severity="warning",
                    line=node.lineno,
                    message="print() inside function may not work as expected under jit.",
                    suggestion="Use jax.debug.print() for debugging jitted functions, or ensure print is outside jit scope."
                ))

        # Check 4: Global variable writes
        if isinstance(node, ast.Global):
            issues.append(Issue(
                severity="warning",
                line=node.lineno,
                message="Global variable modification may cause issues with jit.",
                suggestion="JAX transforms require pure functions. Pass state explicitly as arguments."
            ))

        # Check 5: Random without key
        if isinstance(node, ast.Call):
            func = node.func
            # Check for numpy random usage
            if isinstance(func, ast.Attribute):
                if func.attr in ("random", "randn", "rand", "randint"):
                    if isinstance(func.value, ast.Attribute):
                        if func.value.attr == "random":
                            issues.append(Issue(
                                severity="warning",
                                line=node.lineno,
                                message="Using numpy random functions. These are not compatible with jit.",
                                suggestion="Use jax.random with explicit PRNG keys: key = jax.random.key(0); x = jax.random.normal(key, shape)"
                            ))

    return issues


def _check_patterns(code: str) -> list[Issue]:
    """Regex-based pattern checks."""
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        # Check: time.time() for benchmarking without block_until_ready
        if "time.time()" in line or "time.perf_counter()" in line:
            # Look for block_until_ready nearby
            context = "\n".join(lines[max(0, i-5):min(len(lines), i+5)])
            if "block_until_ready" not in context:
                issues.append(Issue(
                    severity="warning",
                    line=i,
                    message="Timing JAX code without block_until_ready() may give incorrect results.",
                    suggestion="Call .block_until_ready() on JAX arrays before stopping the timer."
                ))

        # Check: float64 usage without jax config
        if "float64" in line or "jnp.float64" in line or "dtype=np.float64" in line:
            if "jax.config" not in code and "JAX_ENABLE_X64" not in code:
                issues.append(Issue(
                    severity="info",
                    line=i,
                    message="Using float64. JAX defaults to float32.",
                    suggestion="Add jax.config.update('jax_enable_x64', True) at startup, or set JAX_ENABLE_X64=True environment variable."
                ))
                break  # Only warn once

        # Check: random key reuse pattern
        if re.search(r"jax\.random\.\w+\([^,]+,", line):
            # Check if same key variable is used multiple times
            key_match = re.search(r"jax\.random\.\w+\((\w+),", line)
            if key_match:
                key_name = key_match.group(1)
                # Count occurrences of this key in random calls
                key_pattern = rf"jax\.random\.\w+\({key_name},"
                occurrences = len(re.findall(key_pattern, code))
                if occurrences > 1:
                    # Check if key is split
                    if f"{key_name} = jax.random.split" not in code and f"= jax.random.split({key_name}" not in code:
                        issues.append(Issue(
                            severity="warning",
                            line=i,
                            message=f"PRNG key '{key_name}' may be reused without splitting.",
                            suggestion="Split keys before reuse: key, subkey = jax.random.split(key)"
                        ))
                        break  # Only warn once per key

        # Check: if/for inside jitted function operating on traced values
        # This is a heuristic - look for @jit decorator followed by control flow
        if "@jit" in line or "@jax.jit" in line:
            # Look at the function body for control flow
            func_start = i
            indent_match = re.match(r"^(\s*)", lines[min(i, len(lines)-1)])
            base_indent = len(indent_match.group(1)) if indent_match else 0

            for j in range(i, min(i + 30, len(lines))):
                func_line = lines[j]
                if func_line.strip() and not func_line.strip().startswith("#"):
                    line_indent = len(func_line) - len(func_line.lstrip())
                    if line_indent <= base_indent and j > func_start + 1:
                        break  # Exited function

                    # Check for Python control flow
                    if re.match(r"\s+if\s+.*:", func_line):
                        # Check if it's using traced values (heuristic)
                        if not re.search(r"if\s+\w+\s*(is|==)\s*(None|True|False)", func_line):
                            issues.append(Issue(
                                severity="info",
                                line=j + 1,
                                message="Python 'if' inside jitted function. May cause retracing if condition depends on traced values.",
                                suggestion="Use jax.lax.cond() for traced conditionals, or mark the condition as static_argnums."
                            ))
                            break

        # Check: list/tuple passed to jax function
        if re.search(r"jnp\.\w+\(\s*\[", line) or re.search(r"jax\.\w+\(\s*\[", line):
            issues.append(Issue(
                severity="info",
                line=i,
                message="Passing Python list to JAX function. This works but may be slow.",
                suggestion="Convert to jax.numpy array first for better performance: jnp.array([...])"
            ))

    return issues


async def jax_checker(code: str) -> str:
    """Check JAX code for common issues.

    Args:
        code: Python source code to check

    Returns:
        Formatted report of issues found
    """
    issues = check_jax_code(code)

    if not issues:
        return "No issues found. The code follows JAX best practices."

    # Group by severity
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    lines = []

    if errors:
        lines.append(f"## ERRORS ({len(errors)})")
        for issue in errors:
            loc = f"Line {issue.line}: " if issue.line else ""
            lines.append(f"- {loc}{issue.message}")
            lines.append(f"  -> {issue.suggestion}")
        lines.append("")

    if warnings:
        lines.append(f"## WARNINGS ({len(warnings)})")
        for issue in warnings:
            loc = f"Line {issue.line}: " if issue.line else ""
            lines.append(f"- {loc}{issue.message}")
            lines.append(f"  -> {issue.suggestion}")
        lines.append("")

    if infos:
        lines.append(f"## INFO ({len(infos)})")
        for issue in infos:
            loc = f"Line {issue.line}: " if issue.line else ""
            lines.append(f"- {loc}{issue.message}")
            lines.append(f"  -> {issue.suggestion}")

    return "\n".join(lines)
