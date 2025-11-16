# Multi-Agent SRE Bot UI Guide

## 🎯 Overview

The Streamlit UI provides an intuitive interface for interacting with the Multi-Agent SRE Bot. You can configure API keys, initialize the multi-agent system, and interact with the bot through a chat interface.

## 🚀 Getting Started

### 1. Launch the UI

```bash
cd multi-agent-sre-bot
source venv/bin/activate
streamlit run app.py
```

The UI will open in your browser at `http://localhost:8501`

### 2. Configure API Keys

#### Required: Nebius API Key
- **Purpose**: Powers all AI agents (Troubleshooting, Monitoring, Automation, Knowledge, Coordinator)
- **Where to get**: https://nebius.ai
- **Format**: Long alphanumeric string

#### Optional: OpenAI API Key
- **Purpose**: Enables RAG knowledge base with Kubernetes documentation
- **Where to get**: https://platform.openai.com
- **Format**: Starts with `sk-`

### 3. Initialize the System

1. **Enter API Keys** in the sidebar
2. **Click "Validate Keys"** to check key formats
3. **Click "Test Connection"** to verify API connectivity (optional)
4. **Click "Initialize Multi-Agent System"** to start

## 📊 UI Components

### Sidebar

#### API Keys Section
- **Nebius API Key**: Required input field (password type)
- **OpenAI API Key**: Optional input field (password type)
- **Validate Keys**: Checks key format validity
- **Test Connection**: Tests API connectivity
- **Initialize Multi-Agent System**: Main initialization button

#### System Status Section
Shows:
- ✅ System initialization status
- Agent status (Active/Limited)
- Kubernetes cluster connection status
- Node count

#### Reset Session
Clears all session data and allows re-initialization

### Main Area

#### Before Initialization
- Welcome message with setup instructions
- Example queries you can ask
- Kubernetes cluster detection status

#### After Initialization
- **Chat Interface**: Interactive conversation with the bot
- **Quick Actions**: 
  - 📊 Cluster Health
  - 📝 View Pods
  - 🔍 Troubleshoot

## 💬 Using the Chat Interface

### Example Queries

**Troubleshooting:**
- "Why are my pods crashing?"
- "My web-app pods are failing, help me debug"
- "Analyze the errors in api-service namespace"

**Monitoring:**
- "Check the health of my cluster"
- "What's the resource usage?"
- "Show me SLO metrics"

**Knowledge:**
- "How do I set up horizontal pod autoscaling?"
- "What are best practices for resource limits?"
- "Explain Kubernetes deployments"

**Automation:**
- "Scale my deployment to 5 replicas"
- "Rollback the api-service deployment"
- "Execute the health check runbook"

## 🔧 Agent Status Indicators

The UI shows which agents are active:

- ✅ **Active**: Agent is fully functional
- ⚠️ **Limited**: Agent has limited functionality (e.g., no knowledge base)

### Agent Capabilities

1. **Troubleshooting Agent** (🔧)
   - Diagnoses issues
   - Analyzes logs and events
   - Provides remediation steps

2. **Monitoring Agent** (📊)
   - Tracks cluster health
   - Monitors SLOs
   - Generates health reports

3. **Automation Agent** (⚙️)
   - Executes runbooks
   - Performs automated actions
   - Manages deployments

4. **Knowledge Agent** (📚)
   - Answers questions from knowledge base
   - Provides best practices
   - Explains concepts

5. **Coordinator Agent** (🎯)
   - Routes queries to appropriate agents
   - Synthesizes multi-agent responses
   - Manages workflows

## 🎨 UI Features

### Real-time Status
- System status updates in sidebar
- Agent availability indicators
- Cluster connection status

### Chat History
- All conversations are saved in session
- Context is maintained across messages
- Memory system stores important information

### Quick Actions
- One-click common queries
- Pre-configured prompts
- Fast access to common tasks

## 🔐 Security

- API keys are stored in session state only (not persisted)
- Keys are masked in input fields (password type)
- Keys are cleared on session reset
- No keys are logged or stored permanently

## 🐛 Troubleshooting

### UI Not Starting
```bash
# Check if streamlit is installed
pip install streamlit

# Check if venv is activated
source venv/bin/activate
```

### Agents Not Initializing
- Verify API keys are correct
- Check cluster connection
- Review error messages in UI
- Check logs: `tail -f logs/sre-bot.log`

### Chat Not Working
- Ensure system is initialized (green status)
- Check that coordinator agent is active
- Verify Kubernetes cluster is accessible

## 📝 Best Practices

1. **Validate Keys First**: Use "Validate Keys" before initialization
2. **Test Connection**: Verify API connectivity before full initialization
3. **Check Status**: Monitor agent status in sidebar
4. **Use Clear Queries**: Be specific about namespaces, pod names, etc.
5. **Review Responses**: Check agent recommendations before taking action

## 🎯 Workflow Example

1. **Start UI**: `streamlit run app.py`
2. **Enter Keys**: Add Nebius and OpenAI keys
3. **Validate**: Click "Validate Keys"
4. **Initialize**: Click "Initialize Multi-Agent System"
5. **Verify**: Check agent status in sidebar
6. **Query**: Ask "Check the health of my cluster"
7. **Review**: Read the bot's analysis and recommendations
8. **Act**: Follow step-by-step guidance

## ✨ Advanced Features

### Memory System
- Conversations are stored in memory
- Context is retrieved for relevant queries
- User preferences are learned over time

### Multi-Agent Coordination
- Queries are automatically routed to appropriate agents
- Multiple agents can work together on complex queries
- Responses are synthesized for clarity

### RAG Knowledge Base
- Comprehensive Kubernetes documentation
- Best practices and patterns
- Industry use cases and examples

Enjoy using the Multi-Agent SRE Bot! 🚀

