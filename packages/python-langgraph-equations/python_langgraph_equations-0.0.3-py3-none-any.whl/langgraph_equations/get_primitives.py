"""
@copyright: 2026 by Pauli Rikula <pauli.rikula@gmail.com>

@license: MIT <https://opensource.org/license/mit>
"""

from langgraph.graph import StateGraph
from category_equations import from_operator


def get_primitives(graph: StateGraph, debug: bool = False):
    """
## get_primitives(graph: StateGraph, debug: bool = False)

Function `get_primitives` returns a tuple (I, O, C) 
that represents the set of equation construction primitives 
for the given langraph StateGraph. The `connect_edge` function
is used to add edges to the graph, optionally printing them if `debug` is True.

The created primitives can be used to manipulate workflows as equations and
to optimize and compare their structure.

Usage example:

Set up a StateGraph and nodes representing various text processing steps:

    >>> from langgraph.graph import StateGraph, END, START

    >>> from typing import TypedDict, List

    >>> from langgraph_equations import get_primitives

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

Now we can use the `get_primitives ` function to obtain the equation primitives and construct a workflow

    >>> I, O, C = get_primitives(graph, debug=True)

    >>> term = C(START) * C("process_input") * C("summarize", "classify", "embed") * C("combine_results") * C(END)

On calling `evaluate`, the term will print the edges (debug=True) and add the edges to the graph:

    >>> term.evaluate()
    __start__ → process_input
    classify → combine_results
    combine_results → __end__
    embed → combine_results
    process_input → classify
    process_input → embed
    process_input → summarize
    summarize → combine_results

Now we can compile and invoke the graph with an input state:

    >>> app = graph.compile()
    
    >>> app.invoke({"text": "LangGraph makes parallel workflows easy!"})
    {'text': 'LangGraph makes parallel workflows easy!', 'summary': 'Summary of: LangGraph makes parallel workf...', 'category': 'short', 'embedding': [40, 1.0, 0.5]}
    
    """
    def connect_edge(src: str, dst: str):
        if debug:
            print(src, "→", dst)
        graph.add_edge(src, dst)
    I, O, C = from_operator(connect_edge)
    return I, O, C