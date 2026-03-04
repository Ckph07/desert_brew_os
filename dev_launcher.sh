#!/bin/bash
# ============================================
# Desert Brew OS — Development Launcher
# ============================================
# Launches ALL backend microservices + Flutter frontend
# Usage: `./dev_launcher.sh` [--backend-only | --frontend-only | --all]
#
# Ctrl+C to stop all services
# ============================================

set -e

SERVICES_DIR="$(cd "$(dirname "$0")/services" && pwd)"
FLUTTER_APP_DIR="$(cd "$(dirname "$0")/desert_brew_app" && pwd)"
FLUTTER_BIN="/Users/ckph/Desktop/flutter/bin"
export PATH="$FLUTTER_BIN:$PATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Track PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo -e "${RED}🛑 Stopping all services...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

launch_backend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  🍺 Desert Brew OS — Backend       ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Use the robust python launcher
    conda run -n base python /tmp/launch_services.py &
    PIDS+=($!)
    
    echo -e "${GREEN}  ✓ Backend launch script triggered${NC}"
    echo ""
}


launch_frontend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  🍺 Desert Brew OS — Frontend      ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd "$FLUTTER_APP_DIR"
    echo -e "${BLUE}  Starting Flutter on Web Server (Port 3000)...${NC}"
    # Use web-server instead of chrome to avoid hanging on debug service
    flutter run -d web-server --web-hostname 127.0.0.1 --web-port 3000 &
    PIDS+=($!)
    echo -e "${GREEN}  ✓ Flutter web started at http://localhost:3000${NC}"
    echo ""
}

# Parse args
MODE="${1:---all}"

case "$MODE" in
    --backend-only)
        launch_backend
        ;;
    --frontend-only)
        launch_frontend
        ;;
    --all|*)
        launch_backend
        sleep 2
        launch_frontend
        ;;
esac

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Press Ctrl+C to stop all services ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Wait for all processes
wait
