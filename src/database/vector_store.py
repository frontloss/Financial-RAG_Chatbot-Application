import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from config.settings import settings

def get_vector_index(nodes=None):
    """
    Get existing index or create a new one if nodes are provided.
    """
    # Initialize ChromaDB Client
    db = chromadb.PersistentClient(path=settings.DB_PATH)
    chroma_collection = db.get_or_create_collection(settings.COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if nodes:
        # Create new index from processed nodes
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context
        )
    else:
        # Load existing index
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )
    
    return index