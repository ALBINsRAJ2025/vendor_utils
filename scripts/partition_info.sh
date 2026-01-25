#!/bin/bash
# partition_info.sh - Print detailed partition info from super.img
#
# Usage: ./partition_info.sh super.img

SUPER_IMG="$1"

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'
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
echo "============================================================"
echo "  Super Image Partition Information"
echo "============================================================"
echo -e "${COLOR_RESET}"

echo "File: $SUPER_IMG"
SIZE=$(stat -c%s "$SUPER_IMG")
SIZE_MB=$((SIZE / 1024 / 1024))
SIZE_GB=$((SIZE_MB / 1024))
echo "Size: ${SIZE_MB}MB (${SIZE_GB}GB)"
echo ""

check_format() {
    MAGIC=$(od -An -tx4 -N4 "$SUPER_IMG" | tr -d ' ')
    
    if [ "$MAGIC" = "3aff26ed" ]; then
        echo -e "${COLOR_YELLOW}Format: SPARSE (needs conversion)${COLOR_RESET}"
        echo ""
        echo "Convert to raw format first:"
        echo "  simg2img $SUPER_IMG ${SUPER_IMG%.img}_raw.img"
        echo ""
        exit 1
    fi
}

print_metadata_geometry() {
    echo -e "${COLOR_CYAN}LP Metadata Geometry:${COLOR_RESET}"
    echo "-----------------------------------------------------------"
    
    LP_MAGIC=$(od -An -tx4 -j4096 -N4 "$SUPER_IMG" | tr -d ' ')
    if [ "$LP_MAGIC" != "67446c41" ]; then
        echo -e "${COLOR_RED}Invalid LP metadata magic${COLOR_RESET}"
        return 1
    fi
    
    STRUCT_SIZE=$(od -An -tu4 -j4100 -N4 "$SUPER_IMG" | tr -d ' ')
    METADATA_MAX_SIZE=$(od -An -tu4 -j4108 -N4 "$SUPER_IMG" | tr -d ' ')
    METADATA_SLOT_COUNT=$(od -An -tu4 -j4132 -N4 "$SUPER_IMG" | tr -d ' ')
    
    echo "  Magic:             0x$LP_MAGIC"
    echo "  Struct size:       $STRUCT_SIZE bytes"
    echo "  Max metadata size: $METADATA_MAX_SIZE bytes"
    echo "  Metadata slots:    $METADATA_SLOT_COUNT"
    echo ""
}

extract_with_lpunpack() {
    if ! command -v lpunpack &> /dev/null; then
        echo -e "${COLOR_YELLOW}lpunpack not found - install android-sdk-libsparse-utils${COLOR_RESET}"
        return 1
    fi
    
    echo -e "${COLOR_CYAN}Partition List:${COLOR_RESET}"
    echo "-----------------------------------------------------------"
    
    OUTPUT=$(lpunpack -p "$SUPER_IMG" 2>&1)
    
    echo "$OUTPUT" | while IFS= read -r line; do
        if echo "$line" | grep -q "Name:"; then
            NAME=$(echo "$line" | awk '{print $2}')
            echo -e "${COLOR_GREEN}$NAME${COLOR_RESET}"
        elif echo "$line" | grep -q "Group:"; then
            echo "  $line"
        elif echo "$line" | grep -q "Attr:"; then
            echo "  $line"
        elif echo "$line" | grep -q "Extent:"; then
            echo "  $line"
        fi
    done
    
    echo ""
    echo -e "${COLOR_CYAN}Partition Summary:${COLOR_RESET}"
    echo "-----------------------------------------------------------"
    
    TOTAL_PARTITIONS=$(echo "$OUTPUT" | grep -c "Name:" || echo "0")
    echo "  Total partitions: $TOTAL_PARTITIONS"
    
    SLOT_A=$(echo "$OUTPUT" | grep -c "_a" || echo "0")
    SLOT_B=$(echo "$OUTPUT" | grep -c "_b" || echo "0")
    
    if [ "$SLOT_A" -gt 0 ] || [ "$SLOT_B" -gt 0 ]; then
        echo "  A/B slots: YES"
        echo "    Slot A partitions: $SLOT_A"
        echo "    Slot B partitions: $SLOT_B"
    else
        echo "  A/B slots: NO"
    fi
    
    echo ""
    echo "Partitions by type:"
    
    for partition_type in system vendor product system_ext odm; do
        COUNT=$(echo "$OUTPUT" | grep "Name:" | grep -c "$partition_type" || echo "0")
        if [ "$COUNT" -gt 0 ]; then
            echo "  $partition_type: $COUNT"
        fi
    done
    
    echo ""
}

print_hex_dump() {
    echo -e "${COLOR_CYAN}Header Hex Dump (first 512 bytes):${COLOR_RESET}"
    echo "-----------------------------------------------------------"
    
    hexdump -C "$SUPER_IMG" -n 512 | head -20
    echo "..."
    echo ""
}

print_extraction_command() {
    echo -e "${COLOR_CYAN}Extraction Command:${COLOR_RESET}"
    echo "-----------------------------------------------------------"
    echo ""
    echo "To extract all partitions:"
    echo ""
    echo "  python3 scripts/super_img_extractor.py \\"
    echo "    --super $SUPER_IMG \\"
    echo "    --output extracted_partitions/ \\"
    echo "    --verbose"
    echo ""
    echo "Or with lpunpack directly:"
    echo ""
    echo "  lpunpack -p $SUPER_IMG extracted_partitions/"
    echo ""
}

main() {
    check_format
    print_metadata_geometry
    extract_with_lpunpack
    print_extraction_command
    
    echo -e "${COLOR_BLUE}============================================================${COLOR_RESET}"
}

main
