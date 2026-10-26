#!/bin/bash
# Run check_payment.py on every XML file in /data, save the output,
# and print a summary. Works in Git Bash and in a Linux Docker container.

cd "$(dirname "$0")/.." || exit 1

# Use python3 if it exists (Linux), otherwise python (Windows Git Bash)
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python is not installed"
  exit 1
fi

RESULTS_DIR="results/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"
LOG="$RESULTS_DIR/run.log"

passed=0
failed=0

for file in data/*.xml; do
  echo "----------------------------------------" | tee -a "$LOG"
  "$PYTHON" scripts/check_payment.py "$file" | tee -a "$LOG"
  # PIPESTATUS[0] is Python's exit code; plain $? would be tee's (always 0)
  if [ "${PIPESTATUS[0]}" -eq 0 ]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
  fi
done

echo "========================================"
echo "Files passed: $passed"
echo "Files failed: $failed"
echo "Failed checks found in log: $(grep -c "FAIL" "$LOG")"
echo "Full log saved to: $LOG"

# Non-zero exit code if anything failed, so a CI pipeline would mark the run as failed
[ "$failed" -eq 0 ]
