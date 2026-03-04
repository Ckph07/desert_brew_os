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
FLUTTER_BIN="${FLUTTER_BIN:-/Users/ckph/Desktop/flutter/bin}"
export PATH="$FLUTTER_BIN:$PATH"
DOCKER_CMD=${DOCKER_CMD:-"docker compose"}

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
    eval $DOCKER_CMD down >/dev/null 2>&1 || true
    wait 2>/dev/null
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

launch_backend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  🍺 Desert Brew OS — Backend       ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "${BLUE}  Starting dockerized stack...${NC}"
    # Bring up infra + microservices
    eval $DOCKER_CMD up -d --build --remove-orphans \
        postgres timescaledb rabbitmq rabbitmq_setup redis \
        inventory_service sales_service security_service \
        production_service finance_service finance_event_consumer payroll_service

    echo -e "${GREEN}  ✓ Backend services running (docker)${NC}"
    echo ""
}


launch_frontend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  🍺 Desert Brew OS — Frontend      ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd "$FLUTTER_APP_DIR"
    if ! command -v flutter >/dev/null 2>&1; then
        echo -e "${RED}Flutter SDK no encontrado en PATH. Configure FLUTTER_BIN o instale Flutter.${NC}"
        echo ""
        return
    fi
    # Optional clean to avoid stale service worker / cached builds
    if [ "${FLUTTER_CLEAN:-0}" = "1" ]; then
        echo -e "${BLUE}  Running flutter clean (FLUTTER_CLEAN=1)...${NC}"
        flutter clean || true
        rm -rf build/web
    fi
    echo -e "${BLUE}  flutter pub get...${NC}"
    flutter pub get
    echo -e "${BLUE}  Building Flutter Web (release)...${NC}"
    flutter build web --release
    echo -e "${BLUE}  Serving static build on Port 3000...${NC}"
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}python3 no disponible para servir build/web.${NC}"
    else
        python3 -m http.server 3000 --bind 127.0.0.1 --directory build/web &
        PIDS+=($!)
        echo -e "${GREEN}  ✓ Flutter web started at http://localhost:3000${NC}"
        echo -e "${BLUE}  Si ves assets viejos, usa FLUTTER_CLEAN=1 y limpia el service worker en Chrome.${NC}"
    fi
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
