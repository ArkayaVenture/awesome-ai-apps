"""AWS EKS connector."""
import boto3
from typing import Optional, Dict, Any
import logging
from .kubernetes import KubernetesConnector

logger = logging.getLogger(__name__)


class AWSEKSConnector(KubernetesConnector):
    """Connector for AWS EKS clusters."""
    
    def __init__(
        self,
        cluster_name: str,
        region: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """Initialize AWS EKS connector.
        
        Args:
            cluster_name: Name of the EKS cluster
            region: AWS region
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
        """
        self.cluster_name = cluster_name
        self.region = region
        
        # Initialize AWS session
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        self.eks_client = session.client('eks')
        self._update_kubeconfig()
        
        # Initialize parent Kubernetes connector
        super().__init__()
    
    def _update_kubeconfig(self):
        """Update kubeconfig with EKS cluster credentials."""
        try:
            import subprocess
            cmd = [
                "aws", "eks", "update-kubeconfig",
                "--name", self.cluster_name,
                "--region", self.region
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Updated kubeconfig for EKS cluster: {self.cluster_name}")
        except Exception as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            raise
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get EKS cluster information."""
        try:
            response = self.eks_client.describe_cluster(name=self.cluster_name)
            cluster = response['cluster']
            
            base_info = super().get_cluster_info()
            base_info.update({
                "platform": "aws-eks",
                "cluster_name": cluster['name'],
                "eks_version": cluster['version'],
                "status": cluster['status'],
                "endpoint": cluster['endpoint'],
                "role_arn": cluster.get('roleArn', ''),
            })
            
            return base_info
        except Exception as e:
            logger.error(f"Error getting EKS cluster info: {e}")
            return {"error": str(e)}

