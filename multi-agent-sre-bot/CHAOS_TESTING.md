# Chaos Engineering Testing Guide

This guide explains how to use the chaos engineering setup with the SRE Bot.

## Overview

The chaos engineering setup creates various failure scenarios in a Kind cluster to test the SRE bot's ability to detect, diagnose, and resolve issues.

## Quick Start

```bash
# Setup everything (cluster + apps + chaos + bot)
make all

# Check status
make cluster-status
make sre-bot-status

# View SRE bot logs
make sre-bot-logs

# Clean up everything
make clean
```

## Step-by-Step Workflow

### 1. Create Kind Cluster

```bash
make cluster-up
```

This creates a 3-node Kind cluster (1 control plane + 2 workers).

### 2. Deploy Sample Applications

```bash
make apps-deploy
```

Deploys:
- **web-app** namespace: 3 replicas of nginx
- **api-service** namespace: 2 replicas of API service
- **database** namespace: PostgreSQL database

### 3. Create Chaos Scenarios

```bash
make chaos-create
```

This creates 5 chaos scenarios:

1. **Pod Kill**: Randomly kills pods in web-app namespace
2. **CPU Stress**: Stresses CPU on api-service pods
3. **Network Latency**: Injects network delays
4. **Memory Pressure**: Creates memory pressure on database
5. **Resource Exhaustion**: Creates resource contention

### 4. Start SRE Bot in Daemon Mode

```bash
make sre-bot-start
```

The bot will:
- Monitor the cluster every 30 seconds
- Detect issues automatically
- Use troubleshooting agent to analyze problems
- Log findings and recommendations

### 5. Monitor and Analyze

```bash
# Check bot status
make sre-bot-status

# View logs
make sre-bot-logs

# List active chaos
make chaos-list

# Check cluster status
make cluster-status
```

## Chaos Scenarios Details

### Scenario 1: Pod Kill
- **Location**: `chaos/pod-kill-web-app.yaml`
- **Effect**: Randomly terminates pods in web-app namespace
- **Detection**: Bot detects pods in CrashLoopBackOff or missing replicas

### Scenario 2: CPU Stress
- **Location**: `chaos/cpu-stress-api.yaml`
- **Effect**: High CPU usage on api-service pods
- **Detection**: Bot detects high resource usage and performance degradation

### Scenario 3: Network Latency
- **Location**: `chaos/network-latency.yaml`
- **Effect**: Network delays between services
- **Detection**: Bot detects connection timeouts and slow responses

### Scenario 4: Memory Pressure
- **Location**: `chaos/memory-pressure-db.yaml`
- **Effect**: Memory pressure on database pods
- **Detection**: Bot detects OOMKilled pods and memory issues

### Scenario 5: Resource Exhaustion
- **Location**: `chaos/resource-exhaustion.yaml`
- **Effect**: Creates multiple pods competing for resources
- **Detection**: Bot detects resource contention and scheduling issues

## Using the SRE Bot to Resolve Issues

### Automatic Detection

The daemon mode bot automatically:
1. Monitors cluster health every 30 seconds
2. Detects failed pods, high restart counts, and error events
3. Uses the troubleshooting agent to analyze issues
4. Provides step-by-step remediation guidance

### Manual Query via CLI

```bash
# Activate venv
source venv/bin/activate

# Query the bot
python cli.py "My web-app pods are crashing, help me debug"

python cli.py "Check the health of my cluster"

python cli.py "What's causing high CPU usage in api-service?"
```

### Manual Query via API

```bash
# Start API (if not running)
uvicorn api.main:app --reload

# Query the bot
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "My pods are failing, help me troubleshoot"}'
```

### Manual Query via Streamlit UI

```bash
streamlit run app.py
```

Then ask questions like:
- "Why are my pods crashing?"
- "Check cluster health"
- "Analyze the errors in web-app namespace"

## Example Troubleshooting Flow

1. **Chaos is created**: `make chaos-create`
2. **Bot detects issues**: Check `make sre-bot-logs`
3. **Bot analyzes**: Troubleshooting agent provides root cause
4. **Bot recommends**: Step-by-step remediation steps
5. **Resolve chaos**: `make chaos-destroy`
6. **Verify resolution**: `make cluster-status`

## Cleanup

```bash
# Stop everything
make clean

# Or step by step
make chaos-destroy
make apps-destroy
make sre-bot-stop
make cluster-down
```

## Troubleshooting

### Bot not detecting issues
- Check bot logs: `make sre-bot-logs`
- Verify cluster connection: `kubectl get nodes`
- Check bot status: `make sre-bot-status`

### Chaos not working
- Verify chaos pods are running: `kubectl get pods -l chaos=true --all-namespaces`
- Check chaos logs: `kubectl logs <chaos-pod-name> -n <namespace>`

### Cluster issues
- Check cluster status: `make cluster-status`
- View all pods: `kubectl get pods --all-namespaces`
- Check events: `kubectl get events --all-namespaces --sort-by='.lastTimestamp'`

## Advanced Usage

### Custom Chaos Scenarios

Create your own chaos scenarios in the `chaos/` directory and reference them in `scripts/chaos-engineering.sh`.

### Custom Applications

Add your own application manifests in `manifests/` and update `scripts/deploy-apps.sh`.

### Bot Configuration

Edit `.env` to configure:
- API keys
- Kubernetes connection
- Monitoring intervals
- Log levels

## Best Practices

1. **Start Small**: Begin with one chaos scenario
2. **Monitor Closely**: Watch bot logs during chaos
3. **Document Findings**: Note what the bot detects and recommends
4. **Iterate**: Adjust chaos scenarios based on findings
5. **Clean Up**: Always clean up chaos before stopping cluster

