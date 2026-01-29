#!/bin/bash
# this_file: examples/batch_translate.sh

# Advanced batch translation scripts

set -e  # Exit on error

# Configuration
PROJECT_ROOT="${1:-./docs}"
OUTPUT_BASE="${2:-./translations}"
LANGUAGES=("es" "fr" "de" "ja" "zh-CN" "pt" "it" "ru")
ENGINE="${ABERSETZ_ENGINE:-tr/google}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Abersetz Batch Translation ===${NC}"
echo "Source: $PROJECT_ROOT"
echo "Output: $OUTPUT_BASE"
echo "Engine: $ENGINE"
echo ""

# Function to translate to a single language
translate_lang() {
    local lang=$1
    local output_dir="$OUTPUT_BASE/$lang"

    echo -e "${BLUE}Translating to $lang...${NC}"

    if abersetz tr "$lang" "$PROJECT_ROOT" \ \
        --engine "$ENGINE" \
        --output "$output_dir" \
        --recurse \
        --include "*.md,*.txt,*.html" \
        --xclude ".*,*test*,*draft*"; then
        echo -e "${GREEN}✓ $lang completed${NC}"
        return 0
    else
        echo -e "${RED}✗ $lang failed${NC}"
        return 1
    fi
}

# Create output directory
mkdir -p "$OUTPUT_BASE"

# Track results
SUCCESS_COUNT=0
FAILED_LANGS=()

# Translate to each language
for lang in "${LANGUAGES[@]}"; do
    if translate_lang "$lang"; then
        ((SUCCESS_COUNT++))
    else
        FAILED_LANGS+=("$lang")
    fi
    echo ""
done

# Summary
echo -e "${BLUE}=== Translation Summary ===${NC}"
echo "Successfully translated to $SUCCESS_COUNT/${#LANGUAGES[@]} languages"

if [ ${#FAILED_LANGS[@]} -gt 0 ]; then
    echo -e "${RED}Failed languages: ${FAILED_LANGS[*]}${NC}"
    exit 1
else
    echo -e "${GREEN}All translations completed successfully!${NC}"
fi

# Generate index file
INDEX_FILE="$OUTPUT_BASE/index.md"
echo "# Translations" > "$INDEX_FILE"
echo "" >> "$INDEX_FILE"
echo "Available translations of $PROJECT_ROOT:" >> "$INDEX_FILE"
echo "" >> "$INDEX_FILE"

for lang in "${LANGUAGES[@]}"; do
    if [ -d "$OUTPUT_BASE/$lang" ]; then
        file_count=$(find "$OUTPUT_BASE/$lang" -type f | wc -l)
        echo "- [$lang]($lang/) - $file_count files" >> "$INDEX_FILE"
    fi
done

echo -e "${GREEN}Index generated at $INDEX_FILE${NC}"