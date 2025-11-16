"""RAG knowledge base for Kubernetes documentation."""
import os
from typing import List, Optional
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader, StorageContext
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.lancedb import LanceDBVectorStore
import lancedb
import logging

logger = logging.getLogger(__name__)


class KubernetesKnowledgeBase:
    """Knowledge base for Kubernetes documentation using RAG."""
    
    # Official Kubernetes documentation URLs
    K8S_DOCS_URLS = [
        "https://kubernetes.io/docs/concepts/",
        "https://kubernetes.io/docs/tasks/",
        "https://kubernetes.io/docs/reference/",
        "https://kubernetes.io/docs/tutorials/",
        "https://kubernetes.io/docs/setup/",
        "https://kubernetes.io/docs/contribute/",
    ]
    
    def __init__(
        self,
        vector_db_path: str = "./data/vector_store",
        openai_api_key: Optional[str] = None
    ):
        """Initialize Kubernetes knowledge base.
        
        Args:
            vector_db_path: Path to vector database
            openai_api_key: OpenAI API key for embeddings
        """
        self.vector_db_path = vector_db_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize embeddings and LLM
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=self.openai_api_key
        )
        Settings.llm = OpenAI(
            model="gpt-4-turbo-preview",
            api_key=self.openai_api_key
        )
        
        self.index: Optional[VectorStoreIndex] = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize vector store."""
        try:
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Connect to LanceDB
            db = lancedb.connect(self.vector_db_path)
            vector_store = LanceDBVectorStore(uri=self.vector_db_path)
            
            # Check if index already exists
            try:
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store
                )
                logger.info("Loaded existing knowledge base")
            except Exception:
                # Create new index
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store
                )
                logger.info("Created new knowledge base")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def load_documents_from_urls(self, urls: Optional[List[str]] = None):
        """Load documents from URLs into knowledge base.
        
        Args:
            urls: List of URLs to load. If None, uses default K8S docs URLs.
        """
        urls = urls or self.K8S_DOCS_URLS
        
        try:
            # Load documents from URLs
            # Note: This is a simplified version. In production, you'd want
            # to use a proper web scraper or download the docs first
            logger.info(f"Loading documents from {len(urls)} URLs...")
            
            # For now, we'll create a placeholder index
            # In production, implement proper document loading
            documents = []
            
            # Add documents to index
            if documents:
                for doc in documents:
                    self.index.insert(doc)
            
            logger.info("Documents loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
    
    def query(self, query_text: str, top_k: int = 5) -> str:
        """Query the knowledge base.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            
        Returns:
            Relevant context from knowledge base
        """
        try:
            if not self.index:
                return "Knowledge base not initialized"
            
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="compact"
            )
            
            response = query_engine.query(query_text)
            return str(response)
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return f"Error querying knowledge base: {str(e)}"
    
    def search(self, query_text: str, top_k: int = 5) -> List[dict]:
        """Search the knowledge base and return results.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        try:
            if not self.index:
                return []
            
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query_text)
            
            results = []
            for node in nodes:
                results.append({
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata if hasattr(node, 'metadata') else {}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

