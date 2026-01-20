from typing import TypedDict, Annotated, List, Any
import operator

class AgentState(TypedDict):
    user_query: str
    plan: List[str]
    insights: Annotated[List[str], operator.add]
    messages: Annotated[List[Any], operator.add]