"""
Defining the GLOBAL context (capabilities) for a Protein interpreter.

NOTE:
    What we define as "global" is not the same as in most languages.
    It is simply a part of the first frame on the lexical stack,
    which contains necessary functions.

    This file should contain ONLY functions that require no interpreter state.

    (It is on top of the Jinja2 utilities.)
"""

import os

import keyring
from markdown_it import MarkdownIt

from .sql import osquery
from .util import dequote, LITERAL_PREFIX



def jinja_assert(condition, message=None):
    """
    Assertions for expressions, necessary in a Jinja2 environment.

    e.g.:
        {{ assert(entry.title is not none, "Missing title") }}

    The explicit purpose of this function, is to provide the user of Protein
    with a tool with which to inspect what's happening on the host (Python).

    It is a "look-through" function, or 
    a _debugging hook_ that fishes the host-side state.

    There _could_ (and probably _should_) be an assert statement for Protein,
    such as .require.

    """
    assert condition, message
    return ""



def quote(value: str) -> str:
    """
    Mark the given string as literal by prefixing the #!literal sentinel.

    This transformation is idempotent: if the value is already quoted,
    it is returned unchanged. It is the inverse of `dequote`.
    """
    if not isinstance(value, str):
        raise TypeError("quote() expects a string")
    if value.startswith(LITERAL_PREFIX):
        return value
    return f"{LITERAL_PREFIX}{value}"




# Create a single parser instance (fast, reusable)
_md = MarkdownIt()

def to_html(s: str) -> str:
    """
    Convert Markdown text to HTML using markdown-it-py.

    - Deterministic output
    - Safe for use inside Protein templates

    Forward‑compatibility:
        This function currently assumes Markdown as the native markup format.
        Future versions may accept an explicit `format` argument to support
        additional markup languages.
    """
    if not isinstance(s, str):
        raise TypeError("render_markdown_to_html expects a string")

    return _md.render(s)


# ---------------------------------
# Global functions for Jinja2
# ---------------------------------
GLOBAL_CONTEXT = {
    # needed for reading environment variables
    "getenv": os.getenv, 

    # needed for accessing keyrings
    "get_password": keyring.get_password, 

    # needed for accessing operating system info (security, etc.)
    "osquery": osquery, 

    # for debugging the host environment from Protein expressions 
    "assert": jinja_assert,

    }

GLOBAL_FILTERS = {

    # needed for Jinja, to prevent interpretation of a template
    "quote": quote,

    # needed in Jinja, if the literal prefix of a template must be stripped
    # so that the string can be evaluated.
    # In Lisp, it would not be unlike the comma (,)
    "dequote": dequote, 

    # converting Markdown to HTML
    "to_html": to_html
}

GLOBAL_CONTEXT.update(GLOBAL_FILTERS)