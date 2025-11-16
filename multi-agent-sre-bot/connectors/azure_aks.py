"""Azure AKS connector."""
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.containerservice import ContainerServiceClient
from typing import Optional, Dict, Any
import logging
from .kubernetes import KubernetesConnector

logger = logging.getLogger(__name__)


class AzureAKSConnector(KubernetesConnector):
    """Connector for Azure AKS clusters."""
    
    def __init__(
        self,
        subscription_id: str,
        resource_group: str,
        cluster_name: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        """Initialize Azure AKS connector.
        
        Args:
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            cluster_name: AKS cluster name
            client_id: Azure client ID (optional, uses DefaultAzureCredential if not provided)
            client_secret: Azure client secret
            tenant_id: Azure tenant ID
        """
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        
        # Initialize Azure credentials
        if client_id and client_secret and tenant_id:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            self.credential = DefaultAzureCredential()
        
        self.aks_client = ContainerServiceClient(
            self.credential,
            subscription_id
        )
        
        self._update_kubeconfig()
        
        # Initialize parent Kubernetes connector
        super().__init__()
    
    def _update_kubeconfig(self):
        """Update kubeconfig with AKS cluster credentials."""
        try:
            import subprocess
            cmd = [
                "az", "aks", "get-credentials",
                "--resource-group", self.resource_group,
                "--name", self.cluster_name,
                "--overwrite-existing"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Updated kubeconfig for AKS cluster: {self.cluster_name}")
        except Exception as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            raise
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get AKS cluster information."""
        try:
            cluster = self.aks_client.managed_clusters.get(
                self.resource_group,
                self.cluster_name
            )
            
            base_info = super().get_cluster_info()
            base_info.update({
                "platform": "azure-aks",
                "cluster_name": cluster.name,
                "kubernetes_version": cluster.kubernetes_version,
                "provisioning_state": cluster.provisioning_state,
                "fqdn": cluster.fqdn,
                "node_resource_group": cluster.node_resource_group,
            })
            
            return base_info
        except Exception as e:
            logger.error(f"Error getting AKS cluster info: {e}")
            return {"error": str(e)}

