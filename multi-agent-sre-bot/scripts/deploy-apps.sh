#!/bin/bash
# Deploy sample applications to Kind cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR/../manifests"

echo "📦 Deploying sample applications..."

# Create namespaces
kubectl create namespace web-app --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace api-service --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace database --dry-run=client -o yaml | kubectl apply -f -

# Deploy web application
echo "🌐 Deploying web application..."
kubectl apply -f "$MANIFESTS_DIR/web-app.yaml" -n web-app

# Deploy API service
echo "🔌 Deploying API service..."
kubectl apply -f "$MANIFESTS_DIR/api-service.yaml" -n api-service

# Deploy database
echo "💾 Deploying database..."
kubectl apply -f "$MANIFESTS_DIR/database.yaml" -n database

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/web-app -n web-app || true
kubectl wait --for=condition=available --timeout=300s deployment/api-service -n api-service || true
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n database || true

# Show status
echo ""
echo "📊 Deployment Status:"
kubectl get pods --all-namespaces | grep -E "(web-app|api-service|database)"

echo "✅ Applications deployed!"

