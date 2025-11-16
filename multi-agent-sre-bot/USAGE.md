# SRE Bot Usage Guide

## Quick Start Examples

### Using the CLI

```bash
# Check cluster health
python cli.py "Check the health of my Kubernetes cluster"

# Troubleshoot a pod issue
python cli.py "My pod named 'web-app' is crashing, help me debug it"

# Get monitoring information
python cli.py "Show me the resource usage of all pods in the default namespace"

# Ask a knowledge question
python cli.py "What are best practices for Kubernetes resource limits?"

# Execute automation
python cli.py "Rollback the deployment named 'api-service' to the previous version"
```

### Using the API

```bash
# Start the API server
uvicorn api.main:app --reload

# Query the bot
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Check the health of my cluster"}'

# Get cluster information
curl "http://localhost:8000/cluster/info"

# Get pod status
curl "http://localhost:8000/cluster/pods?namespace=default"
```

### Using the Streamlit UI

```bash
# Start the Streamlit app
streamlit run app.py
```

Then open your browser to `http://localhost:8501` and start chatting with the bot.

## Common Use Cases

### 1. Troubleshooting Pod Issues

**Query**: "My pod 'web-app-xyz' is in CrashLoopBackOff state"

**What the bot does**:
- Checks pod status and events
- Retrieves pod logs
- Analyzes error patterns
- Provides root cause analysis
- Suggests remediation steps

### 2. Cluster Health Monitoring

**Query**: "What's the overall health of my cluster?"

**What the bot does**:
- Checks node status
- Analyzes pod distribution
- Reviews resource utilization
- Identifies any anomalies
- Provides health report

### 3. Knowledge Queries

**Query**: "How do I set up horizontal pod autoscaling?"

**What the bot does**:
- Searches Kubernetes knowledge base
- Retrieves relevant documentation
- Provides step-by-step guide
- Includes code examples

### 4. Automation Tasks

**Query**: "Scale my deployment 'api-service' to 5 replicas"

**What the bot does**:
- Verifies deployment exists
- Checks current replica count
- Requests approval if needed
- Executes scaling operation
- Verifies success

## Advanced Configuration

### Platform Selection

Set the `K8S_PLATFORM` environment variable:
- `local` - Local Kubernetes cluster
- `aws` - AWS EKS
- `azure` - Azure AKS
- `gcp` - GCP GKE

### Custom Knowledge Base

To add custom documentation to the knowledge base:

```python
from rag import KubernetesKnowledgeBase

kb = KubernetesKnowledgeBase()
kb.load_documents_from_urls([
    "https://your-custom-docs.com",
    "https://internal-wiki.com/k8s"
])
```

### Memory Configuration

The bot uses Memori for context retention. Configure the database:

```bash
export DATABASE_URL="postgresql://user:pass@localhost/sre_bot"
```

## Troubleshooting

### Bot Not Connecting to Cluster

1. Check your kubeconfig: `kubectl config view`
2. Verify cluster access: `kubectl get nodes`
3. Check environment variables in `.env`

### MCP Server Not Starting

1. Ensure Node.js is installed: `node --version`
2. Try installing MCP server manually: `npx -y @modelcontextprotocol/server-kubernetes`
3. Check MCP server logs in the console

### Knowledge Base Not Loading

1. Verify OpenAI API key is set
2. Check vector store path permissions
3. Review logs for embedding errors

## Best Practices

1. **Start with Health Checks**: Always check cluster health before troubleshooting
2. **Use Specific Queries**: Be specific about namespaces, pod names, etc.
3. **Review Recommendations**: Always review automation actions before approval
4. **Monitor Memory Usage**: Large conversations may impact performance
5. **Keep Knowledge Base Updated**: Regularly update the knowledge base with new docs

## Security Considerations

- The bot operates with read-only permissions by default
- Write operations are limited to the bot namespace
- All actions are logged for audit purposes
- Sensitive data is never stored in memory or logs
- Use RBAC to restrict bot permissions further if needed

