#!/bin/bash
# this_file: examples/pipeline.sh

# Complete translation pipeline with preprocessing and postprocessing

set -euo pipefail

# Configuration
SOURCE_DIR="${1:-.}"
TARGET_LANG="${2:-es}"
WORK_DIR="/tmp/abersetz_work_$$"
FINAL_OUTPUT="${3:-./translated_$TARGET_LANG}"

# Setup work directory
mkdir -p "$WORK_DIR"
trap "rm -rf $WORK_DIR" EXIT

echo "=== Abersetz Translation Pipeline ==="
echo "Source: $SOURCE_DIR"
echo "Target language: $TARGET_LANG"
echo "Output: $FINAL_OUTPUT"
echo ""

# Step 1: Find and copy translatable files
echo "Step 1: Collecting files..."
find "$SOURCE_DIR" -type f \( \
    -name "*.md" -o \
    -name "*.txt" -o \
    -name "*.html" -o \
    -name "*.htm" \
\) -not -path "*/\.*" -not -path "*/node_modules/*" \
   -not -path "*/venv/*" -not -path "*/__pycache__/*" | while read -r file; do
    rel_path="${file#$SOURCE_DIR/}"
    dest="$WORK_DIR/source/$rel_path"
    mkdir -p "$(dirname "$dest")"
    cp "$file" "$dest"
done

FILE_COUNT=$(find "$WORK_DIR/source" -type f 2>/dev/null | wc -l || echo 0)
echo "  Found $FILE_COUNT files"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "No files to translate!"
    exit 1
fi

# Step 2: Preprocess files (optional)
echo -e "\nStep 2: Preprocessing..."
# Example: Convert markdown links to absolute URLs
# find "$WORK_DIR/source" -name "*.md" -exec sed -i.bak 's|\](./|\](https://example.com/|g' {} \;
echo "  Preprocessing complete"

# Step 3: Translate
echo -e "\nStep 3: Translating..."
if abersetz tr "$TARGET_LANG" "$WORK_DIR/source" \ \
    --output "$WORK_DIR/translated" \
    --recurse; then
    echo "  Translation complete"
else
    echo "  Translation failed!"
    exit 1
fi

# Step 4: Postprocess translations
echo -e "\nStep 4: Postprocessing..."
# Example: Fix common translation issues
find "$WORK_DIR/translated" -type f -name "*.md" | while read -r file; do
    # Fix code blocks that might have been translated
    sed -i.bak 's/```[a-z]*$/```/g' "$file"
    # Remove backup files
    rm -f "${file}.bak"
done
echo "  Postprocessing complete"

# Step 5: Generate translation report
echo -e "\nStep 5: Generating report..."
REPORT_FILE="$WORK_DIR/translated/TRANSLATION_REPORT.md"
cat > "$REPORT_FILE" <<EOF
# Translation Report

## Summary
- **Source Directory**: $SOURCE_DIR
- **Target Language**: $TARGET_LANG
- **Date**: $(date)
- **Files Translated**: $FILE_COUNT

## File List
EOF

find "$WORK_DIR/translated" -type f -not -name "TRANSLATION_REPORT.md" | while read -r file; do
    rel_path="${file#$WORK_DIR/translated/}"
    size=$(wc -c < "$file")
    echo "- $rel_path ($(numfmt --to=iec-i --suffix=B $size))" >> "$REPORT_FILE"
done

echo "  Report generated"

# Step 6: Copy to final destination
echo -e "\nStep 6: Copying to final destination..."
rm -rf "$FINAL_OUTPUT"
cp -r "$WORK_DIR/translated" "$FINAL_OUTPUT"
echo "  Files copied to $FINAL_OUTPUT"

# Step 7: Verification
echo -e "\nStep 7: Verification..."
TRANSLATED_COUNT=$(find "$FINAL_OUTPUT" -type f -not -name "TRANSLATION_REPORT.md" | wc -l)
if [ "$TRANSLATED_COUNT" -eq "$FILE_COUNT" ]; then
    echo "  ✓ All files translated successfully"
else
    echo "  ⚠ Warning: Expected $FILE_COUNT files, found $TRANSLATED_COUNT"
fi

echo -e "\n=== Pipeline Complete ==="
echo "Translated files are in: $FINAL_OUTPUT"
echo "Report available at: $FINAL_OUTPUT/TRANSLATION_REPORT.md"