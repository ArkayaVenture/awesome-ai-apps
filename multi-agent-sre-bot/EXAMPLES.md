# Natural Language Operations - Examples

## 🎯 Complete Example: Fix Chaos Scenarios

### Step 1: Create Chaos
```bash
# Terminal 1: Create cluster and chaos
cd multi-agent-sre-bot
make cluster-up
make apps-deploy
make chaos-create
```

### Step 2: Start Bot UI
```bash
# Terminal 2: Start Streamlit UI
cd multi-agent-sre-bot
source venv/bin/activate
streamlit run app.py
```

### Step 3: Initialize Bot
1. Enter **Nebius API Key** in sidebar
2. Select **"Auto-detect (Kind cluster)"** for Kubernetes
3. Click **"🚀 Initialize Multi-Agent System"**

### Step 4: Fix Chaos via Natural Language
In the chat interface, type:
```
fix the chaos scenario in web-app namespace
```

### Step 5: Bot Response
The bot will:
1. **Detect** chaos scenarios in web-app namespace
2. **Remove** all chaos pods, jobs, and deployments
3. **Provide Summary**:
   ```
   ✅ Action Completed: fix the chaos scenario in web-app namespace
   
   Chaos Scenarios Detected:
   - Pods: 3
   - Jobs: 1
   - Deployments: 0
   
   Removed:
   - Pods: 3
   - Jobs: 1
   - Deployments: 0
   
   Namespace: web-app
   
   Deleted Pods:
   - web-app/pod-killer-web-app-xxx
   - web-app/cpu-stress-xxx
   - web-app/network-chaos-xxx
   
   Status: success
   ```

## 📝 More Examples

### Example 1: Remove All Chaos
**Command**: `"remove chaos from all namespaces"`

**Bot Action**:
- Scans all namespaces for chaos scenarios
- Removes all chaos resources
- Provides summary of all namespaces affected

### Example 2: Fix Specific Namespace
**Command**: `"fix the chaos scenario in api-service namespace"`

**Bot Action**:
- Detects chaos in api-service namespace only
- Removes chaos resources
- Verifies cleanup

### Example 3: Rollback Deployment
**Command**: `"rollback deployment web-app in web-app namespace"`

**Bot Action**:
- Checks deployment status
- Identifies previous revision
- Executes rollback
- Verifies success

### Example 4: Multi-Agent Coordination
**Command**: `"check cluster health and fix any issues"`

**Bot Action**:
1. **Monitoring Agent**: Checks cluster health
2. **Troubleshooting Agent**: Identifies issues
3. **Automation Agent**: Fixes issues found
4. **Coordinator**: Synthesizes response

## 🔄 Complete Workflow

```bash
# 1. Setup
make cluster-up
make apps-deploy
make chaos-create

# 2. Start UI
streamlit run app.py

# 3. In UI: Initialize with API keys

# 4. In UI Chat: "fix the chaos scenario in web-app namespace"

# 5. Bot fixes and provides summary

# 6. Verify
kubectl get pods -n web-app -l chaos=true
# Should return: No resources found
```

## 🎨 Multi-Agent Flow Example

**User**: "fix the chaos scenario in web-app namespace"

**Flow**:
1. **Coordinator Agent**: 
   - Parses: "fix" + "chaos" + "web-app namespace"
   - Routes to: Automation Agent

2. **Automation Agent**:
   - Calls: `detect_chaos_scenarios(namespace="web-app")`
   - Finds: 3 pods, 1 job
   - Calls: `fix_chaos_scenarios(namespace="web-app")`
   - Removes: All chaos resources
   - Generates: Summary

3. **Response**:
   - Formatted summary with all details
   - Status confirmation
   - List of resources affected

## ✅ Verification

After bot fixes chaos:
```bash
# Check chaos is gone
kubectl get pods --all-namespaces -l chaos=true

# Check namespace is clean
kubectl get pods -n web-app

# Verify applications still running
kubectl get pods -n web-app -l app=web-app
```

The bot provides complete transparency on what was done! 🎉

