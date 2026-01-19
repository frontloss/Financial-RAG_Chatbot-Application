from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

def get_financial_tools(index):
    """Creates the tool set with access to the specific VectorIndex."""
    query_engine = index.as_query_engine(similarity_top_k=5)
    
    # Wrap LlamaIndex engine as a callable for LangGraph
    @tool("financial_data_retriever")
    def financial_data_retriever(query: str):
        """Useful for retrieving specific financial data, report excerpts, or quantitative metrics from the vector store."""
        response = query_engine.query(query)
        return str(response)

    @tool("calculator_tool")
    def calculator_tool(expression: str):
        """
        Useful for performing mathematical calculations. 
        Input must be a string containing numbers and operators (e.g., "(10 + 5) * 0.2").
        DO NOT use variable names.
        """
        try:
            allowed_names = {"sum": sum, "min": min, "max": max, "abs": abs, "round": round}
            return eval(expression,{"__builtins__":{}},allowed_names)
        except NameError as e:
            # Provide a specific error to help the Agent self-correct
            return f"Error: You used a variable name '{e.name}' which is not defined. Please perform the calculation using explicit numbers only (e.g. '25.5 + 10')."
        except SyntaxError:
            return f"Error: Invalid syntax in expression '{expression}'. Check for missing parentheses or operators."
        except Exception as e:
            logger.error("Error calculating {0}: {1}".format(expression,e))
            return "Error calculating {0}: {1}".format(expression,e)
        
    return [financial_data_retriever,calculator_tool]