#!/bin/bash
# setup-local.sh - XianyuFlow local infrastructure setup

set -e

: "${GRAFANA_ADMIN_PASSWORD:=admin}"
echo "Grafana admin password: set via GRAFANA_ADMIN_PASSWORD env var"

echo "🚀 Setting up XianyuFlow local infrastructure..."

# Check dependencies
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform is required but not installed. Aborting."; exit 1; }
command -v kind >/dev/null 2>&1 || { echo "❌ Kind is required but not installed. Aborting."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed. Aborting."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm is required but not installed. Aborting."; exit 1; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/environments/local"

echo "📦 Initializing Terraform..."
cd "${TERRAFORM_DIR}"
terraform init

echo "🏗️  Creating Kind cluster and deploying infrastructure..."
terraform apply -auto-approve

echo "⏳ Waiting for deployments to be ready..."
echo "   This may take a few minutes..."

# Wait for namespaces
kubectl wait --for=condition=Active namespace/xianyuflow --timeout=60s 2>/dev/null || true
kubectl wait --for=condition=Active namespace/monitoring --timeout=60s 2>/dev/null || true

# Wait for Redis
echo "   Waiting for Redis Cluster..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis-cluster -n xianyuflow --timeout=300s || echo "   ⚠️  Redis timeout, may still be starting"

# Wait for PostgreSQL
echo "   Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n xianyuflow --timeout=300s || echo "   ⚠️  PostgreSQL timeout, may still be starting"

# Wait for Kafka
echo "   Waiting for Kafka..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka -n xianyuflow --timeout=300s || echo "   ⚠️  Kafka timeout, may still be starting"

echo ""
echo "✅ Infrastructure setup complete!"
echo ""
echo "📊 Access your services:"
echo ""
echo "  Grafana (admin/${GRAFANA_ADMIN_PASSWORD}):"
echo "    kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring"
echo "    http://localhost:3000"
echo ""
echo "  Jaeger UI:"
echo "    kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring"
echo "    http://localhost:16686"
echo ""
echo "  PostgreSQL:"
echo "    kubectl port-forward svc/postgresql 5432:5432 -n xianyuflow"
echo ""
echo "  Redis:"
echo "    kubectl port-forward svc/redis-redis-cluster 6379:6379 -n xianyuflow"
echo ""
echo "  Kafka:"
echo "    kubectl port-forward svc/kafka 9092:9092 -n xianyuflow"
echo ""
echo "🔧 Useful commands:"
echo "  kubectl get pods -n xianyuflow       # List application pods"
echo "  kubectl get pods -n monitoring       # List monitoring pods"
echo "  kubectl logs -f <pod-name> -n <ns>   # Follow pod logs"
echo ""
