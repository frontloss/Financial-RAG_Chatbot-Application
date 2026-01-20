
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings as LlamaSettings
from langchain_ollama import ChatOllama
from config.settings import settings

def init_models():
    """Initialize Global LlamaIndex Settings and return LangChain wrapper"""
    local_embed_model = HuggingFaceEmbedding(model_name = settings.EMBED_MODEL,device="cpu")
    LlamaSettings.embed_model = local_embed_model
    lc_chat_model = ChatOllama(model=settings.LLM_MODEL,temperature=settings.LLM_TEMPERATURE)

    return lc_chat_model
