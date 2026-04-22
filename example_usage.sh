#!/bin/bash
# Example API Usage Script
# Run this file to test the EdTech NLP-to-SQL API

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "EdTech NLP-to-SQL API - Example Usage"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API request
make_request() {
    local question="$1"
    local description="$2"
    
    echo -e "${BLUE}📝 Test: ${description}${NC}"
    echo -e "${YELLOW}Question: ${question}${NC}"
    echo ""
    
    response=$(curl -s -X POST "$BASE_URL/query" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$question\"}")
    
    echo "Generated SQL:"
    echo "$response" | jq '.generated_sql' 2>/dev/null || echo "$response"
    echo ""
    echo "Result:"
    echo "$response" | jq '.result' 2>/dev/null || echo "$response"
    echo ""
    echo "Execution Time:"
    echo "$response" | jq '.execution_time' 2>/dev/null || echo "$response"
    echo ""
    echo -e "${GREEN}✅ Test completed${NC}"
    echo "=========================================="
    echo ""
}

# Check if API is running
echo "Checking API health..."
health=$(curl -s "$BASE_URL/health")
if echo "$health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  API may not be running. Start it with: python main.py${NC}"
    exit 1
fi

echo ""

# Test 1: Count total students
make_request "How many students are there?" "Count total students"

# Test 2: Count courses by category
make_request "How many courses in the Programming category?" "Count courses by category"

# Test 3: Filter students by grade
make_request "Show all students in grade 10" "Filter students by grade"

# Test 4: Python course enrollments in 2024
make_request "How many students enrolled in Python courses in 2024?" "Count enrollments by course and year"

# Test 5: Popular course
make_request "Which course is most popular?" "Find most popular course"

# Test 6: Student with most courses
make_request "Which student has the most courses?" "Find student with most enrollments"

# Test 7: Grade distribution
make_request "What's the distribution of students by grade?" "Get grade distribution"

# Test 8: Students with their courses
make_request "Show me students with their courses" "Get student-course relationships"

# Test 9: Total courses
make_request "How many total courses do we have?" "Count total courses"

# Test 10: AI/ML courses
make_request "List all AI/ML courses" "Get courses by category"

echo ""
echo "=========================================="
echo "Getting Analytics"
echo "=========================================="
echo ""

echo -e "${BLUE}📊 Fetching /stats endpoint${NC}"
stats=$(curl -s "$BASE_URL/stats")
echo "Total Queries:"
echo "$stats" | jq '.total_queries' 2>/dev/null || echo "$stats"
echo ""
echo "Common Keywords:"
echo "$stats" | jq '.common_keywords' 2>/dev/null || echo "$stats"
echo ""
echo "Slowest Query:"
echo "$stats" | jq '.slowest_query' 2>/dev/null || echo "$stats"
echo ""
echo "Average Execution Time:"
echo "$stats" | jq '.average_execution_time' 2>/dev/null || echo "$stats"
echo ""

echo ""
echo "=========================================="
echo "Direct cURL Examples"
echo "=========================================="
echo ""
echo "You can also make requests manually:"
echo ""
echo "Basic query:"
echo 'curl -X POST http://localhost:8000/query \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"question": "How many students are there?"}'"'"
echo ""
echo "Get stats:"
echo 'curl http://localhost:8000/stats | jq .'
echo ""
echo "Health check:"
echo 'curl http://localhost:8000/health | jq .'
echo ""

echo -e "${GREEN}✅ All tests completed!${NC}"
