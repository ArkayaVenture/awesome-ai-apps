#!/bin/bash
# Kind cluster setup script

set -e

CLUSTER_NAME="sre-bot-cluster"
KIND_CONFIG="kind-config.yaml"

create_cluster() {
    echo "📦 Creating Kind cluster: $CLUSTER_NAME"
    
    # Create kind config if it doesn't exist
    if [ ! -f "$KIND_CONFIG" ]; then
        cat > "$KIND_CONFIG" <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: $CLUSTER_NAME
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8081
    protocol: TCP
  - containerPort: 443
    hostPort: 8444
    protocol: TCP
- role: worker
- role: worker
EOF
    fi
    
    # Delete existing cluster if it exists
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        echo "🗑️  Removing existing cluster..."
        kind delete cluster --name "$CLUSTER_NAME" || true
        sleep 2
    fi
    
    # Create cluster
    kind create cluster --config "$KIND_CONFIG" --name "$CLUSTER_NAME"
    
    # Wait for cluster to be ready
    echo "⏳ Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s --context "kind-$CLUSTER_NAME" || {
        echo "⚠️  Waiting for nodes to be ready..."
        sleep 10
        kubectl wait --for=condition=Ready nodes --all --timeout=300s --context "kind-$CLUSTER_NAME"
    }
    
    # Set kubeconfig context
    kubectl config use-context "kind-$CLUSTER_NAME"
    
    # Export kubeconfig path for SRE bot
    KUBECONFIG_PATH=$(kind get kubeconfig-path --name "$CLUSTER_NAME" 2>/dev/null || echo "$HOME/.kube/config")
    export KUBECONFIG="$KUBECONFIG_PATH"
    
    # Also set in environment for persistence
    echo "export KUBECONFIG=\"$KUBECONFIG_PATH\"" >> ~/.bashrc 2>/dev/null || true
    echo "export KUBECONFIG=\"$KUBECONFIG_PATH\"" >> ~/.zshrc 2>/dev/null || true
    
    echo "✅ Cluster created and ready!"
    echo "📝 Kubeconfig exported: KUBECONFIG=$KUBECONFIG_PATH"
    kubectl cluster-info --context "kind-$CLUSTER_NAME"
}

destroy_cluster() {
    echo "🗑️  Destroying Kind cluster: $CLUSTER_NAME"
    kind delete cluster --name "$CLUSTER_NAME" || echo "⚠️  Cluster not found or already deleted"
    echo "✅ Cluster destroyed"
}

# Main
case "${1:-}" in
    create)
        create_cluster
        ;;
    destroy)
        destroy_cluster
        ;;
    *)
        echo "Usage: $0 {create|destroy}"
        exit 1
        ;;
esac

