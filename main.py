import argparse
import nest_asyncio
import asyncio
from config.logging_config import setup_logging
import logging

# Setup Logging immediately
setup_logging()
logger = logging.getLogger(__name__)

# Apply asyncio patch
nest_asyncio.apply()

from src.models.llm import init_models
from src.database.vector_store import get_vector_index
from src.ingestion.loader import load_and_chunk_data
from src.tools.definitions import get_financial_tools
from src.agents.graph import build_graph

def ingest_data():
    """Run the ingestion pipeline."""
    logger.info("Starting data ingestion...")
    init_models() # Initialize embedding models
    nodes = load_and_chunk_data() # Load and Chunk
    get_vector_index(nodes=nodes) # Index and Persist
    logger.info("Ingestion complete. Index saved.")

async def run_agent(query: str):
    """Run the agentic chatbot."""
    # 1. Init Models & DB
    logger.info("Initializing models and database...")
    llm = init_models()
    index = get_vector_index() # Load existing index
    
    # 2. Init Tools & Graph
    tools = get_financial_tools(index)
    app = build_graph(llm, tools)
    
    # 3. Execute
    logger.info(f"\n--- Processing Query: {query} ---\n")
    inputs = {
        "user_query": query,
        "plan": [],
        "insights": [],
        "messages": []
    }
    
    result = await app.ainvoke(inputs)
    final_answer = result['messages'][-1].content
    
    print(final_answer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial RAG Chatbot")
    parser.add_argument("--ingest", action="store_true", help="Run data ingestion and indexing")
    parser.add_argument("--query", type=str, help="The query to ask the chatbot")
    
    args = parser.parse_args()
    
    if args.ingest:
        ingest_data()
    elif args.query:
        asyncio.run(run_agent(args.query))
    else:
        # Default behavior if no args (useful for interactive debugging)
        query = input("Enter your financial query: ")
        asyncio.run(run_agent(query))