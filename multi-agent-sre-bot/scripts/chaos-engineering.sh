#!/bin/bash
# Chaos engineering script for Kind cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAOS_DIR="$SCRIPT_DIR/../chaos"

create_chaos() {
    echo "💥 Creating chaos scenarios..."
    
    # Scenario 1: Kill random pods in web-app namespace
    echo "🔪 Scenario 1: Random pod termination in web-app namespace"
    kubectl apply -f "$CHAOS_DIR/pod-kill-web-app.yaml" || true
    
    # Scenario 2: CPU stress on api-service
    echo "⚡ Scenario 2: CPU stress on api-service pods"
    kubectl apply -f "$CHAOS_DIR/cpu-stress-api.yaml" || true
    
    # Scenario 3: Network latency
    echo "🌐 Scenario 3: Network latency injection"
    kubectl apply -f "$CHAOS_DIR/network-latency.yaml" || true
    
    # Scenario 4: Memory pressure
    echo "💾 Scenario 4: Memory pressure on database"
    kubectl apply -f "$CHAOS_DIR/memory-pressure-db.yaml" || true
    
    # Scenario 5: Resource exhaustion
    echo "🔥 Scenario 5: Resource exhaustion"
    kubectl apply -f "$CHAOS_DIR/resource-exhaustion.yaml" || true
    
    # Wait a bit for chaos to take effect
    sleep 5
    
    echo "✅ Chaos scenarios created!"
    echo "📊 Check pod status: kubectl get pods --all-namespaces"
}

destroy_chaos() {
    echo "🛑 Stopping all chaos scenarios..."
    
    kubectl delete -f "$CHAOS_DIR/pod-kill-web-app.yaml" --ignore-not-found=true
    kubectl delete -f "$CHAOS_DIR/cpu-stress-api.yaml" --ignore-not-found=true
    kubectl delete -f "$CHAOS_DIR/network-latency.yaml" --ignore-not-found=true
    kubectl delete -f "$CHAOS_DIR/memory-pressure-db.yaml" --ignore-not-found=true
    kubectl delete -f "$CHAOS_DIR/resource-exhaustion.yaml" --ignore-not-found=true
    
    # Clean up any remaining chaos pods
    kubectl delete pods -l chaos=true --all-namespaces --ignore-not-found=true
    
    echo "✅ Chaos scenarios stopped"
}

list_chaos() {
    echo "📋 Active chaos experiments:"
    echo ""
    echo "Pod Kill Jobs:"
    kubectl get jobs -n web-app -l chaos=true 2>/dev/null || echo "  None"
    echo ""
    echo "Stress Test Pods:"
    kubectl get pods --all-namespaces -l chaos=true 2>/dev/null || echo "  None"
    echo ""
    echo "Failed/Crashed Pods:"
    kubectl get pods --all-namespaces --field-selector=status.phase!=Running 2>/dev/null || echo "  All pods running"
}

# Main
case "${1:-}" in
    create)
        create_chaos
        ;;
    destroy)
        destroy_chaos
        ;;
    list)
        list_chaos
        ;;
    *)
        echo "Usage: $0 {create|destroy|list}"
        exit 1
        ;;
esac

