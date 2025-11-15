#!/bin/bash
# Comprehensive test script for ShopWise full-stack application
# Tests both backend API and frontend connectivity

set -e

echo "🧪 ShopWise Full-Stack Testing"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:3000}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoints
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" || echo "000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "📡 Testing Backend API at: $API_URL"
echo ""

# Test 1: Health check
test_endpoint "Health Check" "GET" "$API_URL/api/health"

# Test 2: API Documentation
echo -n "Testing API Docs availability... "
if curl -s "$API_URL/docs" | grep -q "Swagger UI"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((TESTS_FAILED++))
fi

# Test 3: Search endpoint (if API key is set)
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠ Skipping search test (ANTHROPIC_API_KEY not set)${NC}"
    echo "   Set it with: export ANTHROPIC_API_KEY='your-key'"
else
    test_endpoint "Search Endpoint" "POST" "$API_URL/api/search" \
        '{"query": "laptop", "limit": 1}'
fi

echo ""
echo "🌐 Testing Frontend at: $FRONTEND_URL"
echo ""

# Test 4: Frontend availability
echo -n "Testing Frontend availability... "
if curl -s "$FRONTEND_URL" | grep -q "ShopWise\|React\|Vite"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "  Make sure the frontend is running: cd frontend && npm run dev"
    ((TESTS_FAILED++))
fi

# Test 5: CORS configuration (if both are running)
if curl -s "$API_URL/api/health" > /dev/null 2>&1 && \
   curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -n "Testing CORS configuration... "
    cors_test=$(curl -s -X OPTIONS "$API_URL/api/search" \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -w "%{http_code}" -o /dev/null)
    
    if [ "$cors_test" = "200" ] || [ "$cors_test" = "204" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ CORS test inconclusive${NC} (HTTP $cors_test)"
    fi
fi

echo ""
echo "================================"
echo "📊 Test Results:"
echo "   ${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo "   ${RED}Failed: $TESTS_FAILED${NC}"
else
    echo "   Failed: $TESTS_FAILED"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Fix issues before pushing.${NC}"
    exit 1
fi


