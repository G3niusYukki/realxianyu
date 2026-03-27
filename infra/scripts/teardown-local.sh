#!/bin/bash
# teardown-local.sh - XianyuFlow local infrastructure teardown

set -e

echo "🛑 Tearing down XianyuFlow local infrastructure..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform/environments/local"

if [ ! -d "${TERRAFORM_DIR}" ]; then
    echo "❌ Terraform directory not found: ${TERRAFORM_DIR}"
    exit 1
fi

cd "${TERRAFORM_DIR}"

# Check if terraform state exists
if [ ! -f "terraform.tfstate" ]; then
    echo "⚠️  No terraform state found. Nothing to destroy."
    exit 0
fi

echo "🗑️  Destroying all resources..."
terraform destroy -auto-approve

echo ""
echo "✅ Infrastructure destroyed successfully!"
echo ""
echo "💡 To recreate: ./setup-local.sh"
