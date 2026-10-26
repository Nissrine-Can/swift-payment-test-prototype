#!/bin/bash
# analyze_logs.sh - summarize the payment gateway log

LOG_FILE="logs/server.log"

echo "Payment log summary: $LOG_FILE"
echo "-----------------------------"

TOTAL=$(grep -c "Payment received" "$LOG_FILE")
ACCEPTED=$(grep -c -w "ACK" "$LOG_FILE")
REJECTED=$(grep -c "NACK" "$LOG_FILE")
WARNINGS=$(grep -c "WARN" "$LOG_FILE")

echo "Payments received: $TOTAL"
echo "Accepted (ACK):    $ACCEPTED"
echo "Rejected (NACK):   $REJECTED"
echo "Warnings:          $WARNINGS"
echo
echo "Rejection reasons:"
grep "ERROR" "$LOG_FILE" | grep -v "NACK sent"
