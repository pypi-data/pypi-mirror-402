#!/bin/bash
# this_file: examples/validate_report.sh

set -euo pipefail

OUTPUT_FILE=${1:-validate-report.txt}

if ! command -v abersetz >/dev/null 2>&1; then
    echo "abersetz executable not found. Install with: pip install abersetz" >&2
    exit 1
fi

echo "Running abersetz validate (target language: es)..."
abersetz validate --target-lang es >"$OUTPUT_FILE"

echo "Validation summary written to $OUTPUT_FILE"
cat "$OUTPUT_FILE"
