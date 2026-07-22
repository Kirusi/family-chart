import ast
import inspect
import textwrap

import pytest


# @pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item, *args, **kwargs):
    # Only check standard function-based tests
    if not hasattr(item, "obj"):
        return

    # Get the raw source code of the test function
    source = inspect.getsource(item.obj)
    clean_source = textwrap.dedent(source)  # needs to be done for class and object methods

    # Parse code into an Abstract Syntax Tree (AST)
    tree = ast.parse(clean_source)

    # Walk through the tree to find any Assert nodes
    has_assert = any(isinstance(node, ast.Assert) for node in ast.walk(tree))

    # If no 'assert' statement is found, fail the test immediately
    if not has_assert:
        pytest.fail(f"Test '{item.name}' failed because it contains no assert statement.")
