#!/bin/bash
# CLI scripting examples for basyx-client
#
# Prerequisites:
#   pip install basyx-client[cli]
#   Start BaSyx server on localhost:8081
#
# Usage:
#   chmod +x cli_scripting.sh
#   ./cli_scripting.sh

set -e

echo "=== basyx-client CLI Scripting Examples ==="
echo ""

# Check CLI is installed
if ! command -v basyx &> /dev/null; then
    echo "Error: basyx CLI not found"
    echo "Install with: pip install basyx-client[cli]"
    exit 1
fi

echo "1. List shells (table format):"
basyx shells list --limit 5 || echo "   (no shells or server unavailable)"
echo ""

echo "2. List shells (JSON format):"
basyx shells list --limit 3 --format json || echo "   []"
echo ""

echo "3. List submodels:"
basyx submodels list --limit 5 || echo "   (no submodels)"
echo ""

echo "4. Configuration:"
echo "   Config file: ~/.basyx/config.yaml"
basyx config profiles 2>/dev/null || echo "   (no profiles configured)"
echo ""

echo "5. Health check:"
if basyx shells list --limit 1 > /dev/null 2>&1; then
    echo "   ✓ Server is responding"
else
    echo "   ✗ Server not responding"
fi
echo ""

echo "6. Using jq with JSON output:"
if command -v jq &> /dev/null; then
    echo "   Shell IDs:"
    basyx shells list --format json 2>/dev/null | jq -r '.[].id' 2>/dev/null | head -3 || echo "   (none)"
else
    echo "   (jq not installed, skipping)"
fi
echo ""

echo "7. Count resources:"
SHELL_COUNT=$(basyx shells list --all --format json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
SM_COUNT=$(basyx submodels list --all --format json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
echo "   Shells: $SHELL_COUNT"
echo "   Submodels: $SM_COUNT"
echo ""

echo "=== Example Complete ==="
