"""
@copyright: 2026 by Pauli Rikula <pauli.rikula@gmail.com>

@license: MIT <https://opensource.org/license/mit>
"""

__doc__ = """
## How to use `category_equations.simplify` with LangGraph

Lets setup the workflow graph first:

    >>> from langgraph.graph import StateGraph, END, START

    >>> from typing import TypedDict, List

    >>> from langgraph_equations import get_primitives
    
    >>> from category_equations import simplify, EquationMap

    >>> class State(TypedDict):
    ...     text: str
    ...     summary: str
    ...     category: str
    ...     embedding: List[float] 

    >>> def process_input(state: State):
    ...     return {"text": state["text"].strip()}

    >>> def summarize(state: State):
    ...     text = state["text"]
    ...     return {"summary": f"Summary of: {text[:30]}..."}

    >>> def classify(state: State):
    ...     text = state["text"]
    ...     category = "long" if len(text) > 50 else "short"
    ...     return {"category": category}

    >>> def embed(state: State):
    ...     # Fake embedding for demonstration
    ...     return {"embedding": [len(state["text"]), 1.0, 0.5]}

    >>> def combine_results(state: State):
    ...     return state

    >>> graph = StateGraph(State)

    >>> graph = graph.add_node("process_input", process_input)

    >>> graph = graph.add_node("summarize", summarize)

    >>> graph = graph.add_node("classify", classify)

    >>> graph = graph.add_node("embed", embed)

    >>> graph = graph.add_node("combine_results", combine_results)

Now we can use the `get_primitives ` function to obtain the equation primitives and construct a workflow in a way 
that can be simplified with `category_equations.simplify`:

    >>> I, O, C = get_primitives(graph, debug=True)

    >>> term =  (
    ...         O * C(START) * C("process_input") * O + 
    ...         O * C("process_input") * C("summarize") * O + 
    ...         O * C("process_input") * C("classify")  * O + 
    ...         O * C("process_input") * C("embed")  * O + 
    ...         O * C("summarize") * C("combine_results") * O + 
    ...         O * C("classify") * C("combine_results") * O + 
    ...         O * C("embed") * C("combine_results") * O +
    ...         O * C("combine_results") * C(END) * O
    ... )

Now we can use the `category_equations.simplify` function to simplify the workflow. 
First we need to create an `EquationMap` where the search of simplifications will be done:

    >>> m = EquationMap(I, O, C)

Then we can try to simplify the term:

    >>> max_depth = 2000
    >>> simplified_term, path = simplify(term, max_depth, m)

Because the equation solver quality is questionable,
it is always a good idea to test the resulting simplified term to see if it is equivalent to the original term.

    >>> term == simplified_term
    True

All seems to be good, so lets see how the simplified term looks like:

    >>> simplified_term
    (O * C(__start__) * C(process_input) * C(summarize) * O + O * C(process_input) * C(classify) * C(combine_results) * O) + O * C(process_input) * C(embed) * C(combine_results) * C(__end__) * O

To see the steps taken during simplification, we can iterate over the `paths`, but we skip that because it is boring.

    >>> len(path)
    40

It is pretty easy perform better in simplifying than this, which indicates that the equation solver is not good enough.
You can however use this to test your own terms and see if you did any mistakes in constructing them:

    >>> simplified_manually = O * C(START) * C("process_input") * C("summarize", "classify", "embed") * C("combine_results") * C(END) * O
    >>> term == simplified_manually
    True

"""