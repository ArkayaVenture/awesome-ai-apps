# Multi-Agent SRE Bot for Kubernetes

A comprehensive, production-ready multi-agent SRE bot designed for Kubernetes cluster management, troubleshooting, and automation. This bot integrates with Kubernetes v1.32+ clusters across multiple cloud platforms and leverages official MCP servers for seamless Kubernetes operations.

## 🏗️ Architecture

The SRE bot uses a multi-agent architecture with specialized agents for different SRE tasks:

- **Coordinator Agent**: Orchestrates tasks and routes requests to appropriate specialized agents
- **Troubleshooting Agent**: Diagnoses issues, analyzes logs, metrics, and traces
- **Monitoring Agent**: Monitors cluster health, SLOs, and performance metrics
- **Automation Agent**: Executes runbooks and automated remediation actions
- **Knowledge Agent**: Provides answers from Kubernetes knowledge base using RAG

## ✨ Features

- **Multi-Cloud Support**: Works with local Kubernetes, AWS EKS, Azure AKS, and GCP GKE
- **MCP Integration**: Official Kubernetes MCP server integration for native k8s operations
- **RAG Knowledge Base**: Comprehensive Kubernetes documentation and best practices
- **Memory System**: Context retention across conversations using Memori
- **Multi-Agent System**: Specialized agents for different SRE tasks
- **Multiple Interfaces**: API (FastAPI), CLI, and Streamlit ChatOps UI
- **Observability**: Integrated with Phoenix for tracing and monitoring
- **Natural Language Operations**: Execute cluster operations using plain English commands
- **Chaos Management**: Detect and fix chaos scenarios with detailed summaries
- **Action Summaries**: Get comprehensive summaries of all cluster operations

## 📋 Prerequisites

- Python 3.11 or 3.12 (Python 3.13+ has limited memory features due to memori compatibility)
- Kubernetes cluster (v1.32+) or access to EKS/AKS/GKE
- API keys for Nebius AI and OpenAI
- Cloud provider credentials (if using managed Kubernetes)

**Note**: 
- The `memori` package requires Python <3.12. If using Python 3.12+, memory features will be limited but the bot will still function.
- The `agents` package (for MCP) requires tensorflow which is not available for Python 3.13+. MCP features will be disabled on Python 3.13+, but the bot works without it.

## 🚀 Quick Start

### Option 1: Standard Setup

1. **Clone and Install**:
```bash
cd multi-agent-sre-bot
./setup.sh
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run the Streamlit UI**:
```bash
source venv/bin/activate
streamlit run app.py
```

4. **Or use the API**:
```bash
source venv/bin/activate
uvicorn api.main:app --reload
```

5. **Or use the CLI**:
```bash
source venv/bin/activate
python cli.py "Check the health of my cluster"
```

### Option 2: Chaos Engineering Testing (Recommended)

Test the bot with a complete Kind cluster setup including chaos scenarios:

```bash
# Setup everything (cluster + apps + chaos + bot)
make all

# Check status
make cluster-status
make sre-bot-status

# View bot logs and detected issues
make sre-bot-logs

