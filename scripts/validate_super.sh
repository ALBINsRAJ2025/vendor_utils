#!/bin/bash
# validate_super.sh - Validate super.img integrity before processing
#
# Usage: ./validate_super.sh super.img

set -e

SUPER_IMG="$1"

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

if [ -z "$SUPER_IMG" ]; then
    echo "Usage: $0 <super.img>"
    exit 1
fi

if [ ! -f "$SUPER_IMG" ]; then
    echo -e "${COLOR_RED}Error: File not found: $SUPER_IMG${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_BLUE}"
echo "=========================================="
echo "  Super Image Validator"
echo "=========================================="
echo -e "${COLOR_RESET}"

echo "Validating: $SUPER_IMG"
echo ""

validate_file_size() {
    echo -n "Checking file size... "
    
    SIZE=$(stat -c%s "$SUPER_IMG")
    SIZE_MB=$((SIZE / 1024 / 1024))
    SIZE_GB=$((SIZE_MB / 1024))
    
    echo -e "${COLOR_GREEN}OK${COLOR_RESET} (${SIZE_MB}MB / ${SIZE_GB}GB)"
    
    if [ $SIZE -lt 1048576 ]; then
        echo -e "${COLOR_RED}  ERROR: File too small to be valid super image${COLOR_RESET}"
        return 1
    fi
    
    if [ $SIZE_GB -gt 20 ]; then
        echo -e "${COLOR_YELLOW}  WARNING: Unusually large super image${COLOR_RESET}"
    fi
    
    return 0
}

check_sparse_format() {
    echo -n "Checking image format... "
    
    MAGIC=$(od -An -tx4 -N4 "$SUPER_IMG" | tr -d ' ')
    
    if [ "$MAGIC" = "3aff26ed" ]; then
        echo -e "${COLOR_YELLOW}SPARSE${COLOR_RESET}"
        echo "  Image is in sparse format and needs to be converted"
        echo "  Run: simg2img $SUPER_IMG ${SUPER_IMG%.img}_raw.img"
        return 2
    elif [ "$MAGIC" = "67446c41" ]; then
        echo -e "${COLOR_GREEN}RAW${COLOR_RESET}"
        return 0
    else
        echo -e "${COLOR_YELLOW}UNKNOWN${COLOR_RESET} (magic: $MAGIC)"
        return 1
    fi
}

validate_lp_metadata() {
    echo -n "Validating LP metadata... "
    
    LP_MAGIC=$(od -An -tx4 -j4096 -N4 "$SUPER_IMG" | tr -d ' ')
    
    if [ "$LP_MAGIC" = "67446c41" ]; then
        echo -e "${COLOR_GREEN}OK${COLOR_RESET}"
        
        METADATA_SIZE=$(od -An -tu4 -j4100 -N4 "$SUPER_IMG" | tr -d ' ')
        echo "  Metadata size: $METADATA_SIZE bytes"
        
        SLOT_COUNT=$(od -An -tu4 -j4132 -N4 "$SUPER_IMG" | tr -d ' ')
        echo "  Metadata slots: $SLOT_COUNT"
        
        return 0
    else
        echo -e "${COLOR_RED}FAILED${COLOR_RESET}"
        echo "  Invalid LP metadata magic: $LP_MAGIC"
        echo "  Expected: 67446c41"
        return 1
    fi
}

check_readable() {
    echo -n "Checking file readability... "
    
    if [ ! -r "$SUPER_IMG" ]; then
        echo -e "${COLOR_RED}FAILED${COLOR_RESET}"
        echo "  File is not readable"
        return 1
    fi
    
    echo -e "${COLOR_GREEN}OK${COLOR_RESET}"
    return 0
}

extract_partition_info() {
    echo ""
    echo "Extracting partition information..."
    
    if command -v lpunpack &> /dev/null; then
        echo ""
        lpunpack -p "$SUPER_IMG" 2>&1 | grep -v "^$" || true
    else
        echo -e "${COLOR_YELLOW}  lpunpack not available${COLOR_RESET}"
        echo "  Install: sudo apt install android-sdk-libsparse-utils"
    fi
}

calculate_checksum() {
    echo ""
    echo -n "Calculating MD5 checksum... "
    
    if command -v md5sum &> /dev/null; then
        MD5=$(md5sum "$SUPER_IMG" | awk '{print $1}')
        echo -e "${COLOR_GREEN}done${COLOR_RESET}"
        echo "  MD5: $MD5"
        
        CHECKSUM_FILE="${SUPER_IMG}.md5"
        echo "$MD5  $(basename $SUPER_IMG)" > "$CHECKSUM_FILE"
        echo "  Saved to: $CHECKSUM_FILE"
    else
        echo -e "${COLOR_YELLOW}md5sum not available${COLOR_RESET}"
    fi
}

print_summary() {
    echo ""
    echo -e "${COLOR_BLUE}=========================================="
    echo "  Validation Summary"
    echo -e "==========================================${COLOR_RESET}"
    echo ""
    
    if [ "$VALIDATION_PASSED" = true ]; then
        echo -e "${COLOR_GREEN}✓ Super image is valid${COLOR_RESET}"
        echo ""
        echo "You can proceed with extraction:"
        echo "  python3 scripts/super_img_extractor.py --super $SUPER_IMG --output extracted/"
    else
        echo -e "${COLOR_RED}✗ Validation failed${COLOR_RESET}"
        echo ""
        echo "Please verify your super.img file and try again."
    fi
    
    echo ""
}

main() {
    local all_passed=true
    
    validate_file_size || all_passed=false
    check_readable || all_passed=false
    
    check_sparse_format
    local sparse_result=$?
    
    if [ $sparse_result -eq 2 ]; then
        echo ""
        echo -e "${COLOR_YELLOW}Image must be converted from sparse format first${COLOR_RESET}"
        all_passed=false
    elif [ $sparse_result -eq 0 ]; then
        validate_lp_metadata || all_passed=false
    fi
    
    extract_partition_info
    calculate_checksum
    
    if [ "$all_passed" = true ]; then
        VALIDATION_PASSED=true
    else
        VALIDATION_PASSED=false
    fi
    
    print_summary
    
    if [ "$VALIDATION_PASSED" = true ]; then
        exit 0
    else
        exit 1
    fi
}

main
