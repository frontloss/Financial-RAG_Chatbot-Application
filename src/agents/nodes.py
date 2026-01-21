from langchain_core.messages import HumanMessage
from src.agents.state import AgentState
import logging
import asyncio
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

    async def research_node(self, state: AgentState):
        """The Researcher: Executes tools as per the plan steps. """
        plan = state["plan"]
        insights = []
        tool_map = {t.name: t for t in self.tools}

        #Convert Plan to String
        plan_str = "\n".join(["{0}".format(step) for step in plan]
        )

        #Calling all the tools in the single llm prompt
        prompt = """Here is the research plan:\n{0}\n\n"
            Identify ALL necessary financial data or calculations needed for these steps.\n
            **IMPORTANT: While calling the 'calculator_tool', You must extract the ACTUAL NUMBERS from previous steps to use here. Do NOT\n
            use variable name.**\n
            " - CORRECT: 'calculator_tool(expression = "(24.5 + 23.2) / 2")\n"
            " - WRONG: 'calculator_tool(expression = "mean(TCS_Margin)")\n"
            Call the appropriate tools immediately. If a step requires no tool, ignore it.""".format(plan_str)
        
        msg = await self.llm_with_tools.ainvoke(prompt)
        tool_outputs = []
        self.tool_map = {t.name: t for t in self.tools}
        if msg.tool_calls:
            # 4. Parallel Execution Loop
            tasks = []
            for tool_call in msg.tool_calls:
                func_name = tool_call['name']
                args = tool_call['args']
                
                if "query" in args and isinstance(args["query"], dict):
                     # Fallback to the specific plan step if possible, or generic query
                     args["query"] = str(plan_str) 

                if func_name in self.tool_map:
                    # Queue the tool execution (don't await yet)
                    tasks.append(self.tool_map[func_name].ainvoke(args))
            
            # Fire all tools at once (Wait for longest one only)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                tool_outputs.append(str(res))

        return {"insights": tool_outputs}

    def synthesizer_node(self, state: AgentState):
        """The Writer: Compiles everything into a final response."""
        query = state["user_query"]
        insights = "\n".join(state["insights"])
        
        prompt = """
            User Query: {0}\n\n
            Gathered Insights:\n{1}\n\n
            Generate a professional, comprehensive response answering the query based on the insights above in no more than 100 words.
            Cite the specific data points used. Do not include any plan steps used while generating the response. Avoid duplication of insights in the reponse. """.format(query,insights)
        
        response = self.llm.invoke(prompt)
        return {"messages": [response]}