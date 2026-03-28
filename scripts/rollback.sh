#!/bin/bash
# XianyuFlow v10 Phase 5: Emergency Rollback Script
# Usage: ./rollback.sh [service-name] [version]
# Example: ./rollback.sh gateway-service v1.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-xianyuflow}"
ROLLBACK_TIMEOUT="${ROLLBACK_TIMEOUT:-300}"
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=10

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
usage() {
    cat << EOF
XianyuFlow Emergency Rollback Script

Usage:
    $0 [service-name] [version]

Examples:
    $0 gateway-service v1.0.0           # Rollback gateway-service to v1.0.0
    $0 all                             # Rollback all services to last known good
    $0 gateway-service --dry-run       # Preview rollback without executing

Services:
    - gateway-service

Options:
    --dry-run      Preview changes without executing
    --force        Skip confirmation prompts
    -h, --help     Show this help message

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is required but not installed"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Get current deployment info
get_deployment_info() {
    local service=$1
    kubectl get deployment "$service" -n "$NAMESPACE" -o json 2>/dev/null || echo "{}"
}

# Get previous stable version
get_previous_version() {
    local service=$1

    # Try to get from deployment history
    local revision
    revision=$(kubectl rollout history deployment/"$service" -n "$NAMESPACE" | tail -2 | head -1 | awk '{print $1}')

    if [ -n "$revision" ]; then
        echo "$revision"
    else
        echo ""
    fi
}

# Health check for service
check_service_health() {
    local service=$1
    local retries=$HEALTH_CHECK_RETRIES

    log_info "Checking health of $service..."

    while [ $retries -gt 0 ]; do
        # Check if pods are ready
        local ready_replicas
        ready_replicas=$(kubectl get deployment "$service" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        local desired_replicas
        desired_replicas=$(kubectl get deployment "$service" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")

        if [ "$ready_replicas" == "$desired_replicas" ] && [ "$ready_replicas" -gt 0 ]; then
            # Check health endpoint
            local health_status
            health_status=$(kubectl exec -n "$NAMESPACE" \
                "$(kubectl get pods -n "$NAMESPACE" -l app="$service" -o jsonpath='{.items[0].metadata.name}')" \
                -- wget -qO- --timeout=5 http://localhost:8000/health 2>/dev/null || echo "{}")

            if echo "$health_status" | grep -q "ok"; then
                log_info "Service $service is healthy"
                return 0
            fi
        fi

        log_warn "Health check failed, retrying... ($retries attempts left)"
        sleep "$HEALTH_CHECK_INTERVAL"
        retries=$((retries - 1))
    done

    log_error "Service $service failed health check"
    return 1
}

# Rollback single service
rollback_service() {
    local service=$1
    local target_version=$2
    local dry_run=$3

    log_info "Rolling back $service to $target_version..."

    if [ "$dry_run" == "true" ]; then
        echo "[DRY RUN] Would execute:"
        echo "  kubectl rollout undo deployment/$service -n $NAMESPACE --to-revision=$target_version"
        return 0
    fi

    # Get current deployment state for backup
    local current_state
    current_state=$(get_deployment_info "$service")
    echo "$current_state" > "/tmp/${service}_backup_$(date +%Y%m%d_%H%M%S).json"

    # Perform rollback
    if kubectl rollout undo deployment/"$service" -n "$NAMESPACE" --to-revision="$target_version"; then
        log_info "Rollback command executed, waiting for rollout..."

        # Wait for rollout to complete
        if kubectl rollout status deployment/"$service" -n "$NAMESPACE" --timeout="${ROLLBACK_TIMEOUT}s"; then
            # Health check
            if check_service_health "$service"; then
                log_info "✓ Rollback of $service completed successfully"
                return 0
            else
                log_error "✗ Rollback of $service failed health check"
                return 1
            fi
        else
            log_error "✗ Rollout status check failed for $service"
            return 1
        fi
    else
        log_error "✗ Rollback command failed for $service"
        return 1
    fi
}

# Rollback all services
rollback_all() {
    local dry_run=$1

    log_info "Rolling back all services..."

    local services=("gateway-service")
    local failed_services=()

    for service in "${services[@]}"; do
        local previous_version
        previous_version=$(get_previous_version "$service")

        if [ -n "$previous_version" ]; then
            if ! rollback_service "$service" "$previous_version" "$dry_run"; then
                failed_services+=("$service")
            fi
        else
            log_warn "No previous version found for $service, skipping"
        fi
    done

    if [ ${#failed_services[@]} -eq 0 ]; then
        log_info "✓ All services rolled back successfully"
        return 0
    else
        log_error "✗ Failed to rollback: ${failed_services[*]}"
        return 1
    fi
}

# Database rollback (if needed)
rollback_database() {
    local dry_run=$1

    log_warn "Database rollback should be performed manually"
    echo ""
    echo "Steps to rollback database:"
    echo "1. Identify the migration to rollback to"
    echo "2. Run: alembic downgrade <revision>"
    echo "3. Or restore from backup: pg_restore ..."
    echo ""

    if [ "$dry_run" != "true" ]; then
        read -p "Do you want to continue with application rollback only? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Main function
main() {
    local service=""
    local version=""
    local dry_run="false"
    local force="false"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            --force)
                force="true"
                shift
                ;;
            all)
                service="all"
                shift
                ;;
            *)
                if [ -z "$service" ]; then
                    service=$1
                elif [ -z "$version" ]; then
                    version=$1
                fi
                shift
                ;;
        esac
    done

    # Validate arguments
    if [ -z "$service" ]; then
        log_error "Service name is required"
        usage
        exit 1
    fi

    # Check prerequisites
    check_prerequisites

    # Confirm rollback
    if [ "$force" != "true" ] && [ "$dry_run" != "true" ]; then
        echo ""
        log_warn "You are about to rollback $service"
        log_warn "This action cannot be undone automatically"
        echo ""
        read -p "Are you sure you want to continue? (yes/no) " -r
        echo
        if [[ ! $REPLY =~ ^yes$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi

    # Execute rollback
    if [ "$service" == "all" ]; then
        rollback_all "$dry_run"
    else
        if [ -z "$version" ]; then
            version=$(get_previous_version "$service")
            if [ -z "$version" ]; then
                log_error "Cannot determine previous version for $service"
                exit 1
            fi
            log_info "Using previous version: $version"
        fi

        rollback_service "$service" "$version" "$dry_run"
    fi

    # Summary
    echo ""
    echo "========================================"
    if [ "$dry_run" == "true" ]; then
        log_info "Dry run completed - no changes made"
    else
        log_info "Rollback process completed"
    fi
    echo "========================================"
}

# Run main function
main "$@"
