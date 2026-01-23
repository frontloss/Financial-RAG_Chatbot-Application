from langchain_core.tools import tool
import logging
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.query_engine import RetrieverQueryEngine
import json
import re

logger = logging.getLogger(__name__)

def get_financial_tools(index):
    """Creates the tool set with access to the specific VectorIndex."""
    # Enable Hybrid Search (Vector + Keyword)
    # alpha=0.7 means 70% Vector, 30% Keyword importance    
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=20,
        vector_store_query_mode="hybrid", 
        alpha=0.7, 
    )
    # CROSSENCODER RERANKING 
    # Filter from top 20 semantically relevant chunks down to top 5 absolute best chunks
    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=5)

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        node_postprocessors=[reranker]
    )
    
    @tool("financial_data_retriever")
    def financial_data_retriever(query: str):
        """
        Fetches financial data with source citations.
        Returns JSON with 'answer' and 'sources'.
        """
    
        response = query_engine.query(query)
        
        sources = [
            f"Content: {n.node.get_content()[:500]}" 
            for n in response.source_nodes
        ]
        
        return json.dumps({
            "answer": str(response),
            "sources": sources
        })
            
    @tool("calculator_tool")
    def calculator_tool(expression: str):
        """
        Evaluates math. REJECTS text or variables.
        Example Valid: '25.5 + 10'
        Example Invalid: 'revenue + 10'
        """
        try:
            # If the expression contains letters (a-z), it's trying to use variables. Reject it.
            if re.search(r'[a-zA-Z]', expression):
                return (
                    "Error: You passed text/variables to the calculator. "
                    "It ONLY accepts numbers (e.g., '100 - 50'). "
                    "Please use 'financial_data_retriever' to get the actual numbers first."
                )

            return eval(expression)
            
        except Exception as e:
            return f"Math Error: {e}"
        
    return [financial_data_retriever,calculator_tool]

