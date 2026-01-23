import streamlit as st
import asyncio
import nest_asyncio

try:
    nest_asyncio.apply()
except ValueError:
    pass

from src.models.llm import init_models
from src.database.vector_store import get_vector_index
from src.tools.definitions import get_financial_tools
from src.agents.graph import build_graph

st.set_page_config(page_title="AI Financial Analyst", layout="wide")
st.title("AI Financial Analyst ")

@st.cache_resource
def initialize_agent():
    llm = init_models()
    index = get_vector_index()
    tools = get_financial_tools(index)
    return build_graph(llm, tools)

app = initialize_agent()

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ask me about finance related to TCS, Infosys and Microsoft"}]

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])
    if "sources" in msg and msg["sources"]:
        with st.expander(" Evidence (Source Docs)"):
            for s in msg["sources"]:
                st.info(s)

async def process_query(prompt, app_instance, status_container, placeholder):
    inputs = {"user_query": prompt, "plan": [], "messages": []}
    full_response = ""
    collected_sources = []
    
    async for event in app_instance.astream(inputs, stream_mode="updates"):
        
        if "planner" in event:
            plan = event["planner"].get("plan", [])
            with status_container:
                st.write("**Plan Created:**")
                for step in plan:
                    st.write(f"- {step}")

        if "researcher" in event:
            node_out = event["researcher"]
            new_sources = node_out.get("sources", [])
            collected_sources.extend(new_sources)
            
            with status_container:
                st.write(f"Parsed {len(new_sources)} new documents.")

        if "synthesizer" in event:
            final_msg = event["synthesizer"]["messages"][-1]
            full_response = final_msg.content
            placeholder.markdown(full_response)

    return full_response, collected_sources

if prompt := st.chat_input("Ex: Compare TCS and Infosys Net Profit"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    if app:
        with st.chat_message("assistant"):
            status = st.status("Thinking...", expanded=True)
            placeholder = st.empty()
            
            response, sources = asyncio.run(process_query(prompt, app, status, placeholder))
            
            status.update(label="Complete", state="complete", expanded=False)
            
            if sources:
                with st.expander("View Authentic Sources (Evidence)"):
                    for s in sources:
                        st.info(s)
            
            st.session_state["messages"].append({
                "role": "assistant", 
                "content": response, 
                "sources": sources
            })