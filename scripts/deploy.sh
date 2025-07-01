#!/bin/bash
# Secure PR Guard - Fixed Deployment Script

set -e

echo "🚀 Secure PR Guard - Enterprise Deployment"
echo "==========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
VERSION=${2:-latest}
BACKUP=${3:-false}

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   Environment: $ENVIRONMENT"
echo "   Version: $VERSION"
echo "   Backup: $BACKUP"
echo ""

# Pre-flight checks
echo -e "${BLUE}🔍 Pre-flight Checks${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ .env file not found, creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 Please edit .env file with your actual values${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Environment configuration found${NC}"

# Create necessary directories
echo -e "${BLUE}📁 Creating directories${NC}"
mkdir -p logs monitoring/config docs nginx/conf.d monitoring/grafana/{dashboards,datasources}
echo -e "${GREEN}✅ Directories created${NC}"

# Initialize cost tracking
if [ ! -f "logs/cost.csv" ]; then
    echo "timestamp,pr_url,operation,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms" > logs/cost.csv
    echo -e "${GREEN}✅ Cost tracking initialized${NC}"
fi

# Create default budget config
if [ ! -f "monitoring/budget_config.yaml" ]; then
    cat > monitoring/budget_config.yaml << EOF
daily_limit: 10.0
hourly_limit: 2.0
spike_threshold: 5.0
efficiency_min: 0.10
consecutive_violations: 3
cooldown_minutes: 30
slack_enabled: true
email_enabled: true
console_enabled: true
warning_threshold: 0.7
critical_threshold: 0.9
EOF
    echo -e "${GREEN}✅ Budget configuration created${NC}"
fi

# Backup existing data if requested
if [ "$BACKUP" = "true" ]; then
    echo -e "${BLUE}💾 Creating backup${NC}"
    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup logs and config
    if [ -d "logs" ]; then
        cp -r logs "$BACKUP_DIR/"
    fi
    if [ -d "monitoring/config" ]; then
        cp -r monitoring/config "$BACKUP_DIR/"
    fi
    
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
fi

# Build and deploy
echo -e "${BLUE}🏗️ Building and Deploying${NC}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${BLUE}📦 Production deployment${NC}"
    docker-compose --profile production build --no-cache
    docker-compose --profile production up -d
else
    echo -e "${BLUE}🔧 Development deployment${NC}"
    docker-compose build
    docker-compose up -d
fi

# Wait for services to be healthy
echo -e "${BLUE}🔍 Waiting for services to be healthy${NC}"
sleep 30

# Health checks
echo -e "${BLUE}🏥 Health Checks${NC}"

# Check main application
if docker-compose ps secure-pr-guard | grep -q "Up"; then
    echo -e "${GREEN}✅ Secure PR Guard: Running${NC}"
else
    echo -e "${RED}❌ Secure PR Guard: Failed${NC}"
fi

# Check budget guard
if docker-compose ps budget-guard | grep -q "Up"; then
    echo -e "${GREEN}✅ Budget Guard: Running${NC}"
else
    echo -e "${RED}❌ Budget Guard: Failed${NC}"
fi

# Check monitoring dashboard
if docker-compose ps monitoring-dashboard | grep -q "Up"; then
    echo -e "${GREEN}✅ Monitoring Dashboard: Running${NC}"
else
    echo -e "${RED}❌ Monitoring Dashboard: Failed${NC}"
fi

# Check Redis
if docker-compose ps redis | grep -q "Up"; then
    echo -e "${GREEN}✅ Redis: Running${NC}"
else
    echo -e "${RED}❌ Redis: Failed${NC}"
fi

# Check Prometheus
if docker-compose ps prometheus | grep -q "Up"; then
    echo -e "${GREEN}✅ Prometheus: Running${NC}"
else
    echo -e "${RED}❌ Prometheus: Failed${NC}"
fi

# Check Grafana
if docker-compose ps grafana | grep -q "Up"; then
    echo -e "${GREEN}✅ Grafana: Running${NC}"
else
    echo -e "${RED}❌ Grafana: Failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📊 Access Points:${NC}"
echo "   Monitoring Dashboard: http://localhost:8081"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/pr-guard-admin)"
echo "   Redis: localhost:6379"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Budget check: docker-compose exec budget-guard python monitoring/budget_guard.py --check"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "   1. Edit .env file with your API keys"
echo "   2. Test with: python graph_review.py <PR_URL>"
echo "   3. View monitoring at http://localhost:8081"
echo ""
echo -e "${GREEN}✅ Ready for PR analysis!${NC}"