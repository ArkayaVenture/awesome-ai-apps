"""Coordinator Agent for orchestrating multi-agent workflows."""
import os
from agno.agent import Agent
from agno.models.nebius import Nebius
from typing import Optional, List
import logging
from .troubleshooting_agent import TroubleshootingAgent
from .monitoring_agent import MonitoringAgent
from .automation_agent import AutomationAgent
from .knowledge_agent import KnowledgeAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Coordinator Agent that routes queries to specialized agents."""
    
    def __init__(
        self,
        troubleshooting_agent: TroubleshootingAgent,
        monitoring_agent: MonitoringAgent,
        automation_agent: AutomationAgent,
        knowledge_agent: KnowledgeAgent,
        nebius_api_key: Optional[str] = None
    ):
        """Initialize Coordinator Agent.
        
        Args:
            troubleshooting_agent: Troubleshooting agent instance
            monitoring_agent: Monitoring agent instance
            automation_agent: Automation agent instance
            knowledge_agent: Knowledge agent instance
            nebius_api_key: Nebius API key
        """
        self.troubleshooting_agent = troubleshooting_agent
        self.monitoring_agent = monitoring_agent
        self.automation_agent = automation_agent
        self.knowledge_agent = knowledge_agent
        self.nebius_api_key = nebius_api_key or os.getenv("NEBIUS_API_KEY")
        
        coordinator_prompt = self._load_coordinator_prompt()
        
        self.agent = Agent(
            name="CoordinatorAgent",
            role="Coordinate multi-agent SRE bot workflows",
            model=Nebius(
                id="meta-llama/Meta-Llama-3.3-70B-Instruct",
                api_key=self.nebius_api_key
            ),
            instructions=[
                coordinator_prompt,
                "Always provide context about which agent(s) are handling the request",
                "If multiple agents are needed, coordinate their responses",
                "Ensure responses are clear, technical, and actionable",
                "Reference specific Kubernetes resources when relevant",
                "You have access to the following specialized agents:",
                "- TroubleshootingAgent: For diagnosing issues, errors, and failures",
                "- MonitoringAgent: For health checks, metrics, and SLO monitoring",
                "- AutomationAgent: For runbook execution and automated actions",
                "- KnowledgeAgent: For Kubernetes documentation and best practices",
            ],
            markdown=True,
        )
    
    def _load_coordinator_prompt(self) -> str:
        """Load coordinator agent prompt."""
        return """You are the Coordinator Agent for a multi-agent SRE bot system. Your role is to:

1. Analyze incoming user queries and determine which specialized agent(s) should handle the request
2. Route requests to appropriate agents (Troubleshooting, Monitoring, Automation, or Knowledge agents)
3. Synthesize responses from multiple agents when needed
4. Maintain context across the conversation
5. Provide clear, actionable guidance to users

Agent Routing Rules:
- Troubleshooting Agent: Use for issues, errors, failures, debugging, log analysis, pod crashes, network problems
- Monitoring Agent: Use for health checks, metrics queries, SLO monitoring, performance analysis, resource usage
- Automation Agent: Use for runbook execution, deployments, rollbacks, scaling operations, automated remediation
- Knowledge Agent: Use for questions about Kubernetes concepts, best practices, documentation, how-to guides

Response Guidelines:
- Always provide context about which agent(s) are handling the request
- If multiple agents are needed, coordinate their responses
- Ensure responses are clear, technical, and actionable
- Reference specific Kubernetes resources when relevant
- Include relevant metrics, logs, or events when available"""
    
    def process_query(self, query: str, context: Optional[dict] = None) -> str:
        """Process a user query and route to appropriate agent(s).
        
        Args:
            query: User's query
            context: Optional context dictionary
            
        Returns:
            Coordinated response from agents
        """
        try:
            # Determine which agent(s) to use
            agents_to_use = self._determine_agents(query)
            
            # Check for cluster operation commands (fix, remove, delete, etc.)
            query_lower = query.lower()
            is_cluster_operation = any(kw in query_lower for kw in [
                "fix", "remove", "delete", "stop", "clean", "rollback", 
                "scale", "deploy", "update", "restart"
            ])
            
            # Route to appropriate agent(s)
            if is_cluster_operation and "automation" in agents_to_use:
                # Use automation agent for cluster operations
                result = self.automation_agent.execute_cluster_operation(query, context or {})
                
                # Format response with summary
                if isinstance(result, dict):
                    if "summary" in result:
                        return result["summary"]
                    elif "result" in result:
                        return result["result"]
                    else:
                        return f"✅ Operation completed: {query}\n\n{str(result)}"
                else:
                    return str(result)
            elif "troubleshooting" in agents_to_use:
                response = self.troubleshooting_agent.diagnose(query)
            elif "monitoring" in agents_to_use:
                response = self.monitoring_agent.get_cluster_health()
            elif "automation" in agents_to_use:
                # For non-operation automation requests, use runbook execution
                response = self.automation_agent.execute_runbook("default", {})
            elif "knowledge" in agents_to_use:
                response = self.knowledge_agent.query(query)
            else:
                # Use coordinator agent to handle
                response = self.agent.run(query)
                response = str(response.content) if hasattr(response, 'content') else str(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in coordinator agent: {e}")
            return f"Error: {str(e)}"
    
    def _determine_agents(self, query: str) -> List[str]:
        """Determine which agents should handle the query.
        
        Args:
            query: User's query
            
        Returns:
            List of agent names to use
        """
        query_lower = query.lower()
        agents = []
        
        # Troubleshooting keywords
        if any(kw in query_lower for kw in ["error", "fail", "crash", "issue", "problem", "debug", "log", "troubleshoot"]):
            agents.append("troubleshooting")
        
        # Monitoring keywords
        if any(kw in query_lower for kw in ["health", "status", "metric", "slo", "performance", "monitor", "check"]):
            agents.append("monitoring")
        
        # Automation keywords (including chaos and fix operations)
        if any(kw in query_lower for kw in [
            "deploy", "rollback", "scale", "runbook", "automate", "execute",
            "fix", "remove", "delete", "stop", "clean", "chaos", "restart"
        ]):
            agents.append("automation")
        
        # Knowledge keywords
        if any(kw in query_lower for kw in ["what", "how", "explain", "documentation", "best practice", "guide"]):
            agents.append("knowledge")
        
        # Default to knowledge if no specific agent identified
        if not agents:
            agents.append("knowledge")
        
        return agents

