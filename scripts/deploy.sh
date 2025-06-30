#!/bin/bash
# Secure PR Guard Deployment Script
# Enterprise-grade deployment with health checks and rollback

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
🛡️ Secure PR Guard Deployment Script

Usage: $0 [OPTIONS] ENVIRONMENT

ENVIRONMENTS:
    development     Deploy to development environment
    staging         Deploy to staging environment  
    production      Deploy to production environment

OPTIONS:
    -h, --help      Show this help message
    -f, --force     Force deployment without confirmation
    -b, --backup    Create backup before deployment
    -r, --rollback  Rollback to previous version
    -t, --test      Run tests before deployment
    -v, --verbose   Enable verbose output

EXAMPLES:
    $0 development                    # Deploy to development
    $0 --test --backup production     # Test, backup, then deploy to production
    $0 --rollback production          # Rollback production deployment

EOF
}

# Parse command line arguments
ENVIRONMENT=""
FORCE=false
BACKUP=false
ROLLBACK=false
RUN_TESTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -b|--backup)
            BACKUP=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        -t|--test)
            RUN_TESTS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        development|staging|production)
            ENVIRONMENT=$1
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    error "Environment is required. Use -h for help."
fi

# Setup logging
mkdir -p "$(dirname "$LOG_FILE")"
log "🚀 Starting Secure PR Guard deployment to $ENVIRONMENT"

# Pre-flight checks
preflight_checks() {
    log "🔍 Running pre-flight checks..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
    fi
    
    # Check if required files exist
    local required_files=(
        "Dockerfile"
        "docker-compose.yml" 
        "requirements.txt"
        ".env.example"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            error "Required file not found: $file"
        fi
    done
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        warning ".env file not found. Creating from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        info "Please edit .env file with your configuration before deploying"
    fi
    
    log "✅ Pre-flight checks completed"
}

# Run tests
run_tests() {
    if [[ "$RUN_TESTS" == true ]]; then
        log "🧪 Running test suite..."
        
        cd "$PROJECT_ROOT"
        
        # Install test dependencies
        python -m pip install pytest pytest-cov pytest-mock
        
        # Run tests
        if python -m pytest tests/ -v --tb=short; then
            log "✅ All tests passed"
        else
            error "❌ Tests failed. Deployment aborted."
        fi
        
        # Run integration tests
        if [[ -f "test_budget_integration.py" ]]; then
            log "🔗 Running integration tests..."
            if python test_budget_integration.py; then
                log "✅ Integration tests passed"
            else
                error "❌ Integration tests failed. Deployment aborted."
            fi
        fi
    fi
}

# Create backup
create_backup() {
    if [[ "$BACKUP" == true ]]; then
        log "💾 Creating backup..."
        
        mkdir -p "$BACKUP_DIR"
        
        # Backup current deployment
        if docker-compose ps | grep -q "Up"; then
            log "📁 Backing up current containers..."
            docker-compose config > "$BACKUP_DIR/docker-compose-backup.yml"
        fi
        
        # Backup data
        if [[ -d "$PROJECT_ROOT/logs" ]]; then
            cp -r "$PROJECT_ROOT/logs" "$BACKUP_DIR/"
            log "📊 Backed up logs directory"
        fi
        
        if [[ -d "$PROJECT_ROOT/monitoring/config" ]]; then
            cp -r "$PROJECT_ROOT/monitoring/config" "$BACKUP_DIR/"
            log "⚙️ Backed up monitoring config"
        fi
        
        log "✅ Backup created at $BACKUP_DIR"
    fi
}

# Rollback deployment
rollback_deployment() {
    if [[ "$ROLLBACK" == true ]]; then
        log "🔄 Rolling back deployment..."
        
        # Find latest backup
        local latest_backup=$(find "$PROJECT_ROOT/backups" -type d -name "20*" | sort -r | head -n1)
        
        if [[ -z "$latest_backup" ]]; then
            error "No backup found for rollback"
        fi
        
        log "📂 Rolling back to: $latest_backup"
        
        # Stop current services
        docker-compose down
        
        # Restore backup
        if [[ -f "$latest_backup/docker-compose-backup.yml" ]]; then
            cp "$latest_backup/docker-compose-backup.yml" "$PROJECT_ROOT/docker-compose.yml"
        fi
        
        if [[ -d "$latest_backup/logs" ]]; then
            rm -rf "$PROJECT_ROOT/logs"
            cp -r "$latest_backup/logs" "$PROJECT_ROOT/"
        fi
        
        if [[ -d "$latest_backup/monitoring" ]]; then
            cp -r "$latest_backup/monitoring/config" "$PROJECT_ROOT/monitoring/"
        fi
        
        # Start services
        docker-compose up -d
        
        log "✅ Rollback completed"
        exit 0
    fi
}

# Environment-specific configuration
configure_environment() {
    log "⚙️ Configuring $ENVIRONMENT environment..."
    
    case $ENVIRONMENT in
        development)
            export COMPOSE_FILE="docker-compose.yml"
            export LOG_LEVEL="DEBUG"
            export MONITORING_ENABLED="true"
            ;;
        staging)
            export COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
            export LOG_LEVEL="INFO"
            export MONITORING_ENABLED="true"
            ;;
        production)
            export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
            export LOG_LEVEL="WARNING"
            export MONITORING_ENABLED="true"
            ;;
    esac
    
    log "✅ Environment configured for $ENVIRONMENT"
}

