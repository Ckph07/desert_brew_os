#!/bin/bash
# ============================================
# Desert Brew OS — Development Launcher
# ============================================
# Launches ALL backend microservices + Flutter frontend
# Usage: ./dev_launcher.sh [--backend-only | --frontend-only | --all]
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

    declare -A services=(
        ["inventory_service"]="8001"
        ["sales_service"]="8002"
        ["security_service"]="8003"
        ["production_service"]="8004"
        ["finance_service"]="8005"
        ["payroll_service"]="8006"
    )

    for service in inventory_service sales_service security_service production_service finance_service payroll_service; do
        port="${services[$service]}"
        echo -e "${BLUE}  Starting $service on :$port ...${NC}"
        cd "$SERVICES_DIR/$service"
        python main.py > /tmp/desert_brew_${service}.log 2>&1 &
        PIDS+=($!)
        echo -e "${GREEN}  ✓ $service (PID: $!) → http://localhost:$port/docs${NC}"
    done

    echo ""
    echo -e "${GREEN}  All 6 backend services running!${NC}"
    echo -e "${GREEN}  Swagger docs:${NC}"
    echo -e "    📦 Inventory  → http://localhost:8001/docs"
    echo -e "    💰 Sales      → http://localhost:8002/docs"
    echo -e "    🔐 Security   → http://localhost:8003/docs"
    echo -e "    🏭 Production → http://localhost:8004/docs"
    echo -e "    📊 Finance    → http://localhost:8005/docs"
    echo -e "    👥 Payroll    → http://localhost:8006/docs"
    echo ""
}

launch_frontend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  🍺 Desert Brew OS — Frontend      ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd "$FLUTTER_APP_DIR"
    echo -e "${BLUE}  Starting Flutter on Chrome...${NC}"
    flutter run -d chrome &
    PIDS+=($!)
    echo -e "${GREEN}  ✓ Flutter web started${NC}"
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
