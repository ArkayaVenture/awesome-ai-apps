# Quick Start Guide - Chaos Testing with SRE Bot

## Prerequisites

- Docker installed and running
- Kind installed: `brew install kind` or `go install sigs.k8s.io/kind@latest`
- kubectl installed
- Python 3.11+ (or 3.13+ with limited features)
- Make installed

## One-Command Setup

```bash
# Setup everything: cluster, apps, chaos, and bot
make all
```

This will:
1. ✅ Create a 3-node Kind cluster
2. ✅ Deploy sample applications (web-app, api-service, database)
3. ✅ Create 5 chaos scenarios
4. ✅ Start SRE bot in daemon mode

## Check Status

```bash
# Cluster status
make cluster-status

# SRE bot status
make sre-bot-status

# View bot logs (shows detected issues)
make sre-bot-logs
```

## What the Bot Detects

The SRE bot automatically detects:
- ❌ Pods in CrashLoopBackOff
- ⚠️ Pods with high restart counts (>3)
- 🔴 Warning events in namespaces
- 💾 Memory pressure issues
- ⚡ CPU stress and resource exhaustion
- 🌐 Network connectivity problems

## View Detected Issues

```bash
# Real-time logs
make sre-bot-logs

# Or follow logs
tail -f logs/sre-bot.log
```

## Interact with the Bot

### Via CLI
```bash
source venv/bin/activate
python cli.py "My pods are crashing, help me debug"
```

### Via API
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Check cluster health"}'
```

### Via Streamlit UI
```bash
source venv/bin/activate
streamlit run app.py
```

## Cleanup

```bash
# Stop everything
make clean
```

## Common Workflows

### Test Specific Chaos Scenario

```bash
# Start with clean cluster
make cluster-up
make apps-deploy

# Create specific chaos
kubectl apply -f chaos/pod-kill-web-app.yaml

# Start bot
make sre-bot-start

# Watch logs
make sre-bot-logs
```

### Manual Troubleshooting

```bash
# After chaos is created, query the bot
python cli.py "Why are my web-app pods failing?"

# Get step-by-step resolution
python cli.py "Help me fix the issues in my cluster"
```

## Troubleshooting

### Bot not starting
```bash
# Check if venv is activated
source venv/bin/activate

# Check .env file exists
ls -la .env

# Check logs
cat logs/sre-bot.log
```

### Cluster not accessible
```bash
# Verify cluster exists
kind get clusters

# Check kubeconfig
kubectl config current-context

# Should be: kind-sre-bot-cluster
```

### Chaos not working
```bash
# Check chaos pods
kubectl get pods -l chaos=true --all-namespaces

# Check chaos logs
kubectl logs <chaos-pod-name> -n <namespace>
```

## Next Steps

- Read [CHAOS_TESTING.md](CHAOS_TESTING.md) for detailed guide
- Customize chaos scenarios in `chaos/` directory
- Add your own applications in `manifests/` directory
- Configure bot monitoring intervals in `daemon.py`

