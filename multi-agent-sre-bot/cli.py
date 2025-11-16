#!/usr/bin/env python3
"""CLI interface for SRE Bot."""
import asyncio
import sys
import os
from typing import Optional
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from connectors import (
    KubernetesConnector,
    AWSEKSConnector,
    AzureAKSConnector,
    GCPGKEConnector
)
from mcp import KubernetesMCPServer
from rag import KubernetesKnowledgeBase
from memory import MemoryManager
from agents import (
    CoordinatorAgent,
    TroubleshootingAgent,
    MonitoringAgent,
    AutomationAgent,
    KnowledgeAgent
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_bot():
    """Initialize SRE bot components."""
    # Initialize Kubernetes connector
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
    
    # Initialize agents
    troubleshooting_agent = TroubleshootingAgent(
        k8s_connector=k8s_connector,
        mcp_server=mcp_server,
        nebius_api_key=settings.nebius_api_key
    )
    
    monitoring_agent = MonitoringAgent(
        k8s_connector=k8s_connector,
        nebius_api_key=settings.nebius_api_key
    )
    
    automation_agent = AutomationAgent(
        k8s_connector=k8s_connector,
        nebius_api_key=settings.nebius_api_key
    )
    
    knowledge_agent = KnowledgeAgent(
        knowledge_base=knowledge_base,
        nebius_api_key=settings.nebius_api_key
    )
    
    coordinator_agent = CoordinatorAgent(
        troubleshooting_agent=troubleshooting_agent,
        monitoring_agent=monitoring_agent,
        automation_agent=automation_agent,
        knowledge_agent=knowledge_agent,
        nebius_api_key=settings.nebius_api_key
    )
    
    return coordinator_agent, memory_manager, mcp_server


async def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python cli.py <query>")
        print("Example: python cli.py 'Check the health of my cluster'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        print(f"🤖 Initializing SRE Bot...")
        coordinator_agent, memory_manager, mcp_server = await initialize_bot()
        
        print(f"\n📝 Processing query: {query}\n")
        
        # Get context from memory
        context = {}
        if memory_manager:
            memory_context = memory_manager.get_context(query)
            if memory_context:
                context["memory"] = memory_context
        
        # Process query
        response = coordinator_agent.process_query(query, context)
        
        # Record conversation
        if memory_manager:
            memory_manager.record_conversation(query, response)
        
        print("\n" + "="*80)
        print("RESPONSE:")
        print("="*80)
        print(response)
        print("="*80 + "\n")
        
        # Cleanup
        if mcp_server:
            await mcp_server.disconnect()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

