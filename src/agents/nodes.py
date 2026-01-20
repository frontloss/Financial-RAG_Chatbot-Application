import logging
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

class AgentNodes:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        # Create a dictionary for easy tool lookup
        self.tool_map = {t.name: t for t in tools}
        self.llm_with_tools = llm.bind_tools(tools)

    def answer_node(self, state: AgentState):
        """
        Answer Node: Identifies tools, EXECUTES them, and generates the final answer.
        """
        query = state["user_query"]
        
        # Ask LLM which tools to use
        prompt = f"User Query: {query}. Identify necessary financial data and call tools to fetch it."
        initial_msg = self.llm_with_tools.invoke(prompt)
        
        tool_outputs = []
        
        # Check if the LLM wants to call tools
        if initial_msg.tool_calls:
            logger.info(f"Tools triggered: {len(initial_msg.tool_calls)}")
            
            for tool_call in initial_msg.tool_calls:
                func_name = tool_call['name']
                args = tool_call['args']
                
                if "query" in args and isinstance(args["query"], dict):
                    args["query"] = query # Fallback for Llama 3.2 bug
                
                # 3. EXECUTE THE TOOL
                if func_name in self.tool_map:
                    try:
                        logger.info(f"Executing {func_name} with {args}")
                        result = self.tool_map[func_name].invoke(args)
                        tool_outputs.append(f"Data from {func_name}: {str(result)}")
                    except Exception as e:
                        tool_outputs.append(f"Error executing {func_name}: {str(e)}")
        else:
            # If no tools called, just return the text (e.g. general knowledge)
            tool_outputs.append(initial_msg.content)

        # Synthesize the data into a Natural Language Answer
        context_data = "\n\n".join(tool_outputs)
        synthesis_prompt = (
            f"User Query: {query}\n\n"
            f"Raw Data Gathered:\n{context_data}\n\n"
            "Based on the raw data above, write a clear, direct answer to the user's query. "
            "Do NOT write code. Write a financial report."
        )
        
        final_response = self.llm.invoke(synthesis_prompt)

        return {
            "answer": [final_response.content], 
            "messages": [HumanMessage(content=query), final_response]
        }

    def reviewer_node(self, state: AgentState):
        """The Reviewer: Validates the text answer."""
        query = state["user_query"]
        
        current_answer = state["answer"][-1] 
        
        prompt = (
            f"User Query: {query}\n\n"
            f"Draft Answer:\n{current_answer}\n\n"
            "Review this answer. If it answers the query accurately based on the context, output the answer as is. "
            "If it is missing data or unclear, rewrite it to be better. Answer should be no more than 30-40 words."
        )
        
        response = self.llm.invoke(prompt)
        return {"messages": [response]}