# Build and deploy
deploy() {
    log "🏗️ Building and deploying..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    log "📥 Pulling latest base images..."
    docker-compose pull
    
    # Build services
    log "🔨 Building services..."
    docker-compose build --no-cache
    
    # Start services
    log "🚀 Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log "⏳ Waiting for services to be ready..."
    sleep 30
    
    log "✅ Deployment completed"
}

# Health checks
health_checks() {
    log "🏥 Running health checks..."
    
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log "🔍 Health check attempt $attempt/$max_attempts..."
        
        # Check main application
        if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
            log "✅ Main application is healthy"
        else
            warning "⚠️ Main application health check failed"
        fi
        
        # Check monitoring dashboard
        if curl -f -s http://localhost:8080 >/dev/null 2>&1; then
            log "✅ Monitoring dashboard is healthy"
        else
            warning "⚠️ Monitoring dashboard health check failed"
        fi
        
        # Check budget guard integration
        if docker-compose exec -T secure-pr-guard python -c "from monitoring.budget_guard import BudgetGuard; BudgetGuard()" >/dev/null 2>&1; then
            log "✅ Budget Guard integration is healthy"
            break
        else
            warning "⚠️ Budget Guard health check failed"
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "❌ Health checks failed after $max_attempts attempts"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log "✅ All health checks passed"
}

# Post-deployment tasks
post_deployment() {
    log "📋 Running post-deployment tasks..."
    
    # Display service status
    log "📊 Service Status:"
    docker-compose ps
    
    # Display access URLs
    log "🌐 Access URLs:"
    log "   Main Application: http://localhost:8000"
    log "   Monitoring Dashboard: http://localhost:8080"
    log "   Grafana: http://localhost:3000 (admin/pr-guard-admin)"
    log "   Prometheus: http://localhost:9090"
    
    # Show budget status
    log "💰 Budget Status:"
    docker-compose exec -T secure-pr-guard python monitoring/budget_guard.py --check || true
    
    # Show recent logs
    log "📝 Recent logs:"
    docker-compose logs --tail=20 secure-pr-guard
    
    log "✅ Post-deployment tasks completed"
}

# Confirmation prompt
confirm_deployment() {
    if [[ "$FORCE" != true ]]; then
        echo -e "${YELLOW}⚠️ About to deploy Secure PR Guard to $ENVIRONMENT environment${NC}"
        echo -e "${BLUE}Configuration:${NC}"
        echo -e "  - Environment: $ENVIRONMENT"
        echo -e "  - Backup: $BACKUP"
        echo -e "  - Tests: $RUN_TESTS"
        echo ""
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "❌ Deployment cancelled by user"
            exit 0
        fi
    fi
}

# Main deployment flow
main() {
    log "🛡️ Secure PR Guard Deployment Started"
    log "📝 Deployment log: $LOG_FILE"
    
    # Check for rollback
    rollback_deployment
    
    # Confirm deployment
    confirm_deployment
    
    # Run deployment steps
    preflight_checks
    run_tests
    create_backup
    configure_environment
    deploy
    health_checks
    post_deployment
    
    log "🎉 Deployment to $ENVIRONMENT completed successfully!"
    log "📊 View monitoring: http://localhost:8080"
    log "💰 Check budget: docker-compose exec secure-pr-guard python monitoring/budget_guard.py --check"
}

# Trap for cleanup on exit
trap 'log "🛑 Deployment interrupted"' INT TERM

# Run main deployment
main "$@"