"""
Low-level tests for literal prefix handling
(prefix is "#!literal")
"""

from string import Template

import pytest
from protein import Interpreter
from protein.util import LITERAL_PREFIX, dequote

# -------------------------
# dequote tests
# -------------------------

def test_dequote_present():
    s = f"{LITERAL_PREFIX}   Hello world"
    assert dequote(s) == "Hello world"


def test_dequote_absent():
    s = "Hello world"
    assert dequote(s) == "Hello world"


def test_dequote_exact_prefix():
    s = LITERAL_PREFIX
    assert dequote(s) == ""


def test_dequote_non_string():
    with pytest.raises(TypeError):
        assert dequote(123) == 123


# -------------------------
# evaluate_expression tests
# -------------------------

def test_eval_preserves_prefix_in_normal_mode():
    "In normal mode, the literal prefix is preserved"
    p = Interpreter()

    # Build the expression safely using Template
    expr = Template("$prefix Hello {{ name }}").substitute(prefix=LITERAL_PREFIX)

    result = p.evaluate_expression(expr, final=False)
    assert result == expr


def test_eval_strips_prefix_in_final_mode():
    "In final mode, the literal prefix is stripped"
    p = Interpreter()

    expr = Template("$prefix Hello {{ name }}").substitute(prefix=LITERAL_PREFIX)

    result = p.evaluate_expression(expr, final=True)
    assert result == "Hello {{ name }}"


def test_eval_runs_jinja_when_no_prefix():
    "When there is no literal prefix, Jinja2 is evaluated normally"
    p = Interpreter()
    p.stack["name"] = "Laurent"

    expr = "Hello {{ name }}"
    result = p.evaluate_expression(expr)

    assert result == "Hello Laurent"

