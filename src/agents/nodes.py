from langchain_core.messages import HumanMessage,SystemMessage,AIMessage
from src.agents.state import AgentState
import logging
import asyncio
import re

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
        collected_sources = []
        self.tool_map = {t.name: t for t in self.tools}
        if msg.tool_calls:
            # Parallel Execution Loop
            # Queue the tools execution before calling await on the tasks.
            tasks = [self.tool_map[tool_call["name"]].ainvoke(tool_call["args"]) for tool_call in msg.tool_calls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                try:
                    data = json.loads(str(res))
                    if isinstance(data, dict) and "sources" in data:
                        tool_outputs.append(f"Data: {data['answer']}")
                        collected_sources.extend(data["sources"])
                    else:
                        tool_outputs.append(str(res))
                except:
                    tool_outputs.append(str(res))

        return {"answer": tool_outputs,"sources":collected_sources}

    def synthesizer_node(self, state: AgentState):
        """The Writer: Compiles everything into a final report."""
        query = state["user_query"]
        insights = "\n".join(state["insights"])
        system_prompt = (
            "You are a Senior Financial Analyst at a top-tier investment firm. "
            "Your clients expect rigor, precision, and data-backed insights.\n\n"
            "STRUCTURE YOUR REPORT AS FOLLOWS:\n"
            "1. **Executive Summary**: A 2-sentence bottom line.\n"
            "2. **Key Financials Table**: Compare metrics (Revenue, Margins, YoY Growth) in a Markdown table.\n"
            "3. **Analysis**: Explain *why* the numbers changed (Drivers & Risks).\n"
            "4. **Sources**: List the specific documents used.\n\n"
            "RULES:\n"
            "- speak in a professional, objective tone.\n"
            "- If data is missing, say 'Data not disclosed' instead of guessing.\n"
        )
        user_prompt = f"Query: {query}\n\nData gathered:\n{insights}\n\nWrite the report."
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return {"messages": [response]}