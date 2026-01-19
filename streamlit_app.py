import streamlit as st
import nest_asyncio

# Applying asyncio loops in Streamlit
nest_asyncio.apply()

from src.models.llm import init_models
from src.database.vector_store import get_vector_index
from src.ingestion.loader import load_and_chunk_data
from src.tools.definitions import get_financial_tools
from src.agents.graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Financial Analyst Agent",
    page_icon="Ef",
    layout="wide"
)

st.title("AI Financial Analyst")
st.markdown("**Powered by Llama 3.2, LangGraph & LlamaIndex.**")
st.markdown("""
This chatbot can help you research financial reports, perform calculations, and generate insights.
""")

# SIDEBAR: Model Details
with st.sidebar:
    st.markdown("### Model Details")
    st.info("Embedding: BAAI/bge-m3\nLLM: Llama 3.2 (3B)")

@st.cache_resource(show_spinner="Loading AI Models & Database...")
def initialize_agent():
    """
    Initializes the agent workflow. Cached to prevent reloading 
    heavy models on every interaction.
    """
    try:
        # Initialize LLM & Embeddings
        llm = init_models()
        
        # Connect to Vector Store (ChromaDB)
        index = get_vector_index()
        
        # Create Tools
        tools = get_financial_tools(index)
        
        # Compile Graph
        graph = build_graph(llm, tools)
        
        return graph
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None

app = initialize_agent()

### CHAT INTERFACE

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! Ask me anything related to latest financial reports of TCS, Infosys and Microsoft."}
    ]

# Display Chat History
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# Handle User Input
if prompt := st.chat_input("Ex: Compare the Net Profit of TCS and Infosys for 2023"):
    
    # Display User Message immediately
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Run Agent
    if app:
        with st.chat_message("assistant"):
            status_container = st.status("Thinking...", expanded=True)
            
            try:
                # Prepare inputs for the graph
                inputs = {
                    "user_query": prompt,
                    "plan": [],
                    "insights": [],
                    "messages": []
                }
                
                #Create a placeholder for the final answer
                answer_placeholder = st.empty()
                full_response = ""
                
                # We stream the events from the graph
                for event in app.stream(inputs, stream_mode="updates"):
                    
                    # 1. Handle Planner Output
                    if "planner" in event:
                        plan = event["planner"]["plan"]
                        with status_container:
                            st.write("**Plan Created:**")
                            for step in plan:
                                st.write(f"- {step}")
                                
                    # 2. Handle Researcher Output
                    if "researcher" in event:
                        insights = event["researcher"]["insights"]
                        with status_container:
                            with st.expander("Research Progress", expanded=False):
                                for insight in insights:
                                    st.write(insight)
                            status_container.update(label="Research Complete! Writing report...", state="running")

                    # 3. Handle Synthesizer (The Final Answer)
                    if "synthesizer" in event:
                        # The synthesizer returns a "messages" list with the AIMessage
                        # We grab the content directly
                        final_msg = event["synthesizer"]["messages"][-1]
                        
                        #Displaying the streaming chunks of completed message to the markdown.
                        full_response = final_msg.content
                        answer_placeholder.markdown(full_response)
                
                status_container.update(label="Finished", state="complete", expanded=False)
                
                # Save final response to history
                st.session_state["messages"].append({"role": "assistant", "content": full_response})

            except Exception as e:
                status_container.update(label="Error", state="error")
                st.error(f"Error: {e}")