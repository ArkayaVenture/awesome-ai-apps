#!/bin/bash
# Export Kind cluster kubeconfig for SRE bot

CLUSTER_NAME="sre-bot-cluster"

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    # Get kubeconfig path
    KUBECONFIG_PATH=$(kind get kubeconfig-path --name "$CLUSTER_NAME" 2>/dev/null)
    
    if [ -z "$KUBECONFIG_PATH" ]; then
        # Fallback: use default kubeconfig location
        KUBECONFIG_PATH="$HOME/.kube/config"
    fi
    
    # Export for current session
    export KUBECONFIG="$KUBECONFIG_PATH"
    
    # Also set context
    kubectl config use-context "kind-$CLUSTER_NAME" >/dev/null 2>&1
    
    echo "✅ Kubeconfig exported: $KUBECONFIG_PATH"
    echo "📝 Context: kind-$CLUSTER_NAME"
    
    # Verify connection
    if kubectl cluster-info --context "kind-$CLUSTER_NAME" >/dev/null 2>&1; then
        echo "✅ Cluster connection verified"
        return 0
    else
        echo "⚠️  Could not verify cluster connection"
        return 1
    fi
else
    echo "❌ Cluster '$CLUSTER_NAME' not found"
    echo "💡 Run 'make cluster-up' to create the cluster"
    return 1
fi

