import os
import re
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def load_and_chunk_data():
    """Loads documents, parses metadata, and chunks them. """
    dataset_metadata = []
    reports_dataset_path = "Financial Reports Dataset"
    companies = os.listdir(reports_dataset_path)
    for company in companies:
        filenames = os.path.join(reports_dataset_path,"/"+company)
        for filename in filenames:
            year_match = re.search(r'(20\d{2})', filename)
            year = int(year_match.group(1)) if year_match else "Unknown"
            dataset = {"year":year,"company":company,"source_filename":filename}
            dataset_metadata.append(dataset)
    
    documents = []
    llama_parse_data_path = "LlamaParsed_pdf_data"
    filenames = os.listdir(llama_parse_data_path)
    for filename, meta in zip(filenames,dataset_metadata):
        f = open(llama_parse_data_path + "/" + filename,'r',encoding="utf-8")
        full_text = f.read()
        doc = Document(text = full_text, metadata = meta)
        documents.append(doc)
        f.close()

    # Context-Aware Chunking
    node_parser = MarkdownNodeParser()
    nodes = node_parser.get_nodes_from_documents(documents)
    logger.info(f"Created {len(nodes)} chunks from {len(documents)} documents.")
    
    return nodes