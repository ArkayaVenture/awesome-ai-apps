"""Knowledge Agent for answering questions from Kubernetes knowledge base."""
import os
from agno.agent import Agent
from agno.models.nebius import Nebius
from typing import Optional
import logging
from ..rag import KubernetesKnowledgeBase

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Knowledge Agent that answers questions using RAG."""
    
    def __init__(
        self,
        knowledge_base: KubernetesKnowledgeBase,
        nebius_api_key: Optional[str] = None
    ):
        """Initialize Knowledge Agent.
        
        Args:
            knowledge_base: Kubernetes knowledge base instance
            nebius_api_key: Nebius API key
        """
        self.knowledge_base = knowledge_base
        self.nebius_api_key = nebius_api_key or os.getenv("NEBIUS_API_KEY")
        
        # Load prompts
        knowledge_prompt = self._load_knowledge_prompt()
        
        self.agent = Agent(
            name="KnowledgeAgent",
            role="Answer questions about Kubernetes using the knowledge base",
            model=Nebius(
                id="meta-llama/Meta-Llama-3.1-70B-Instruct",
                api_key=self.nebius_api_key
            ),
            instructions=[
                knowledge_prompt,
                "Always search the knowledge base first before answering",
                "Provide accurate, up-to-date information from official Kubernetes documentation",
                "Include code examples when relevant",
                "Reference official documentation sources",
            ],
            markdown=True,
        )
    
    def _load_knowledge_prompt(self) -> str:
        """Load knowledge agent prompt."""
        return """You are a Knowledge Agent with access to comprehensive Kubernetes documentation, 
best practices, and industry knowledge.

Your Knowledge Base Includes:
- Official Kubernetes documentation (v1.32+)
- Best practices and patterns
- Industry use cases and case studies
- Troubleshooting guides
- Migration strategies
- Security best practices

Your Role:
- Answer questions about Kubernetes concepts
- Provide best practice recommendations
- Explain how to implement patterns
- Reference official documentation
- Share relevant examples and use cases

Response Guidelines:
- Use RAG to search knowledge base first
- Provide accurate, up-to-date information
- Include code examples when relevant
- Reference official documentation
- Explain concepts clearly for different skill levels"""
    
    def query(self, question: str) -> str:
        """Query the knowledge agent.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        try:
            # Search knowledge base first
            context = self.knowledge_base.query(question)
            
            # Build prompt with context
            prompt = f"""Context from knowledge base:
{context}

User question: {question}

Please answer the question using the context provided. If the context doesn't contain enough information, 
provide a general answer based on your Kubernetes knowledge."""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error in knowledge agent query: {e}")
            return f"Error: {str(e)}"

