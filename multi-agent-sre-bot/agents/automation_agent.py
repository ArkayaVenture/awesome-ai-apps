"""Automation Agent for executing runbooks and automated actions."""
import os
from agno.agent import Agent
from agno.models.nebius import Nebius
from typing import Optional, Dict, Any
import logging
from ..connectors import KubernetesConnector

logger = logging.getLogger(__name__)


class AutomationAgent:
    """Automation Agent for executing runbooks and automated remediation."""
    
    def __init__(
        self,
        k8s_connector: KubernetesConnector,
        nebius_api_key: Optional[str] = None
    ):
        """Initialize Automation Agent.
        
        Args:
            k8s_connector: Kubernetes connector instance
            nebius_api_key: Nebius API key
        """
        self.k8s_connector = k8s_connector
        self.nebius_api_key = nebius_api_key or os.getenv("NEBIUS_API_KEY")
        
        automation_prompt = self._load_automation_prompt()
        
        self.agent = Agent(
            name="AutomationAgent",
            role="Execute runbooks and automated remediation actions",
            model=Nebius(
                id="meta-llama/Meta-Llama-3.1-70B-Instruct",
                api_key=self.nebius_api_key
            ),
            instructions=[
                automation_prompt,
                "ALWAYS request approval for destructive operations",
                "Only perform operations in the bot namespace by default",
                "Log all actions for audit purposes",
                "Verify prerequisites before execution",
                "Provide rollback procedures",
            ],
            markdown=True,
        )
    
    def _load_automation_prompt(self) -> str:
        """Load automation agent prompt."""
        return """You are an Automation Agent that executes runbooks and automated remediation 
actions in Kubernetes clusters.

Your Capabilities:
- Execute approved runbooks
- Perform automated remediation
- Manage deployments and rollbacks
- Scale resources
- Update configurations

Safety Guidelines:
- ALWAYS request approval for destructive operations
- Only perform operations in the bot namespace by default
- Log all actions for audit purposes
- Verify prerequisites before execution
- Provide rollback procedures

Automation Types:
- Deployments: Rolling updates, blue-green, canary
- Scaling: Horizontal and vertical pod autoscaling
- Remediation: Restart pods, update configs, rollback deployments
- Maintenance: Drain nodes, update addons, rotate secrets

Response Format:
- Describe the action to be taken
- List prerequisites and checks
- Request approval if needed
- Execute and report results
- Provide verification steps"""
    
    def execute_runbook(self, runbook_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a runbook.
        
        Args:
            runbook_name: Name of the runbook
            parameters: Runbook parameters
            
        Returns:
            Execution result
        """
        try:
            prompt = f"""Execute the following runbook:

Runbook: {runbook_name}
Parameters: {parameters}

Please:
1. Describe the action to be taken
2. List prerequisites and checks
3. Request approval if this is a destructive operation
4. Execute the runbook
5. Report results
6. Provide verification steps"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error executing runbook: {e}")
            return f"Error: {str(e)}"
    
    def rollback_deployment(self, deployment_name: str, namespace: str = "default") -> str:
        """Rollback a deployment.
        
        Args:
            deployment_name: Name of the deployment
            namespace: Kubernetes namespace
            
        Returns:
            Rollback result
        """
        try:
            prompt = f"""Rollback deployment:

Deployment: {deployment_name}
Namespace: {namespace}

Please:
1. Check current deployment status
2. Identify the previous revision
3. Request approval for rollback
4. Execute rollback
5. Verify rollback success"""
            
            response = self.agent.run(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error rolling back deployment: {e}")
            return f"Error: {str(e)}"
    
    def detect_chaos_scenarios(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Detect chaos scenarios in the cluster.
        
        Args:
            namespace: Optional namespace to check. If None, checks all namespaces.
            
        Returns:
            Dictionary with detected chaos scenarios
        """
        try:
            chaos_info = self.k8s_connector.list_chaos_scenarios(namespace=namespace)
            return chaos_info
        except Exception as e:
            logger.error(f"Error detecting chaos scenarios: {e}")
            return {"error": str(e)}
    
    def fix_chaos_scenarios(self, namespace: Optional[str] = None, action: str = "remove") -> Dict[str, Any]:
        """Fix/remove chaos scenarios from the cluster.
        
        Args:
            namespace: Optional namespace to fix. If None, fixes all namespaces.
            action: Action to take (remove, stop, disable)
            
        Returns:
            Dictionary with action results and summary
        """
        try:
            # First detect what chaos scenarios exist
            chaos_info = self.detect_chaos_scenarios(namespace=namespace)
            
            if "error" in chaos_info:
                return chaos_info
            
            # Remove chaos scenarios
            removal_results = self.k8s_connector.remove_chaos_scenarios(namespace=namespace)
            
            # Generate summary
            summary = {
                "action": action,
                "namespace": namespace or "all namespaces",
                "chaos_detected": {
                    "pods": len(chaos_info.get("chaos_pods", [])),
                    "jobs": len(chaos_info.get("chaos_jobs", [])),
                    "deployments": len(chaos_info.get("chaos_deployments", []))
                },
                "removed": {
                    "pods": len(removal_results.get("pods_deleted", [])),
                    "jobs": len(removal_results.get("jobs_deleted", [])),
                    "deployments": len(removal_results.get("deployments_deleted", []))
                },
                "details": removal_results,
                "status": "success" if not removal_results.get("errors") else "partial"
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error fixing chaos scenarios: {e}")
            return {"error": str(e), "status": "failed"}
    
    def execute_cluster_operation(self, operation: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a cluster operation based on natural language command.
        
        Args:
            operation: Natural language description of the operation
            parameters: Optional parameters for the operation
            
        Returns:
            Dictionary with operation results and summary
        """
        try:
            operation_lower = operation.lower()
            parameters = parameters or {}
            
            # Parse operation to determine action
            if any(kw in operation_lower for kw in ["fix", "remove", "stop", "delete", "clean"]):
                if "chaos" in operation_lower:
                    # Extract namespace if mentioned
                    namespace = parameters.get("namespace")
                    if not namespace:
                        # Try to extract from operation text
                        if "namespace" in operation_lower:
                            # Simple extraction - could be improved with NLP
                            parts = operation_lower.split("namespace")
                            if len(parts) > 1:
                                namespace_part = parts[1].strip().split()[0]
                                namespace = namespace_part if namespace_part else None
                    
                    result = self.fix_chaos_scenarios(namespace=namespace, action="remove")
                    
                    # Generate human-readable summary
                    summary_text = self._generate_action_summary(operation, result)
                    result["summary"] = summary_text
                    
                    return result
                elif "deployment" in operation_lower and "rollback" in operation_lower:
                    # Extract deployment name and namespace
                    deployment_name = parameters.get("deployment_name", "unknown")
                    namespace = parameters.get("namespace", "default")
                    
                    rollback_result = self.rollback_deployment(deployment_name, namespace)
                    return {
                        "operation": "rollback_deployment",
                        "deployment": deployment_name,
                        "namespace": namespace,
                        "result": rollback_result,
                        "summary": f"Rolled back deployment {deployment_name} in namespace {namespace}"
                    }
            
            # Default: use AI agent to interpret and execute
            prompt = f"""Execute the following cluster operation:

Operation: {operation}
Parameters: {parameters}

Please:
1. Understand what operation is being requested
2. Check prerequisites and current cluster state
3. Execute the operation safely
4. Verify the operation completed successfully
5. Provide a detailed summary of what was done"""
            
            response = self.agent.run(prompt)
            result_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            return {
                "operation": operation,
                "result": result_text,
                "summary": self._extract_summary(result_text)
            }
            
        except Exception as e:
            logger.error(f"Error executing cluster operation: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _generate_action_summary(self, operation: str, result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of an action.
        
        Args:
            operation: Original operation description
            result: Result dictionary from the operation
            
        Returns:
            Formatted summary string
        """
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        summary_parts = []
        summary_parts.append(f"✅ **Action Completed: {operation}**\n")
        
        if "chaos_detected" in result:
            detected = result["chaos_detected"]
            removed = result.get("removed", {})
            
            summary_parts.append(f"**Chaos Scenarios Detected:**")
            summary_parts.append(f"- Pods: {detected.get('pods', 0)}")
            summary_parts.append(f"- Jobs: {detected.get('jobs', 0)}")
            summary_parts.append(f"- Deployments: {detected.get('deployments', 0)}")
            summary_parts.append(f"\n**Removed:**")
            summary_parts.append(f"- Pods: {removed.get('pods', 0)}")
            summary_parts.append(f"- Jobs: {removed.get('jobs', 0)}")
            summary_parts.append(f"- Deployments: {removed.get('deployments', 0)}")
            
            if result.get("namespace"):
                summary_parts.append(f"\n**Namespace:** {result['namespace']}")
        
        if result.get("details"):
            details = result["details"]
            if details.get("pods_deleted"):
                summary_parts.append(f"\n**Deleted Pods:**")
                for pod in details["pods_deleted"][:5]:  # Show first 5
                    summary_parts.append(f"- {pod}")
                if len(details["pods_deleted"]) > 5:
                    summary_parts.append(f"- ... and {len(details['pods_deleted']) - 5} more")
            
            if details.get("errors"):
                summary_parts.append(f"\n⚠️ **Errors:** {len(details['errors'])}")
                for error in details["errors"][:3]:
                    summary_parts.append(f"- {error}")
        
        summary_parts.append(f"\n**Status:** {result.get('status', 'unknown')}")
        
        return "\n".join(summary_parts)
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from AI response text.
        
        Args:
            text: Full response text
            
        Returns:
            Extracted summary
        """
        # Try to find summary section
        if "summary" in text.lower():
            parts = text.lower().split("summary")
            if len(parts) > 1:
                return parts[1].strip()
        
        # Return first 200 characters as summary
        return text[:200] + "..." if len(text) > 200 else text

