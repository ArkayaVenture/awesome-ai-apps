"""Kubernetes connector for local and standard Kubernetes clusters."""
import os
from typing import Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logger = logging.getLogger(__name__)


class KubernetesConnector:
    """Connector for standard Kubernetes clusters."""
    
    def __init__(self, kubeconfig: Optional[str] = None):
        """Initialize Kubernetes connector.
        
        Args:
            kubeconfig: Path to kubeconfig file. If None, uses default kubeconfig.
        """
        self.kubeconfig = kubeconfig or os.getenv("KUBECONFIG")
        self.api_client = None
        self.core_v1 = None
        self.apps_v1 = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Kubernetes cluster."""
        try:
            if self.kubeconfig:
                config.load_kube_config(config_file=self.kubeconfig)
            else:
                config.load_incluster_config()
            
            self.api_client = client.ApiClient()
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Connected to Kubernetes cluster")
        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes: {e}")
            raise
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        try:
            nodes = self.core_v1.list_node()
            namespaces = self.core_v1.list_namespace()
            
            return {
                "node_count": len(nodes.items),
                "namespace_count": len(namespaces.items),
                "kubernetes_version": nodes.items[0].status.node_info.kubelet_version if nodes.items else "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"error": str(e)}
    
    def get_pod_status(self, namespace: str = "default") -> Dict[str, Any]:
        """Get pod status for a namespace."""
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            pod_statuses = {}
            
            for pod in pods.items:
                pod_statuses[pod.metadata.name] = {
                    "status": pod.status.phase,
                    "ready": pod.status.container_statuses[0].ready if pod.status.container_statuses else False,
                    "restarts": sum(container.restart_count for container in pod.status.container_statuses or []),
                }
            
            return pod_statuses
        except ApiException as e:
            logger.error(f"Error getting pod status: {e}")
            return {"error": str(e)}
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
        """Get logs from a pod."""
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
            return logs
        except ApiException as e:
            logger.error(f"Error getting pod logs: {e}")
            return f"Error: {str(e)}"
    
    def get_events(self, namespace: str = "default", limit: int = 50) -> list:
        """Get recent events from a namespace."""
        try:
            events = self.core_v1.list_namespaced_event(
                namespace=namespace,
                limit=limit
            )
            return [
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                }
                for event in events.items
            ]
        except ApiException as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def list_chaos_scenarios(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """List all chaos scenarios in the cluster.
        
        Args:
            namespace: Optional namespace to filter. If None, searches all namespaces.
            
        Returns:
            Dictionary with chaos scenarios information
        """
        try:
            chaos_info = {
                "chaos_pods": [],
                "chaos_jobs": [],
                "chaos_deployments": [],
                "namespaces": []
            }
            
            # Get all pods with chaos label
            if namespace:
                pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector="chaos=true")
            else:
                pods = self.core_v1.list_pod_for_all_namespaces(label_selector="chaos=true")
            
            for pod in pods.items:
                chaos_info["chaos_pods"].append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "labels": pod.metadata.labels or {}
                })
                if pod.metadata.namespace not in chaos_info["namespaces"]:
                    chaos_info["namespaces"].append(pod.metadata.namespace)
            
            # Get chaos jobs
            batch_v1 = client.BatchV1Api()
            if namespace:
                jobs = batch_v1.list_namespaced_job(namespace=namespace, label_selector="chaos=true")
            else:
                jobs = batch_v1.list_job_for_all_namespaces(label_selector="chaos=true")
            
            for job in jobs.items:
                chaos_info["chaos_jobs"].append({
                    "name": job.metadata.name,
                    "namespace": job.metadata.namespace,
                    "active": job.status.active or 0,
                    "succeeded": job.status.succeeded or 0,
                    "failed": job.status.failed or 0
                })
            
            # Get chaos deployments
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace, label_selector="chaos=true")
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces(label_selector="chaos=true")
            
            for deployment in deployments.items:
                chaos_info["chaos_deployments"].append({
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": deployment.spec.replicas or 0,
                    "ready": deployment.status.ready_replicas or 0
                })
            
            return chaos_info
            
        except ApiException as e:
            logger.error(f"Error listing chaos scenarios: {e}")
            return {"error": str(e)}
    
    def remove_chaos_scenarios(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Remove all chaos scenarios from the cluster.
        
        Args:
            namespace: Optional namespace to filter. If None, removes from all namespaces.
            
        Returns:
            Dictionary with removal results
        """
        results = {
            "pods_deleted": [],
            "jobs_deleted": [],
            "deployments_deleted": [],
            "errors": []
        }
        
        try:
            # Delete chaos pods
            if namespace:
                pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector="chaos=true")
            else:
                pods = self.core_v1.list_pod_for_all_namespaces(label_selector="chaos=true")
            
            for pod in pods.items:
                try:
                    self.core_v1.delete_namespaced_pod(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace,
                        grace_period_seconds=0
                    )
                    results["pods_deleted"].append(f"{pod.metadata.namespace}/{pod.metadata.name}")
                except ApiException as e:
                    results["errors"].append(f"Failed to delete pod {pod.metadata.name}: {str(e)}")
            
            # Delete chaos jobs
            batch_v1 = client.BatchV1Api()
            if namespace:
                jobs = batch_v1.list_namespaced_job(namespace=namespace, label_selector="chaos=true")
            else:
                jobs = batch_v1.list_job_for_all_namespaces(label_selector="chaos=true")
            
            for job in jobs.items:
                try:
                    batch_v1.delete_namespaced_job(
                        name=job.metadata.name,
                        namespace=job.metadata.namespace,
                        propagation_policy="Foreground"
                    )
                    results["jobs_deleted"].append(f"{job.metadata.namespace}/{job.metadata.name}")
                except ApiException as e:
                    results["errors"].append(f"Failed to delete job {job.metadata.name}: {str(e)}")
            
            # Delete chaos deployments
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace, label_selector="chaos=true")
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces(label_selector="chaos=true")
            
            for deployment in deployments.items:
                try:
                    self.apps_v1.delete_namespaced_deployment(
                        name=deployment.metadata.name,
                        namespace=deployment.metadata.namespace,
                        propagation_policy="Foreground"
                    )
                    results["deployments_deleted"].append(f"{deployment.metadata.namespace}/{deployment.metadata.name}")
                except ApiException as e:
                    results["errors"].append(f"Failed to delete deployment {deployment.metadata.name}: {str(e)}")
            
            return results
            
        except ApiException as e:
            logger.error(f"Error removing chaos scenarios: {e}")
            results["errors"].append(f"Error: {str(e)}")
            return results
    
    def delete_resource(self, resource_type: str, name: str, namespace: str = "default") -> Dict[str, Any]:
        """Delete a Kubernetes resource.
        
        Args:
            resource_type: Type of resource (pod, deployment, job, etc.)
            name: Name of the resource
            namespace: Namespace of the resource
            
        Returns:
            Dictionary with deletion result
        """
        try:
            if resource_type.lower() == "pod":
                self.core_v1.delete_namespaced_pod(name=name, namespace=namespace, grace_period_seconds=0)
            elif resource_type.lower() == "deployment":
                self.apps_v1.delete_namespaced_deployment(name=name, namespace=namespace, propagation_policy="Foreground")
            elif resource_type.lower() == "job":
                batch_v1 = client.BatchV1Api()
                batch_v1.delete_namespaced_job(name=name, namespace=namespace, propagation_policy="Foreground")
            else:
                return {"error": f"Unsupported resource type: {resource_type}"}
            
            return {"success": True, "resource": f"{resource_type}/{name}", "namespace": namespace}
            
        except ApiException as e:
            logger.error(f"Error deleting {resource_type} {name}: {e}")
            return {"error": str(e), "success": False}

