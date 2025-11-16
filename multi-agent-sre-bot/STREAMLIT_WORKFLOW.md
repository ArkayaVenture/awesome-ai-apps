# Streamlit UI Workflow - Independent Lifecycles

## 🎯 Overview

The Multi-Agent SRE Bot Streamlit UI is designed with **independent lifecycles**:
- **Kind Cluster**: Managed via Makefile (`make cluster-up`, `make apps-deploy`, etc.)
- **SRE Bot**: Managed via Streamlit UI (start/stop independently)
- **Kubeconfig**: Dynamically imported/selected in UI

## 🚀 Workflow

### Step 1: Start Kind Cluster (Independent)

```bash
# In terminal 1: Manage cluster lifecycle
cd multi-agent-sre-bot

# Create cluster
make cluster-up

# Deploy applications
make apps-deploy

# Create chaos scenarios (optional, can be done after bot is running)
make chaos-create
```

### Step 2: Start Streamlit UI (Independent)

```bash
# In terminal 2: Start Streamlit UI
cd multi-agent-sre-bot
source venv/bin/activate
streamlit run app.py
```

The UI will open at `http://localhost:8501`

### Step 3: Configure in UI

#### 3.1 API Keys
1. Enter **Nebius API Key** (required)
2. Enter **OpenAI API Key** (optional, for RAG)
3. Click **"Validate Keys"** to check formats
4. Click **"Test Connection"** to verify APIs (optional)

#### 3.2 Kubernetes Configuration
1. Select **Kubeconfig Source**:
   - **Auto-detect (Kind cluster)**: Automatically detects `sre-bot-cluster`
   - **Default (~/.kube/config)**: Uses default kubeconfig
   - **Custom path**: Enter custom kubeconfig path

2. If using "Auto-detect":
   - UI will show: ✅ Kind cluster 'sre-bot-cluster' detected
   - Or: ℹ️ Kind cluster not found (if cluster not running)

### Step 4: Initialize Multi-Agent System

1. Click **"🚀 Initialize Multi-Agent System"**
2. Bot will:
   - Connect to Kubernetes cluster using selected kubeconfig
   - Initialize all 5 agents
   - Show status of each agent
   - Enable chat interface

### Step 5: Start Scenarios (After Bot is Running)

```bash
# In terminal 1: Start chaos scenarios
make chaos-create

# Or start specific scenarios
make chaos-list
```

The bot will automatically detect issues as chaos scenarios affect the cluster.

## 🔄 Independent Lifecycle Management

### Cluster Lifecycle (Makefile)
```bash
make cluster-up      # Create cluster
make apps-deploy     # Deploy apps
make chaos-create    # Start chaos
make cluster-status  # Check status
make clean           # Destroy everything
```

### Bot Lifecycle (Streamlit UI)
- **Start**: `streamlit run app.py`
- **Stop**: Close browser or Ctrl+C
- **Reconfigure**: Change API keys/kubeconfig in UI
- **Reinitialize**: Click "Initialize Multi-Agent System" again

### Key Benefits
1. **Cluster can run independently** - Create/destroy without affecting bot
2. **Bot can run independently** - Start/stop UI without affecting cluster
3. **Kubeconfig selection** - Choose cluster at runtime
4. **No hard dependencies** - Bot doesn't require cluster to be running to start

## 📊 UI Features

### Kubernetes Configuration Section
- **Auto-detect**: Automatically finds Kind cluster
- **Default**: Uses standard kubeconfig location
- **Custom**: Specify any kubeconfig path
- **Status indicators**: Shows if cluster is detected

### Agent Status
After initialization, sidebar shows:
- ✅ Troubleshooting Agent: Active
- ✅ Monitoring Agent: Active
- ✅ Automation Agent: Active
- ✅ Knowledge Agent: Active (if OpenAI key provided)
- ✅ Coordinator Agent: Active
- ✅ Kubernetes Connected

### Chat Interface
Once initialized:
- Ask questions about cluster
- Get troubleshooting help
- Monitor cluster health
- Execute automated actions

## 🎯 Typical Workflow

### Scenario 1: Fresh Start
```bash
# Terminal 1
make cluster-up
make apps-deploy

# Terminal 2
streamlit run app.py
# In UI: Enter keys, select "Auto-detect", initialize
# Then in Terminal 1:
make chaos-create
```

### Scenario 2: Bot Already Running
```bash
# Terminal 1 (cluster already running)
make chaos-create

# Bot in UI automatically detects new issues
```

### Scenario 3: Switch Clusters
```bash
# In UI:
# 1. Change kubeconfig selection
# 2. Click "Reset Session"
# 3. Re-initialize with new cluster
```

## 🔧 Troubleshooting

### Bot Can't Find Cluster
1. Check cluster is running: `make cluster-status`
2. Verify kubeconfig: `kubectl config current-context`
3. Try "Custom path" option with explicit path
4. Check Kind cluster name matches: `kind get clusters`

### Import Errors
- Fixed: MCP module now loads correctly
- Fixed: Relative imports resolved
- If issues persist, restart Streamlit

### Connection Issues
- Verify kubeconfig path is correct
- Check cluster is accessible: `kubectl get nodes`
- Ensure context is set: `kubectl config use-context kind-sre-bot-cluster`

## ✅ Benefits of This Architecture

1. **Separation of Concerns**: Cluster and bot managed independently
2. **Flexibility**: Can connect to any cluster at runtime
3. **Resilience**: Bot can restart without affecting cluster
4. **Testing**: Easy to test with different clusters
5. **Development**: Can develop bot without cluster running

## 📝 Notes

- Cluster lifecycle is managed via Makefile
- Bot lifecycle is managed via Streamlit UI
- Kubeconfig is selected/imported at runtime
- No hard coupling between cluster and bot
- Both can be started/stopped independently

This architecture allows for maximum flexibility and independent operation! 🚀

