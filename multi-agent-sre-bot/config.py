"""Configuration management for SRE Bot."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # AI API Keys (optional for daemon mode monitoring)
    nebius_api_key: Optional[str] = Field(None, env="NEBIUS_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    llm_provider: Optional[str] = Field(None, env="LLM_PROVIDER")
    llm_model: Optional[str] = Field(None, env="LLM_MODEL")
    
    # Kubernetes Configuration
    kubeconfig: Optional[str] = Field(None, env="KUBECONFIG")
    
    # AWS EKS Configuration
    aws_region: Optional[str] = Field(None, env="AWS_REGION")
    aws_eks_cluster_name: Optional[str] = Field(None, env="AWS_EKS_CLUSTER_NAME")
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    
    # Azure AKS Configuration
    azure_subscription_id: Optional[str] = Field(None, env="AZURE_SUBSCRIPTION_ID")
    azure_resource_group: Optional[str] = Field(None, env="AZURE_RESOURCE_GROUP")
    azure_aks_cluster_name: Optional[str] = Field(None, env="AZURE_AKS_CLUSTER_NAME")
    azure_client_id: Optional[str] = Field(None, env="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(None, env="AZURE_CLIENT_SECRET")
    azure_tenant_id: Optional[str] = Field(None, env="AZURE_TENANT_ID")
    
    # GCP GKE Configuration
    gcp_project_id: Optional[str] = Field(None, env="GCP_PROJECT_ID")
    gcp_zone: Optional[str] = Field(None, env="GCP_ZONE")
    gcp_gke_cluster_name: Optional[str] = Field(None, env="GCP_GKE_CLUSTER_NAME")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Database and Storage
    database_url: str = Field("sqlite:///sre_bot_memory.db", env="DATABASE_URL")
    vector_db_path: str = Field("./data/vector_store", env="VECTOR_DB_PATH")
    
    # Observability
    phoenix_api_key: Optional[str] = Field(None, env="ARIZE_PHOENIX_API_KEY")
    phoenix_collector_endpoint: Optional[str] = Field(None, env="PHOENIX_COLLECTOR_ENDPOINT")
    
    # MCP Configuration
    mcp_server_timeout: int = Field(300, env="MCP_SERVER_TIMEOUT")
    
    # Platform Selection
    platform: str = Field("local", env="K8S_PLATFORM")  # local, aws, azure, gcp
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

