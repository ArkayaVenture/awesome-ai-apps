"""Troubleshooting Agent for diagnosing Kubernetes issues."""
import os
from agno.agent import Agent
from agno.models.nebius import Nebius
from typing import Optional, Dict, Any
import logging
from ..mcp import KubernetesMCPServer
from ..connectors import KubernetesConnector

logger = logging.getLogger(__name__)


class TroubleshootingAgent:
    """Troubleshooting Agent for diagnosing and resolving Kubernetes issues."""
    
    def __init__(
        self,
        k8s_connector: KubernetesConnector,
        mcp_server: Optional[KubernetesMCPServer] = None,
        nebius_api_key: Optional[str] = None
    ):
        """Initialize Troubleshooting Agent.
        
        Args:
            k8s_connector: Kubernetes connector instance
            mcp_server: Optional MCP server instance
            nebius_api_key: Nebius API key
        """
        self.k8s_connector = k8s_connector
        self.mcp_server = mcp_server
        self.nebius_api_key = nebius_api_key or os.getenv("NEBIUS_API_KEY")
        
        troubleshooting_prompt = self._load_troubleshooting_prompt()
        
        # MCP tools will be added via the server if available
        # Note: MCP integration is handled at the coordinator level
        
        self.agent = Agent(
            name="TroubleshootingAgent",
            role="Diagnose and resolve Kubernetes cluster issues",
            model=Nebius(
                id="deepseek-ai/DeepSeek-V3-0324",
                api_key=self.nebius_api_key
            ),
            instructions=[
                troubleshooting_prompt,
                "Always gather information first: logs, events, metrics, resource states",
                "Analyze patterns and identify root causes",
                "Provide step-by-step remediation guidance",
                "Include verification steps",
            ],
            markdown=True,
        )
    
    def _load_troubleshooting_prompt(self) -> str:
        """Load troubleshooting agent prompt."""
        return """You are a Senior SRE Troubleshooting Agent specializing in Kubernetes cluster 
diagnostics and issue resolution.

Your Capabilities:
- Analyze pod logs, events, and metrics
- Diagnose deployment, networking, and resource issues
- Identify root causes of failures
- Provide step-by-step remediation guidance
- Use Kubernetes MCP tools to inspect cluster state

Troubleshooting Process:
1. Gather Information: Collect logs, events, metrics, and resource states
2. Analyze: Identify patterns, errors, and anomalies
3. Diagnose: Determine root cause using Kubernetes knowledge
4. Recommend: Provide specific remediation steps
5. Verify: Suggest verification steps to confirm resolution

Best Practices:
- Always check pod status, events, and logs first
- Verify resource quotas and limits
- Check network policies and service endpoints
- Review recent changes (deployments, configmaps, secrets)
- Consider dependencies between resources
- Provide rollback options when appropriate

Response Format:
- Start with a summary of the issue
- List relevant findings (logs, events, metrics)
- Provide root cause analysis
- Give step-by-step remediation steps
- Include verification commands"""
    
    def diagnose(self, issue_description: str, namespace: str = "default") -> str:
        """Diagnose a Kubernetes issue.
        
        Args:
            issue_description: Description of the issue
            namespace: Kubernetes namespace
            
        Returns:
            Diagnosis and recommendations
        """
        try:
            # Gather information
            pod_statuses = self.k8s_connector.get_pod_status(namespace)
            events = self.k8s_connector.get_events(namespace)
            
            # Build context
            context = f"""Current Pod Status in namespace '{namespace}':
{pod_statuses}

Recent Events:
{events[:10]}  # Last 10 events

Issue Description: {issue_description}"""
            
            prompt = f"""{context}

Please diagnose this issue and provide:
1. Summary of the issue
2. Root cause analysis
3. Step-by-step remediation steps
4. Verification commands"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error in troubleshooting agent: {e}")
            return f"Error: {str(e)}"
    
    def analyze_logs(self, pod_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
        """Analyze pod logs.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            tail_lines: Number of log lines to retrieve
            
        Returns:
            Log analysis
        """
        try:
            logs = self.k8s_connector.get_pod_logs(pod_name, namespace, tail_lines)
            
            prompt = f"""Analyze these pod logs for errors, warnings, or issues:

Pod: {pod_name}
Namespace: {namespace}

Logs:
{logs}

Please identify:
1. Any errors or warnings
2. Patterns or anomalies
3. Potential root causes
4. Recommended actions"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return f"Error: {str(e)}"

