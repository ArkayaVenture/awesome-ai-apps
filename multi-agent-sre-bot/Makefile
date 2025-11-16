.PHONY: help cluster-up cluster-down cluster-status apps-deploy apps-destroy chaos-create chaos-destroy chaos-list sre-bot-start sre-bot-stop sre-bot-logs sre-bot-status all clean

# Default target
help:
	@echo "Multi-Agent SRE Bot - Kind Cluster Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make cluster-up          - Create Kind cluster"
	@echo "  make cluster-down        - Destroy Kind cluster"
	@echo "  make cluster-status      - Show cluster status"
	@echo "  make apps-deploy         - Deploy sample applications"
	@echo "  make apps-destroy        - Remove sample applications"
	@echo "  make chaos-create        - Create chaos scenarios"
	@echo "  make chaos-destroy       - Remove chaos scenarios"
	@echo "  make chaos-list          - List active chaos experiments"
	@echo "  make sre-bot-start      - Start SRE bot in daemon mode"
	@echo "  make sre-bot-stop       - Stop SRE bot daemon"
	@echo "  make sre-bot-logs       - Show SRE bot logs"
	@echo "  make sre-bot-status      - Check SRE bot status"
	@echo "  make all                - Setup everything (cluster + apps + chaos + bot)"
	@echo "  make clean              - Clean up everything"
	@echo ""

# Kind cluster management
cluster-up:
	@echo "🚀 Creating Kind cluster..."
	@./scripts/kind-setup.sh create
	@echo "✅ Cluster created successfully"

cluster-down:
	@echo "🗑️  Destroying Kind cluster..."
	@./scripts/kind-setup.sh destroy
	@echo "✅ Cluster destroyed"

cluster-status:
	@echo "📊 Cluster Status:"
	@kubectl cluster-info --context kind-sre-bot-cluster 2>/dev/null || echo "❌ Cluster not found"
	@kubectl get nodes --context kind-sre-bot-cluster 2>/dev/null || echo "❌ Cannot connect to cluster"

# Application deployment
apps-deploy:
	@echo "📦 Deploying sample applications..."
	@./scripts/deploy-apps.sh
	@echo "✅ Applications deployed"

apps-destroy:
	@echo "🗑️  Removing sample applications..."
	@kubectl delete namespace web-app --ignore-not-found=true
	@kubectl delete namespace api-service --ignore-not-found=true
	@kubectl delete namespace database --ignore-not-found=true
	@echo "✅ Applications removed"

# Chaos engineering
chaos-create:
	@echo "💥 Creating chaos scenarios..."
	@./scripts/chaos-engineering.sh create
	@echo "✅ Chaos scenarios created"

chaos-destroy:
	@echo "🛑 Stopping chaos scenarios..."
	@./scripts/chaos-engineering.sh destroy
	@echo "✅ Chaos scenarios stopped"

chaos-list:
	@echo "📋 Active chaos experiments:"
	@./scripts/chaos-engineering.sh list

# SRE Bot management
sre-bot-start:
	@echo "🤖 Starting SRE bot in daemon mode..."
	@./scripts/sre-bot-daemon.sh start
	@echo "✅ SRE bot started"

sre-bot-stop:
	@echo "🛑 Stopping SRE bot..."
	@./scripts/sre-bot-daemon.sh stop
	@echo "✅ SRE bot stopped"

sre-bot-logs:
	@./scripts/sre-bot-daemon.sh logs

sre-bot-status:
	@./scripts/sre-bot-daemon.sh status

# Combined targets
all: cluster-up apps-deploy chaos-create sre-bot-start
	@echo ""
	@echo "✅ Everything is set up!"
	@echo "📊 Check status with: make cluster-status"
	@echo "🤖 SRE bot is running in daemon mode"

clean: chaos-destroy apps-destroy sre-bot-stop cluster-down
	@echo "🧹 Cleanup complete"

# Quick test
test: cluster-status
	@echo "🧪 Running quick test..."
	@kubectl get pods --all-namespaces --context kind-sre-bot-cluster || echo "❌ Test failed"

