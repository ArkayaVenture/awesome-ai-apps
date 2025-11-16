"""Monitoring Agent for cluster health and SLO tracking."""
import os
from agno.agent import Agent
from agno.models.nebius import Nebius
from typing import Optional, Dict, Any
import logging
from ..connectors import KubernetesConnector

logger = logging.getLogger(__name__)


class MonitoringAgent:
    """Monitoring Agent for cluster health and performance monitoring."""
    
    def __init__(
        self,
        k8s_connector: KubernetesConnector,
        nebius_api_key: Optional[str] = None
    ):
        """Initialize Monitoring Agent.
        
        Args:
            k8s_connector: Kubernetes connector instance
            nebius_api_key: Nebius API key
        """
        self.k8s_connector = k8s_connector
        self.nebius_api_key = nebius_api_key or os.getenv("NEBIUS_API_KEY")
        
        monitoring_prompt = self._load_monitoring_prompt()
        
        self.agent = Agent(
            name="MonitoringAgent",
            role="Monitor Kubernetes cluster health, performance, and SLOs",
            model=Nebius(
                id="Qwen/Qwen3-32B",
                api_key=self.nebius_api_key
            ),
            instructions=[
                monitoring_prompt,
                "Provide current cluster status overview",
                "Highlight any anomalies or concerns",
                "Include relevant metrics and trends",
                "Compare against SLO targets",
                "Recommend actions if thresholds are exceeded",
            ],
            markdown=True,
        )
    
    def _load_monitoring_prompt(self) -> str:
        """Load monitoring agent prompt."""
        return """You are a Monitoring Agent responsible for Kubernetes cluster health, 
performance, and SLO tracking.

Your Responsibilities:
- Monitor cluster health and resource utilization
- Track SLOs and error budgets
- Analyze performance metrics
- Generate health reports
- Alert on anomalies and trends

Monitoring Focus Areas:
- Cluster Health: Node status, pod distribution, resource availability
- Application Health: Deployment status, replica counts, readiness
- Performance: CPU, memory, network, disk usage
- SLOs: Availability, latency, error rates
- Capacity: Resource requests/limits, scaling recommendations

Response Format:
- Provide current cluster status overview
- Highlight any anomalies or concerns
- Include relevant metrics and trends
- Compare against SLO targets
- Recommend actions if thresholds are exceeded"""
    
    def get_cluster_health(self) -> str:
        """Get cluster health report.
        
        Returns:
            Health report
        """
        try:
            cluster_info = self.k8s_connector.get_cluster_info()
            pod_statuses = self.k8s_connector.get_pod_status()
            
            context = f"""Cluster Information:
{cluster_info}

Pod Statuses:
{pod_statuses}"""
            
            prompt = f"""{context}

Please provide a comprehensive cluster health report including:
1. Overall cluster status
2. Node health
3. Pod distribution and status
4. Resource utilization
5. Any concerns or recommendations"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error getting cluster health: {e}")
            return f"Error: {str(e)}"
    
    def check_slo(self, slo_target: Dict[str, Any]) -> str:
        """Check SLO compliance.
        
        Args:
            slo_target: SLO target definition
            
        Returns:
            SLO compliance report
        """
        try:
            prompt = f"""Check SLO compliance for the following targets:
{slo_target}

Please analyze:
1. Current SLO metrics
2. Compliance status
3. Error budget remaining
4. Recommendations if targets are at risk"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error checking SLO: {e}")
            return f"Error: {str(e)}"

