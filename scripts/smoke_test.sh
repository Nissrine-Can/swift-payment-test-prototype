#!/bin/bash
# smoke_test.sh - quick API checks with curl.
# Start the API first in another terminal: python3 api/app.py

cd "$(dirname "$0")/.." || exit 1

BASE_URL="http://localhost:5000"
passed=0
failed=0

# Stop early if the API is not running
if ! curl -s "$BASE_URL/health" | grep -q "UP"; then
  echo "API is not running. Start it with: python3 api/app.py"
  exit 1
fi

# run_test NAME BODY EXPECTED_CODE EXPECTED_STATUS
run_test() {
  local name="$1" body="$2" expected_code="$3" expected_status="$4"
  local response code
  response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/xml" \
    --data-binary "$body" "$BASE_URL/payments")
  code=$(echo "$response" | tail -n 1)

  if [ "$code" = "$expected_code" ] && echo "$response" | grep -q "<Status>$expected_status</Status>"; then
    echo "PASS  $name (HTTP $code, $expected_status)"
    passed=$((passed + 1))
  else
    echo "FAIL  $name (expected HTTP $expected_code $expected_status, got HTTP $code)"
    failed=$((failed + 1))
  fi
}

run_test "Valid payment"   @data/payment.xml     200 ACK
run_test "Invalid payment" @data/payment_bad.xml 400 NACK
run_test "Not XML"         "hello"               400 NACK

echo "-----------------------------"
echo "Passed: $passed  Failed: $failed"

# Exit code 0 only if every test passed, so CI can use it
[ "$failed" -eq 0 ]