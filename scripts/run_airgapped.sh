#!/bin/bash
# Run SATx commands in a network-isolated namespace
# Usage: ./scripts/run_airgapped.sh python scripts/predict_passes.py
echo "🔒 Running in air-gapped network namespace..."
exec unshare --net -- "$@"
