"""GCP GKE connector."""
from google.cloud import container_v1
from google.oauth2 import service_account
from typing import Optional, Dict, Any
import logging
import os
from .kubernetes import KubernetesConnector

logger = logging.getLogger(__name__)


class GCPGKEConnector(KubernetesConnector):
    """Connector for GCP GKE clusters."""
    
    def __init__(
        self,
        project_id: str,
        zone: str,
        cluster_name: str,
        credentials_path: Optional[str] = None
    ):
        """Initialize GCP GKE connector.
        
        Args:
            project_id: GCP project ID
            zone: GCP zone
            cluster_name: GKE cluster name
            credentials_path: Path to service account JSON file
        """
        self.project_id = project_id
        self.zone = zone
        self.cluster_name = cluster_name
        
        # Initialize GCP credentials
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        else:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
            else:
                # Use default credentials
                from google.auth import default
                credentials, _ = default()
        
        self.gke_client = container_v1.ClusterManagerClient(credentials=credentials)
        
        self._update_kubeconfig()
        
        # Initialize parent Kubernetes connector
        super().__init__()
    
    def _update_kubeconfig(self):
        """Update kubeconfig with GKE cluster credentials."""
        try:
            import subprocess
            cmd = [
                "gcloud", "container", "clusters", "get-credentials",
                self.cluster_name,
                "--zone", self.zone,
                "--project", self.project_id
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Updated kubeconfig for GKE cluster: {self.cluster_name}")
        except Exception as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            raise
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get GKE cluster information."""
        try:
            cluster_path = f"projects/{self.project_id}/locations/{self.zone}/clusters/{self.cluster_name}"
            cluster = self.gke_client.get_cluster(name=cluster_path)
            
            base_info = super().get_cluster_info()
            base_info.update({
                "platform": "gcp-gke",
                "cluster_name": cluster.name,
                "kubernetes_version": cluster.current_master_version,
                "status": cluster.status.name,
                "endpoint": cluster.endpoint,
                "location": cluster.location,
            })
            
            return base_info
        except Exception as e:
            logger.error(f"Error getting GKE cluster info: {e}")
            return {"error": str(e)}

