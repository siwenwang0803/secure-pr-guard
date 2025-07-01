#!/bin/bash
# Docker Image Publishing Script for Secure PR Guard
# Publishes to GitHub Container Registry (GHCR)

set -euo pipefail

# Configuration
PROJECT_NAME="secure-pr-guard"
REGISTRY="ghcr.io"
GITHUB_USERNAME="${GITHUB_USERNAME:-your-username}"  # Replace with your GitHub username
VERSION="${1:-latest}"
PLATFORMS="linux/amd64,linux/arm64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
🐳 Secure PR Guard - Docker Publishing Script

Usage: $0 [VERSION] [OPTIONS]

ARGUMENTS:
    VERSION         Image version tag (default: latest)

OPTIONS:
    -h, --help      Show this help message
    -d, --dry-run   Show commands without executing
    -f, --force     Force rebuild without cache

EXAMPLES:
    $0                    # Publish as :latest
    $0 v1.0.0            # Publish as :v1.0.0
    $0 v1.0.0 --dry-run  # Show what would be published

PREREQUISITES:
    - Docker logged in to GHCR: docker login ghcr.io
    - GitHub username set: export GITHUB_USERNAME=your-username
    - Project built locally: docker-compose build

EOF
}

# Parse arguments
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        v*)
            VERSION=$1
            shift
            ;;
        *)
            VERSION=$1
            shift
            ;;
    esac
done

# Validate prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker login to GHCR
    if ! docker info | grep -q "ghcr.io" 2>/dev/null; then
        warning "Not logged in to GHCR. Run: docker login ghcr.io"
    fi
    
    # Check GitHub username
    if [[ "$GITHUB_USERNAME" == "your-username" ]]; then
        error "Please set your GitHub username: export GITHUB_USERNAME=your-github-username"
    fi
    
    # Check if local image exists
    if ! docker images | grep -q "$PROJECT_NAME" 2>/dev/null; then
        warning "Local image not found. Building now..."
        build_local_image
    fi
    
    log "✅ Prerequisites check completed"
}

# Build local image
build_local_image() {
    log "🔨 Building local image..."
    
    local build_args=""
    if [[ "$FORCE" == true ]]; then
        build_args="--no-cache"
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        info "DRY RUN: docker-compose build $build_args"
        return
    fi
    
    docker-compose build $build_args
    log "✅ Local image built successfully"
}

# Tag images for registry
tag_images() {
    log "🏷️ Tagging images for registry..."
    
    local local_image="secure-pr-guard_secure-pr-guard"
    local base_tag="$REGISTRY/$GITHUB_USERNAME/$PROJECT_NAME"
    
    # Tag with version
    local version_tag="$base_tag:$VERSION"
    
    # Also tag as latest if version is not latest
    local latest_tag="$base_tag:latest"
    
    if [[ "$DRY_RUN" == true ]]; then
        info "DRY RUN: docker tag $local_image $version_tag"
        if [[ "$VERSION" != "latest" ]]; then
            info "DRY RUN: docker tag $local_image $latest_tag"
        fi
        return
    fi
    
    # Tag with version
    docker tag "$local_image" "$version_tag"
    log "✅ Tagged as $version_tag"
    
    # Tag as latest if version is not latest
    if [[ "$VERSION" != "latest" ]]; then
        docker tag "$local_image" "$latest_tag"
        log "✅ Tagged as $latest_tag"
    fi
}

# Push images to registry
push_images() {
    log "🚀 Pushing images to registry..."
    
    local base_tag="$REGISTRY/$GITHUB_USERNAME/$PROJECT_NAME"
    local version_tag="$base_tag:$VERSION"
    local latest_tag="$base_tag:latest"
    
    if [[ "$DRY_RUN" == true ]]; then
        info "DRY RUN: docker push $version_tag"
        if [[ "$VERSION" != "latest" ]]; then
            info "DRY RUN: docker push $latest_tag"
        fi
        return
    fi
    
    # Push version tag
    docker push "$version_tag"
    log "✅ Pushed $version_tag"
    
    # Push latest tag if version is not latest
    if [[ "$VERSION" != "latest" ]]; then
        docker push "$latest_tag"
        log "✅ Pushed $latest_tag"
    fi
}

# Generate usage instructions
generate_usage_instructions() {
    local base_tag="$REGISTRY/$GITHUB_USERNAME/$PROJECT_NAME"
    
    log "📋 Publishing complete! Usage instructions:"
    echo ""
    echo -e "${BLUE}🐳 Pull and run the image:${NC}"
    echo "  docker pull $base_tag:$VERSION"
    echo "  docker run -p 8000:8000 $base_tag:$VERSION"
    echo ""
    echo -e "${BLUE}🐳 Use in docker-compose:${NC}"
    echo "  services:"
    echo "    secure-pr-guard:"
    echo "      image: $base_tag:$VERSION"
    echo "      ports:"
    echo "        - \"8000:8000\""
    echo ""
    echo -e "${BLUE}🐳 Available tags:${NC}"
    echo "  - $base_tag:$VERSION"
    if [[ "$VERSION" != "latest" ]]; then
        echo "  - $base_tag:latest"
    fi
    echo ""
    echo -e "${BLUE}📊 Registry URL:${NC}"
    echo "  https://github.com/$GITHUB_USERNAME/$PROJECT_NAME/pkgs/container/$PROJECT_NAME"
}

# Main execution
main() {
    log "🐳 Starting Docker publishing for Secure PR Guard"
    log "📝 Version: $VERSION"
    log "📦 Registry: $REGISTRY/$GITHUB_USERNAME/$PROJECT_NAME"
    
    if [[ "$DRY_RUN" == true ]]; then
        warning "🧪 DRY RUN MODE - No actual changes will be made"
    fi
    
    check_prerequisites
    build_local_image
    tag_images
    push_images
    generate_usage_instructions
    
    log "🎉 Docker publishing completed successfully!"
}

# Run main function
main "$@"