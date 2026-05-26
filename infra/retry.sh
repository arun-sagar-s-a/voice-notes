#!/usr/bin/env bash
# Retry terraform apply across all 3 ADs until success or 30-min timeout.

set -u  # error on undefined vars
END=$(( $(date +%s) + 1800 ))  # 30 minutes from now
ATTEMPT=0

while [ "$(date +%s)" -lt "$END" ]; do
  for AD in 0 1 2; do
    ATTEMPT=$((ATTEMPT + 1))
    echo ""
    echo "=== Attempt $ATTEMPT — AD index $AD — $(date +%H:%M:%S) ==="

    terraform apply -auto-approve -var="ad_index=$AD"

    if [ $? -eq 0 ]; then
      echo ""
      echo "✅ SUCCESS on AD $AD (attempt $ATTEMPT)"
      exit 0
    fi

    echo "❌ AD $AD failed. Waiting 60s before next try..."
    sleep 60
  done
done

echo ""
echo "⏱  30 minutes elapsed, still no capacity. Try again later or fall back to AMD micro."
exit 1