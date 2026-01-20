from typing import TypedDict, Annotated, List, Any
import operator

class AgentState(TypedDict):
    user_query: str
    messages: Annotated[List[Any], operator.add]
    answer: Annotated[List[str], operator.add] # Must be List[str]