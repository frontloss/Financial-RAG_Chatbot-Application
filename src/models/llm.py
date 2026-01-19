
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings as LlamaSettings
from langchain_groq import ChatGroq
from config.settings import settings
from config.settings import settings
import os

def init_models():
    """Initialize Global LlamaIndex Settings and return LangChain wrapper"""
    local_llm = Ollama(model=settings.LLM_MODEL,
                       request_timeout=settings.LLM_TIMEOUT,
                       temperature=settings.LLM_TEMPERATURE,
                       context_window=4096)
    local_embed_model = HuggingFaceEmbedding(model_name = settings.EMBED_MODEL,device="cpu")
    LlamaSettings.llm = local_llm
    LlamaSettings.embed_model = local_embed_model
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets!")
    lc_chat_model = ChatGroq(model=settings.LLM_MODEL,temperature=settings.LLM_TEMPERATURE)

    return lc_chat_model
