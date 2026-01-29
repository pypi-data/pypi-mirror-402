"""
Low-level tests for literal prefix quoting and dequoting
(prefix is "#!literal")

see also: test_literal_prefix.py
"""

import pytest

from protein.global_context import quote, dequote, LITERAL_PREFIX


# ------------------------------------------------------------
# Basic quoting
# ------------------------------------------------------------

def test_quote_basic():
    assert quote("hello") == LITERAL_PREFIX + "hello"
    assert quote("{{ x }}") == LITERAL_PREFIX + "{{ x }}"


# ------------------------------------------------------------
# Basic dequoting
# ------------------------------------------------------------

def test_dequote_basic():
    assert dequote(LITERAL_PREFIX + "hello") == "hello"
    assert dequote(LITERAL_PREFIX + "{{ x }}") == "{{ x }}"


# ------------------------------------------------------------
# Idempotence of quote
# ------------------------------------------------------------

def test_quote_idempotent():
    assert quote(LITERAL_PREFIX + "hello") == LITERAL_PREFIX + "hello"
    assert quote(quote("hello")) == quote("hello")


# ------------------------------------------------------------
# Idempotence of dequote
# ------------------------------------------------------------

def test_dequote_idempotent():
    assert dequote("hello") == "hello"
    assert dequote(dequote(LITERAL_PREFIX + "hello")) == "hello"


# ------------------------------------------------------------
# Reversibility: quote → dequote
# ------------------------------------------------------------

def test_quote_then_dequote():
    assert dequote(quote("hello")) == "hello"
    assert dequote(quote("{{ x }}")) == "{{ x }}"


# ------------------------------------------------------------
# Reversibility: dequote → quote
# ------------------------------------------------------------

def test_dequote_then_quote():
    assert quote(dequote(LITERAL_PREFIX + "hello")) == LITERAL_PREFIX + "hello"
    assert quote(dequote(LITERAL_PREFIX + "{{ x }}")) == LITERAL_PREFIX + "{{ x }}"


# ------------------------------------------------------------
# Empty string behavior
# ------------------------------------------------------------

def test_empty_string():
    assert quote("") == LITERAL_PREFIX
    assert dequote(LITERAL_PREFIX) == ""
    assert dequote("") == ""


# ------------------------------------------------------------
# Prefix inside string should not count as quoted
# ------------------------------------------------------------

def test_prefix_inside_string_not_quoted():
    s = f"hello {LITERAL_PREFIX} world"
    assert quote(s) == LITERAL_PREFIX + s
    assert dequote(s) == s


# ------------------------------------------------------------
# Type behavior (strict)
# ------------------------------------------------------------

def test_non_string_input():
    with pytest.raises(TypeError):
        quote(123)
    with pytest.raises(TypeError):
        dequote(123)
