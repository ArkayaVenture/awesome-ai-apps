"""FastAPI application for SRE Bot."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

from ..config import settings
from ..connectors import (
    KubernetesConnector,
    AWSEKSConnector,
    AzureAKSConnector,
    GCPGKEConnector
)
from ..mcp import KubernetesMCPServer
from ..rag import KubernetesKnowledgeBase
from ..memory import MemoryManager
from ..agents import (
    CoordinatorAgent,
    TroubleshootingAgent,
    MonitoringAgent,
    AutomationAgent,
    KnowledgeAgent
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent SRE Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
k8s_connector: Optional[KubernetesConnector] = None
mcp_server: Optional[KubernetesMCPServer] = None
knowledge_base: Optional[KubernetesKnowledgeBase] = None
memory_manager: Optional[MemoryManager] = None
coordinator_agent: Optional[CoordinatorAgent] = None


@app.on_event("startup")
async def startup():
    """Initialize components on startup."""
    global k8s_connector, mcp_server, knowledge_base, memory_manager, coordinator_agent
    
    try:
        # Initialize Kubernetes connector based on platform
        if settings.platform == "aws":
            k8s_connector = AWSEKSConnector(
                cluster_name=settings.aws_eks_cluster_name or "",
                region=settings.aws_region or "us-east-1",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        elif settings.platform == "azure":
            k8s_connector = AzureAKSConnector(
                subscription_id=settings.azure_subscription_id or "",
                resource_group=settings.azure_resource_group or "",
                cluster_name=settings.azure_aks_cluster_name or "",
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
                tenant_id=settings.azure_tenant_id
            )
        elif settings.platform == "gcp":
            k8s_connector = GCPGKEConnector(
                project_id=settings.gcp_project_id or "",
                zone=settings.gcp_zone or "",
                cluster_name=settings.gcp_gke_cluster_name or "",
                credentials_path=settings.google_application_credentials
            )
        else:
            k8s_connector = KubernetesConnector(kubeconfig=settings.kubeconfig)
        
        # Initialize MCP server (optional)
        mcp_server = None
        try:
            mcp_server = KubernetesMCPServer(timeout=settings.mcp_server_timeout)
            await mcp_server.connect()
        except Exception as e:
            logger.warning(f"MCP server initialization failed: {e}. Continuing without MCP.")
        
        # Initialize knowledge base
        knowledge_base = KubernetesKnowledgeBase(
            vector_db_path=settings.vector_db_path,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize memory manager
        memory_manager = MemoryManager(
            database_url=settings.database_url,
            openai_api_key=settings.openai_api_key
        )
        
        # Shared LLM configuration
        llm_provider = settings.llm_provider
        llm_model = settings.llm_model
        llm_api_keys = {
            "nebius": settings.nebius_api_key,
            "openai": settings.openai_api_key,
            "anthropic": getattr(settings, "anthropic_api_key", None),
        }

        # Initialize agents
        troubleshooting_agent = TroubleshootingAgent(
            k8s_connector=k8s_connector,
            mcp_server=mcp_server,
            nebius_api_key=settings.nebius_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_keys=llm_api_keys,
        )
        
        monitoring_agent = MonitoringAgent(
            k8s_connector=k8s_connector,
            nebius_api_key=settings.nebius_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_keys=llm_api_keys,
        )
        
        automation_agent = AutomationAgent(
            k8s_connector=k8s_connector,
            nebius_api_key=settings.nebius_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_keys=llm_api_keys,
            mcp_server=mcp_server,
        )
        
        knowledge_agent = KnowledgeAgent(
            knowledge_base=knowledge_base,
            nebius_api_key=settings.nebius_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_keys=llm_api_keys,
        )
        
        coordinator_agent = CoordinatorAgent(
            troubleshooting_agent=troubleshooting_agent,
            monitoring_agent=monitoring_agent,
            automation_agent=automation_agent,
            knowledge_agent=knowledge_agent,
            nebius_api_key=settings.nebius_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_keys=llm_api_keys,
        )
        
        logger.info("SRE Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing SRE Bot: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    global mcp_server
    if mcp_server:
        await mcp_server.disconnect()


class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    namespace: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query response model."""
    response: str
    agent_used: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Agent SRE Bot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "platform": settings.platform,
        "components": {
            "k8s_connector": k8s_connector is not None,
            "mcp_server": mcp_server is not None,
            "knowledge_base": knowledge_base is not None,
            "memory_manager": memory_manager is not None,
            "coordinator_agent": coordinator_agent is not None,
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a query using the coordinator agent.
    
    Args:
        request: Query request
        
    Returns:
        Query response
    """
    if not coordinator_agent:
        raise HTTPException(status_code=503, detail="Coordinator agent not initialized")
    
    try:
        # Get context from memory if available
        context = request.context or {}
        if memory_manager:
            memory_context = memory_manager.get_context(request.query)
            if memory_context:
                context["memory"] = memory_context
        
        # Process query
        response = coordinator_agent.process_query(request.query, context)
        
        # Record conversation in memory
        if memory_manager:
            memory_manager.record_conversation(request.query, response)
        
        return QueryResponse(
            response=response,
            agent_used="coordinator"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster/info")
async def get_cluster_info():
    """Get cluster information."""
    if not k8s_connector:
        raise HTTPException(status_code=503, detail="Kubernetes connector not initialized")
    
    try:
        info = k8s_connector.get_cluster_info()
        return info
    except Exception as e:
        logger.error(f"Error getting cluster info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster/pods")
async def get_pods(namespace: str = "default"):
    """Get pod status for a namespace."""
    if not k8s_connector:
        raise HTTPException(status_code=503, detail="Kubernetes connector not initialized")
    
    try:
        pods = k8s_connector.get_pod_status(namespace)
        return pods
    except Exception as e:
        logger.error(f"Error getting pods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster/events")
async def get_events(namespace: str = "default", limit: int = 50):
    """Get recent events from a namespace."""
    if not k8s_connector:
        raise HTTPException(status_code=503, detail="Kubernetes connector not initialized")
    
    try:
        events = k8s_connector.get_events(namespace, limit)
        return events
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

