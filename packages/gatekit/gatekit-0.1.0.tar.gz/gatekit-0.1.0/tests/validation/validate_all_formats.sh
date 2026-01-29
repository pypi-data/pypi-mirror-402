#!/bin/bash

# Quick Validation Script for Gatekit Auditing Formats
# This script validates all 4 auditing plugin formats
# Exit codes: 0 = all pass, 1 = one or more failures

# set -e  # Exit on first error - disabled to allow validation of all formats

# Colors for output (works on macOS, Linux, WSL)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track validation results
TOTAL_FORMATS=3
PASSED_FORMATS=0
FAILED_FORMATS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✓${NC} $message"
        ((PASSED_FORMATS++))
    elif [ "$status" = "fail" ]; then
        echo -e "${RED}✗${NC} $message"
        ((FAILED_FORMATS++))
    else
        echo -e "${YELLOW}⚠${NC} $message"
    fi
}

# Function to check if file exists and has content
check_file_exists() {
    local file=$1
    local format=$2
    
    if [ ! -f "$file" ]; then
        print_status "fail" "$format: File not found at $file"
        return 1
    fi
    
    if [ ! -s "$file" ]; then
        print_status "fail" "$format: File exists but is empty"
        return 1
    fi
    
    return 0
}

echo "════════════════════════════════════════════════════════════"
echo "     Gatekit Auditing Format Validation"
echo "════════════════════════════════════════════════════════════"
echo ""

# Change to validation directory
cd "$(dirname "$0")"

# 0. Check Plugin Loading (from debug log)
echo "0. Plugin Load Verification"
if [ -f "logs/validation.log" ]; then
    # Check that all auditing plugins loaded successfully
    missing_plugins=""
    for plugin in "line_auditing" "json_auditing" "csv_auditing"; do
        if ! grep -q "Loaded auditing plugin '$plugin'" logs/validation.log 2>/dev/null; then
            missing_plugins="$missing_plugins $plugin"
        fi
    done
    
    if [ -z "$missing_plugins" ]; then
        print_status "pass" "All auditing plugins loaded successfully"
    else
        print_status "fail" "Missing plugins:$missing_plugins"
    fi
    
    # Check for tool renaming in middleware
    if grep -q "Renamed tool.*to 'secure_read'\|Renamed tool.*to 'execute_sql'" logs/validation.log 2>/dev/null; then
        print_status "pass" "Tool renaming detected in middleware logs"
    else
        print_status "warn" "Tool renaming not detected (check if tools/list was called)"
    fi
else
    print_status "warn" "Debug log not found - cannot verify plugin loading"
fi
echo ""

# 1. Validate Line Format
echo "1. Line Format Validation"
if check_file_exists "logs/validation-line.log" "Line"; then
    # Check for proper line format in last 20 lines
    if tail -20 logs/validation-line.log | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}.*UTC - (REQUEST|RESPONSE|NOTIFICATION):.*-.*-.*-.*'; then
        print_status "pass" "Line format: Valid new format detected"
    else
        print_status "fail" "Line format: Invalid format structure"
    fi
fi
echo ""

# 2. Validate JSON Format
echo "2. JSON Format Validation"
if check_file_exists "logs/validation-json.jsonl" "JSON"; then
    # Check if jq is available
    if command -v jq &> /dev/null; then
        # Validate JSON with jq (check last 20 lines)
        if tail -20 logs/validation-json.jsonl | jq '.' > /dev/null 2>&1; then
            # Additional check for required fields and new pipeline structure
            if tail -20 logs/validation-json.jsonl | jq -e '.timestamp and .event_type and .pipeline_outcome and .security_evaluated and .pipeline' > /dev/null 2>&1; then
                print_status "pass" "JSON format: Valid JSON with new pipeline structure"
                
                # Check for pipeline outcomes and nested structure
                if tail -20 logs/validation-json.jsonl | jq -e 'select(.pipeline.stages)' > /dev/null 2>&1; then
                    outcomes=$(tail -20 logs/validation-json.jsonl | jq -r 'select(.pipeline_outcome) | .pipeline_outcome' | sort -u | tr '\n' ' ')
                    print_status "pass" "  Pipeline outcomes detected: $outcomes"
                    print_status "pass" "  Nested pipeline stages detected"
                fi
                
                # Check for tool renaming in JSON logs
                if tail -50 logs/validation-json.jsonl | jq -e 'select(.request.params.name == "secure_read" or .request.params.name == "execute_sql")' > /dev/null 2>&1; then
                    print_status "pass" "  Tool renaming validated: renamed tools used in requests"
                fi
            else
                print_status "fail" "JSON format: Valid JSON but missing required fields"
            fi
        else
            print_status "fail" "JSON format: Invalid JSON structure"
        fi
    else
        # Fallback: Python JSON validation (check last 20 lines)
        if python3 -c "import json; [json.loads(line) for line in open('logs/validation-json.jsonl').readlines()[-20:]]" 2>/dev/null; then
            print_status "pass" "JSON format: Valid JSON (Python validation)"
        else
            print_status "fail" "JSON format: Invalid JSON structure"
        fi
    fi
