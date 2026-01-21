from typing import Literal
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
import os

# 1. Define the Output Schema
class RouteDecision(BaseModel):
    complexity: Literal["simple", "complex"] = Field(
        ..., 
        description="Select 'simple' for direct data lookups. Select 'complex' for comparisons, aggregations, or multi-step reasoning."
    )

# 2. Initialize Fast Router Model
router_llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    api_key = os.getenv("GROQ_API_KEY"), 
    temperature=0
).with_structured_output(RouteDecision)

# 3. The Router Function
def route_query_ai(state):
    query = state["user_query"]
    
    # Fast Classification
    decision = router_llm.invoke(
        f"Classify this query: '{query}'.\n"
        "SIMPLE: asking for a single fact, number, or document (e.g. 'Revenue of TCS').\n"
        "COMPLEX: asking for comparison, reasoning, trends, or math (e.g. 'Compare TCS and Infy', 'Reason for revenue drop')."
    )
    
    if decision.complexity == "complex":
        return "planner"
    else:
        return "researcher"