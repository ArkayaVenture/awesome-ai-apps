# Natural Language Cluster Operations

## 🎯 Overview

The Multi-Agent SRE Bot now supports **natural language commands** for cluster operations. Users can interact with the bot using plain English to perform operations on the Kubernetes cluster, and the bot will:

1. **Parse** the natural language command
2. **Detect** what operation is needed
3. **Execute** the operation using the appropriate agent
4. **Provide** a detailed summary of the action

## 💬 Example Workflow

### Scenario: Fix Chaos Scenarios

1. **User creates chaos**:
   ```bash
   make chaos-create
   ```

2. **User asks bot in chat**:
   ```
   "fix the chaos scenario in web-app namespace"
   ```

3. **Bot responds**:
   - Detects chaos scenarios in web-app namespace
   - Removes all chaos pods, jobs, and deployments
   - Provides detailed summary:
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

## 🤖 Supported Operations

### Chaos Management
- **"fix the chaos scenario in [namespace]"** - Removes all chaos scenarios from specified namespace
- **"remove chaos from [namespace]"** - Same as fix
- **"stop chaos in [namespace]"** - Stops chaos scenarios
- **"clean up chaos scenarios"** - Removes all chaos from all namespaces

### Deployment Operations
- **"rollback deployment [name] in [namespace]"** - Rolls back a deployment
- **"scale deployment [name] to [N] replicas"** - Scales a deployment
- **"restart deployment [name]"** - Restarts a deployment

### General Operations
- **"fix [issue]"** - Uses automation agent to fix issues
- **"remove [resource]"** - Removes specified resource
- **"delete [resource] in [namespace]"** - Deletes a resource

## 🔧 How It Works

### 1. Natural Language Parsing
The coordinator agent analyzes the user's query and:
- Identifies operation keywords (fix, remove, delete, etc.)
- Extracts namespace if mentioned
- Determines which agent should handle it

### 2. Multi-Agent Coordination
- **Coordinator Agent**: Routes the command to appropriate agent
- **Automation Agent**: Executes the cluster operation
- **Troubleshooting Agent**: (if needed) Diagnoses issues before fixing
- **Monitoring Agent**: (if needed) Verifies operation success

### 3. Operation Execution
The automation agent:
- Detects what needs to be done
- Performs the operation using Kubernetes API
- Tracks all changes made
- Generates detailed summary

### 4. Summary Generation
After execution, the bot provides:
- What was detected
- What was changed
- Resources affected
- Status of operation
- Any errors encountered

## 📝 Example Commands

### Chaos Scenarios
```
"fix the chaos scenario in web-app namespace"
"remove all chaos from api-service"
"stop chaos experiments"
"clean up chaos in default namespace"
```

### Deployments
```
"rollback web-app deployment in web-app namespace"
"scale api-service to 5 replicas"
"restart database deployment"
```

### General
```
"fix the pod crashes in web-app"
"remove failed pods from default namespace"
"clean up old jobs"
```

### Direct kubectl (via MCP)
```
"list cluster namespaces"          -> kubectl get namespaces
"show pods in api namespace"       -> kubectl get pods -n api
"describe pod web-123 in web-app"  -> kubectl describe pod web-123 -n web-app
"stream logs for pod api-7d6c8"    -> kubectl logs api-7d6c8 -f
```
These commands are executed through the Kubernetes MCP server for secure, auditable cluster access. If MCP is unavailable the bot falls back to the local `kubectl` binary.

## 🎨 Multi-Agent Flow

### Example: "fix the chaos scenario in web-app namespace"

1. **Coordinator Agent**:
   - Receives: "fix the chaos scenario in web-app namespace"
   - Detects: operation keyword "fix", "chaos", namespace "web-app"
   - Routes to: Automation Agent

2. **Automation Agent**:
   - Detects chaos scenarios in web-app namespace
   - Removes chaos pods, jobs, deployments
   - Generates summary

3. **Response**:
   - Formatted summary with all details
   - Status of operation
   - List of resources affected

## 🔍 Detection Capabilities

The bot can detect:
- **Chaos Pods**: Pods with `chaos=true` label
- **Chaos Jobs**: Jobs with `chaos=true` label
- **Chaos Deployments**: Deployments with `chaos=true` label
- **Namespace-specific**: Can filter by namespace
- **All namespaces**: Can operate cluster-wide

## ✅ Action Summaries

Every operation returns a detailed summary including:
- **Action**: What was requested
- **Detected**: What was found before action
- **Changed**: What was modified/removed
- **Details**: Specific resources affected
- **Status**: Success/partial/failed
- **Errors**: Any issues encountered

## 🚀 Usage in Streamlit UI

1. **Start the UI**:
   ```bash
   streamlit run app.py
   ```

2. **Initialize the bot** with API keys

3. **Type natural language commands**:
   - "fix the chaos scenario in web-app namespace"
   - "remove chaos from all namespaces"
   - "rollback deployment api-service"

4. **Get detailed summaries** of all actions

## 🎯 Benefits

- **Natural Interaction**: No need to know kubectl commands
- **Multi-Agent**: Uses specialized agents for different tasks
- **Detailed Summaries**: Know exactly what was done
- **Safe Operations**: Bot verifies before executing
- **Context Aware**: Understands namespaces and resources

The bot now understands natural language and can perform cluster operations with detailed summaries! 🎉