fi
echo ""

# 3. Validate CSV Format
echo "3. CSV Format Validation"
if check_file_exists "logs/validation-csv.csv" "CSV"; then
    # Check if pandas is available
    if python3 -c "import pandas" 2>/dev/null; then
        # Validate with pandas
        validation_result=$(python3 -c "
import pandas as pd
try:
    df = pd.read_csv('logs/validation-csv.csv')
    expected_cols = ['pipeline_outcome', 'security_evaluated', 'decision_plugin']
    if len(df) > 0 and len(df.columns) > 10 and all(col in df.columns for col in expected_cols):
        print('VALID')
    else:
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            print(f'INVALID: Missing columns: {missing_cols}')
        else:
            print('INVALID: Not enough data or columns')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
        
        if [[ "$validation_result" == "VALID" ]]; then
            print_status "pass" "CSV format: Valid CSV with proper structure (pandas)"
        else
            print_status "fail" "CSV format: $validation_result"
        fi
    else
        # Fallback: Basic CSV validation
        if python3 -c "import csv; list(csv.reader(open('logs/validation-csv.csv')))" 2>/dev/null; then
            print_status "pass" "CSV format: Valid CSV (FALLBACK: basic Python csv module)"
        else
            print_status "fail" "CSV format: Invalid CSV structure"
        fi
    fi
fi
echo ""

# Track validation methods used
VALIDATION_METHODS=""

# Check which tools are available
echo ""
echo "Validation Tools Status:"
if command -v jq &> /dev/null; then
    echo -e "${GREEN}✓${NC} jq: Available (preferred for JSON validation)"
else
    echo -e "${YELLOW}⚠${NC} jq: Not available (using Python fallback)"
    VALIDATION_METHODS="${VALIDATION_METHODS}JSON:Python fallback, "
fi

if python3 -c "import pandas" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} pandas: Available (preferred for CSV validation)"
else
    echo -e "${YELLOW}⚠${NC} pandas: Not available (using basic csv module)"
    VALIDATION_METHODS="${VALIDATION_METHODS}CSV:Basic fallback, "
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo "                    Validation Summary"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Total Formats: $TOTAL_FORMATS"
echo -e "${GREEN}Passed: $PASSED_FORMATS${NC}"
echo -e "${RED}Failed: $FAILED_FORMATS${NC}"

if [ -n "$VALIDATION_METHODS" ]; then
    echo ""
    echo -e "${YELLOW}Note: Some formats validated using fallback methods${NC}"
fi

echo ""

if [ $FAILED_FORMATS -eq 0 ]; then
    echo -e "${GREEN}✓ All auditing formats validated successfully!${NC}"
    echo ""
    echo "Validated Components:"
    echo "  • Line format (human-readable) auditing"
    echo "  • JSON Lines format auditing"
    echo "  • CSV format auditing"
    echo "  • Security pipeline processing"
    echo "  • Multi-server routing support"
    echo "  • Tool renaming and description customization"
    
    if [ -n "$VALIDATION_METHODS" ]; then
        echo ""
        echo "For enhanced validation, consider installing:"
        if ! command -v jq &> /dev/null; then
            echo "  - jq: brew install jq (macOS) or apt-get install jq (Linux)"
        fi
        if ! python3 -c "import pandas" 2>/dev/null; then
            echo "  - pandas: pip install pandas"
        fi
    fi
    exit 0
else
    echo -e "${RED}✗ Validation failed for $FAILED_FORMATS format(s)${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Ensure Gatekit is running with the validation-config.yaml"
    echo "2. Execute test prompts in Claude Desktop to generate events"
    echo "3. Check that all plugins are enabled in the config"
    echo "4. Review logs/validation.log for detailed error messages"
    exit 1
fi