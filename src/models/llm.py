
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings as LlamaSettings
from langchain_ollama import ChatOllama
from config.settings import settings
from langchain_groq import ChatGroq
import os

def init_models():
    """Initialize Global LlamaIndex Settings and return LangChain wrapper"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file!")
    local_embed_model = HuggingFaceEmbedding(model_name = settings.EMBED_MODEL,device="cpu")
    local_llm = Groq(model=settings.LLM_MODEL,temperature=settings.LLM_TEMPERATURE,api_key=api_key)
    LlamaSettings.embed_model = local_embed_model
    LlamaSettings.llm = local_llm
    lc_chat_model = ChatGroq(model="llama-3.1-8b-instant",temperature=settings.LLM_TEMPERATURE,api_key = api_key)

    return lc_chat_model
