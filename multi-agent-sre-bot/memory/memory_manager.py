"""Memory management for SRE bot using Memori."""
import os
from typing import Optional
import logging

# Try to import Memori, but make it optional for Python 3.12+
try:
    from memorisdk import Memori, MemoriContext
    MEMORI_AVAILABLE = True
except ImportError:
    MEMORI_AVAILABLE = False
    Memori = None
    MemoriContext = None

logger = logging.getLogger(__name__)


class MemoryManager:
    """Memory manager for context retention."""
    
    def __init__(
        self,
        database_url: str = "sqlite:///sre_bot_memory.db",
        openai_api_key: Optional[str] = None
    ):
        """Initialize memory manager.
        
        Args:
            database_url: Database connection URL
            openai_api_key: OpenAI API key for memory operations
        """
        self.database_url = database_url
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not MEMORI_AVAILABLE:
            logger.warning("Memori not available (requires Python <3.12). Memory features will be limited.")
            self.memori = None
            return
        
        try:
            self.memori = Memori(
                database_connect=database_url,
                namespace="sre_bot",
                conscious_ingest=True,  # Working memory
                auto_ingest=True,  # Dynamic search
                openai_api_key=self.openai_api_key,
                verbose=False
            )
            self.memori.enable()
            logger.info("Memory system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            self.memori = None
    
    def record_conversation(self, user_input: str, ai_output: str):
        """Record a conversation in memory.
        
        Args:
            user_input: User's input
            ai_output: AI's response
        """
        if not self.memori:
            return
        
        try:
            context = MemoriContext(
                user_input=user_input,
                assistant_output=ai_output
            )
            self.memori.ingest(context)
        except Exception as e:
            logger.error(f"Error recording conversation: {e}")
    
    def search_memory(self, query: str, limit: int = 5) -> list:
        """Search memory for relevant context.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant memory entries
        """
        if not self.memori:
            return []
        
        try:
            # Use Memori's search functionality
            # This is a simplified version - adjust based on actual Memori API
            results = self.memori.search(query, limit=limit)
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    def get_context(self, query: str) -> str:
        """Get relevant context from memory for a query.
        
        Args:
            query: Query to get context for
            
        Returns:
            Context string
        """
        results = self.search_memory(query)
        
        if not results:
            return ""
        
        context_parts = []
        for result in results:
            if isinstance(result, dict):
                context_parts.append(result.get("content", str(result)))
            else:
                context_parts.append(str(result))
        
        return "\n\n".join(context_parts)

