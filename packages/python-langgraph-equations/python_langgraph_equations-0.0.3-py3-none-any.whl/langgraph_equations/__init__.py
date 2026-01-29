"""
@copyright: 2026 by Pauli Rikula <pauli.rikula@gmail.com>

@license: MIT <https://opensource.org/license/mit>
"""

__doc__ = """

# python-langgraph-equations

This library provides integration between LangGraph and Category Equations,
providing a set of primitives to construct, evaluate and simplify workflows.

For about python-category-equations see:
 https://github.com/kummahiih/python-category-equations
 
"""

from .get_primitives import get_primitives

from .simplify import __doc__ as simplify_doc

__simplify_doc__ = simplify_doc

__all__ = [get_primitives]