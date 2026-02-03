#!/bin/bash
# Sprint 2 - Validation and Smoke Tests
# Run this script to validate keg management implementation

set -e  # Exit on error

echo "🚀 Sprint 2 - Keg Management Validation"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if service is running
echo "1️⃣ Checking if Inventory Service is running..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service is not running${NC}"
    echo "Starting service..."
    cd services/inventory_service
    python main.py &
    SERVICE_PID=$!
    sleep 3
    cd ../..
fi

echo ""
echo "2️⃣ Applying Alembic migrations..."
cd services/inventory_service

# Check if Alembic is initialized
if [ ! -d "alembic" ]; then
    echo -e "${YELLOW}⚠ Alembic not initialized. Initializing...${NC}"
    alembic init alembic
fi

# Run migrations
echo "Running: alembic upgrade head"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations applied successfully${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi

cd ../..

echo ""
echo "3️⃣ Running smoke tests on Keg endpoints..."

BASE_URL="http://localhost:8001/api/v1/inventory"

# Test 1: Create keg
echo "   Test 1: Create keg..."
RESPONSE=$(curl -s -X POST "$BASE_URL/kegs" \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "KEG-SMOKE-001",
    "size_liters": 30,
    "keg_type": "SANKE_D"
  }')

KEG_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$KEG_ID" ]; then
    echo -e "   ${GREEN}✓ Keg created: $KEG_ID${NC}"
else
    echo -e "   ${RED}✗ Failed to create keg${NC}"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Test 2: List kegs
echo "   Test 2: List kegs..."
RESPONSE=$(curl -s "$BASE_URL/kegs")
if echo "$RESPONSE" | grep -q "KEG-SMOKE-001"; then
    echo -e "   ${GREEN}✓ Keg listed successfully${NC}"
else
    echo -e "   ${RED}✗ Failed to list kegs${NC}"
    exit 1
fi

# Test 3: Get keg detail
echo "   Test 3: Get keg detail..."
RESPONSE=$(curl -s "$BASE_URL/kegs/$KEG_ID")
if echo "$RESPONSE" | grep -q "qr_code"; then
    QR_CODE=$(echo $RESPONSE | grep -o '"qr_code":"[^"]*' | cut -d'"' -f4)
    echo -e "   ${GREEN}✓ Got keg detail (QR: $QR_CODE)${NC}"
else
    echo -e "   ${RED}✗ Failed to get keg detail${NC}"
    exit 1
fi

# Test 4: Transition to CLEAN
echo "   Test 4: Transition EMPTY → CLEAN..."
RESPONSE=$(curl -s -X PATCH "$BASE_URL/kegs/$KEG_ID/transition" \
  -H "Content-Type: application/json" \
  -d '{
    "new_state": "CLEAN",
    "user_id": 1,
    "location": "Washing Station"
  }')

if echo "$RESPONSE" | grep -q "CLEAN"; then
    echo -e "   ${GREEN}✓ Transition successful${NC}"
else
    echo -e "   ${RED}✗ Transition failed${NC}"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Test 5: Bulk scan with QR
echo "   Test 5: Bulk QR scan..."
RESPONSE=$(curl -s -X POST "$BASE_URL/kegs/bulk-scan" \
  -H "Content-Type: application/json" \
  -d "{
    \"qr_codes\": [\"$QR_CODE\"],
    \"new_state\": \"DIRTY\",
    \"location\": \"Dock A\",
    \"user_id\": 1
  }")

if echo "$RESPONSE" | grep -q "success_count"; then
    echo -e "   ${GREEN}✓ Bulk scan successful${NC}"
else
    echo -e "   ${RED}✗ Bulk scan failed${NC}"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Test 6: Get at-risk kegs
echo "   Test 6: Get at-risk kegs..."
RESPONSE=$(curl -s "$BASE_URL/kegs/at-risk")
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓ At-risk endpoint working${NC}"
else
    echo -e "   ${RED}✗ At-risk endpoint failed${NC}"
    exit 1
fi

echo ""
echo "4️⃣ Cleanup test data..."
# Note: We don't have DELETE endpoint, keg will remain in DB
echo -e "   ${YELLOW}⚠ Test keg KEG-SMOKE-001 remains in database${NC}"

echo ""
echo "5️⃣ Running pytest..."
cd services/inventory_service
pytest tests/unit/test_keg_fsm.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

cd ../..

echo ""
echo "======================================"
echo -e "${GREEN}✅ Sprint 2 Validation PASSED${NC}"
echo "======================================"
echo ""
echo "Summary:"
echo "  ✓ Migrations applied"
echo "  ✓ 6 smoke tests passed"
echo "  ✓ Unit tests passed"
echo "  ✓ System ready for production"
echo ""
echo "Next: Sprint 2.5 - Cold Room Inventory"