# Clean up
make clean
```

See [CHAOS_TESTING.md](CHAOS_TESTING.md) for detailed chaos engineering guide.

### Option 3: Natural Language Operations

The bot supports natural language commands for cluster operations:

```bash
# In Streamlit UI, type:
"fix the chaos scenario in web-app namespace"
"remove chaos from all namespaces"
"rollback deployment api-service"
```

The bot will:
- Parse your natural language command
- Execute the operation
- Provide a detailed summary

See [NATURAL_LANGUAGE_OPS.md](NATURAL_LANGUAGE_OPS.md) for complete guide.

## 🧪 Chaos Engineering Testing

The bot includes a complete chaos engineering setup for testing:

- **Kind Cluster**: Local Kubernetes cluster for testing
- **Sample Applications**: Web app, API service, and database
- **Chaos Scenarios**: 5 different chaos experiments
- **Daemon Mode**: Bot runs in background monitoring and detecting issues

**Quick Start**:
```bash
make all          # Setup everything
make sre-bot-logs # View detected issues
make clean        # Cleanup
```

See [CHAOS_TESTING.md](CHAOS_TESTING.md) for complete guide.

## 📁 Project Structure

```
multi-agent-sre-bot/
├── agents/              # Agent implementations
│   ├── __init__.py
│   ├── coordinator_agent.py
│   ├── troubleshooting_agent.py
│   ├── monitoring_agent.py
│   ├── automation_agent.py
│   └── knowledge_agent.py
├── connectors/          # Cloud platform connectors
│   ├── __init__.py
│   ├── kubernetes.py
│   ├── aws_eks.py
│   ├── azure_aks.py
│   └── gcp_gke.py
├── mcp/                 # MCP server integration
│   ├── __init__.py
│   └── k8s_mcp.py
├── rag/                 # RAG system
│   ├── __init__.py
│   └── knowledge_base.py
├── memory/              # Memory management
│   ├── __init__.py
│   └── memory_manager.py
├── api/                 # FastAPI endpoints
│   ├── __init__.py
│   └── main.py
├── cli.py               # CLI interface
├── app.py               # Streamlit UI
├── daemon.py            # Daemon mode for background monitoring
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── Makefile             # Make targets for cluster/chaos management
├── scripts/             # Setup and management scripts
│   ├── kind-setup.sh
│   ├── deploy-apps.sh
│   ├── chaos-engineering.sh
│   └── sre-bot-daemon.sh
├── manifests/           # Kubernetes application manifests
│   ├── web-app.yaml
│   ├── api-service.yaml
│   └── database.yaml
├── chaos/               # Chaos engineering scenarios
│   ├── pod-kill-web-app.yaml
│   ├── cpu-stress-api.yaml
│   ├── network-latency.yaml
│   ├── memory-pressure-db.yaml
│   └── resource-exhaustion.yaml
└── README.md            # This file
```

## 🔧 Configuration

The bot supports multiple Kubernetes platforms:

### Local Kubernetes
Set `KUBECONFIG` environment variable to your kubeconfig path.

### AWS EKS
Configure AWS credentials and set:
- `AWS_REGION`
- `AWS_EKS_CLUSTER_NAME`

### Azure AKS
Configure Azure credentials and set:
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AKS_CLUSTER_NAME`

### GCP GKE
Set up service account and configure:
- `GCP_PROJECT_ID`
- `GCP_ZONE`
- `GCP_GKE_CLUSTER_NAME`

## 📚 Knowledge Base

The bot includes a comprehensive Kubernetes knowledge base with:
- Official Kubernetes documentation
- Best practices and patterns
- Industry use cases
- Troubleshooting guides
- Migration strategies

Knowledge base is automatically loaded on first run and stored in a vector database.

## 🤖 Agents

### Coordinator Agent
Routes user queries to appropriate specialized agents and synthesizes responses.

### Troubleshooting Agent
- Analyzes pod logs, events, and metrics
- Identifies root causes of issues
- Provides step-by-step remediation guidance

### Monitoring Agent
- Monitors cluster health and resource usage
- Tracks SLOs and error budgets
- Generates health reports

### Automation Agent
- Executes approved runbooks
- Performs automated remediation
- Manages deployments and rollbacks

### Knowledge Agent
- Answers questions from Kubernetes knowledge base
- Provides best practices and recommendations
- Explains concepts and patterns

## 🔐 Security

- Read-only permissions by default
- Write operations only in bot namespace
- All actions logged and audited
- Support for RBAC and policy enforcement

## 📊 Observability

Integrated with Phoenix for:
- Agent execution tracing
- Performance monitoring
- Error tracking
- Conversation analytics

## 🤝 Contributing

See CONTRIBUTING.md for guidelines.

## 📄 License

MIT License

## 🙏 Acknowledgments

Built using:
- Agno AI Framework
- OpenAI Agents SDK
- Model Context Protocol (MCP)
- LlamaIndex for RAG
- Memori for memory management

