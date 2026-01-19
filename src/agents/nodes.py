from langchain_core.messages import HumanMessage
from src.agents.state import AgentState
import logging

logger = logging.getLogger(__name__)

class AgentNodes:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.llm_with_tools = llm.bind_tools(tools)

    def planner_node(self, state: AgentState):
        """Planner Node: To Break down the complex query into 3 steps."""
        query = state["user_query"]
        prompt = """You are a Financial Analyst Planner. Break down this query into a step-by-step execution plan: {0}.\n 
       Return ONLY the list of steps as plain text, one per line. Do not add introductory text.""".format(query)

        response = self.llm.invoke(prompt)
        plan = [step.strip() for step in response.content.split('\n') if step.strip()]
        return {"plan": plan, "messages": [HumanMessage(content=query)]}

    def research_node(self, state: AgentState):
        """The Researcher: Decides whether to use internal docs or web search based on data availability. """
        plan = state["plan"]
        insights = []
        tool_map = {t.name: t for t in self.tools}

        # Convert Plan to String
        plan_str = "\n".join(["{0}".format(step) for step in plan])

        #Calling all the tools in the single llm prompt 
        prompt = (
            f"Here is the research plan:\n{plan_str}\n\n"
            "Identify ALL necessary financial data or calculations needed for these steps. "
            "Call the appropriate tools immediately. If a step requires no tool, ignore it."
        )
                  
        msg = self.llm_with_tools.invoke(prompt)
        
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                func_name = tool_call['name']
                args = tool_call['args']
                
                if func_name == "financial_data_retriever":
                    if "query" not in args or isinstance(args["query"], dict):
                        args["query"] = plan_str # Fallback to full plan context
                
                if func_name in tool_map:
                    logger.info(f"--- Executing Tool: {func_name} ---")
                    try:
                        result = tool_map[func_name].invoke(args)
                        insights.append(f"Data from {func_name}: {result}")
                    except Exception as e:
                        insights.append(f"Error: {e}")  
                        logger.error("Error executing {0}:{1}".format(func_name,e))   
        else:
            #Fallback in case no tools are called
            insights.append(f"No specific data found via tools. Relying on internal knowledge.")
            logger.debug("No specific data found via tools. Relying on internal knowledge.")

        return {"insights": insights}

    def synthesizer_node(self, state: AgentState):
        """The Writer: Compiles everything into a final report."""
        query = state["user_query"]
        insights = "\n".join(state["insights"])
        
        prompt = """
            User Query: {0}\n\n
            Gathered Insights:\n{1}\n\n
            Generate a professional, comprehensive financial report answering the query based on the insights above.
            Cite the specific data points used. Do not include any plan steps used while generating the report. Avoid duplication of insights in the report. """.format(query,insights)
        
        response = self.llm.invoke(prompt)
        return {"messages": [response]}