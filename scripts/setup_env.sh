#!/bin/bash
# setup_env.sh - Setup ROM porting environment and validate dependencies
#
# Usage: ./setup_env.sh [workspace_dir]

set -e

WORKSPACE_DIR="${1:-rom_porting_workspace}"
REQUIRED_TOOLS=(
    "python3"
    "file"
    "dd"
    "sed"
    "awk"
)

OPTIONAL_TOOLS=(
    "lpunpack"
    "simg2img"
    "img2simg"
    "make_ext4fs"
    "mke2fs"
    "e2fsck"
    "resize2fs"
    "dtc"
    "mkdtboimg"
    "unpack_bootimg"
    "adb"
    "fastboot"
)

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}"
echo "=========================================="
echo "  ROM Porting Environment Setup"
echo "  MT6769H Android 13 Porting Toolkit"
echo "=========================================="
echo -e "${COLOR_RESET}"

check_python_version() {
    echo -n "Checking Python version... "
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${COLOR_RED}FAILED${COLOR_RESET}"
        echo "  Python 3 is not installed"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        echo -e "${COLOR_GREEN}OK${COLOR_RESET} (Python $PYTHON_VERSION)"
        return 0
    else
        echo -e "${COLOR_YELLOW}WARNING${COLOR_RESET} (Python $PYTHON_VERSION - 3.8+ recommended)"
        return 0
    fi
}

check_required_tools() {
    echo ""
    echo "Checking required tools..."
    
    local all_found=true
    
    for tool in "${REQUIRED_TOOLS[@]}"; do
        echo -n "  $tool... "
        
        if command -v "$tool" &> /dev/null; then
            echo -e "${COLOR_GREEN}found${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}NOT FOUND${COLOR_RESET}"
            all_found=false
        fi
    done
    
    if [ "$all_found" = false ]; then
        echo ""
        echo -e "${COLOR_RED}ERROR: Missing required tools${COLOR_RESET}"
        echo "Install missing tools and try again"
        return 1
    fi
    
    return 0
}

check_optional_tools() {
    echo ""
    echo "Checking optional tools..."
    
    local missing_tools=()
    
    for tool in "${OPTIONAL_TOOLS[@]}"; do
        echo -n "  $tool... "
        
        if command -v "$tool" &> /dev/null; then
            echo -e "${COLOR_GREEN}found${COLOR_RESET}"
        else
            echo -e "${COLOR_YELLOW}not found${COLOR_RESET}"
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo ""
        echo -e "${COLOR_YELLOW}Optional tools missing:${COLOR_RESET}"
        echo "  ${missing_tools[*]}"
        echo ""
        echo "To install (Ubuntu/Debian):"
        echo "  sudo apt install android-sdk-libsparse-utils device-tree-compiler"
        echo "  sudo apt install android-tools-adb android-tools-fastboot"
        echo ""
        echo "Some features may be limited without these tools."
    fi
}

setup_workspace() {
    echo ""
    echo "Setting up workspace: $WORKSPACE_DIR"
    
    mkdir -p "$WORKSPACE_DIR"/{source,target,output,tools,logs}
    mkdir -p "$WORKSPACE_DIR/source"/{partitions,super,boot}
    mkdir -p "$WORKSPACE_DIR/target"/{partitions,super,boot}
    mkdir -p "$WORKSPACE_DIR/output"/{merged,super,flashable}
    
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created directory structure"
    
    cat > "$WORKSPACE_DIR/README.txt" << 'EOF'
ROM Porting Workspace
=====================

Directory Structure:
  source/           - Hot 30 (Android 13) ROM files
    partitions/     - Extracted partition images
    super/          - Super image files
    boot/           - Boot, dtbo images
  
  target/           - Note 11 (Android 12) ROM files
    partitions/     - Extracted partition images
    super/          - Super image files
    boot/           - Boot, dtbo images
  
  output/           - Ported ROM output
    merged/         - Merged partitions
    super/          - Reconstructed super.img
    flashable/      - Final flashable ROM
  
  tools/            - Downloaded tools and scripts
  logs/             - Build and extraction logs

Workflow:
1. Place source ROM in source/
2. Place target ROM in target/
3. Extract super images using super_img_extractor.py
4. Analyze differences using partition_analyzer.py
5. Adapt build.prop using build_prop_adapter.py
6. Extract vendor blobs using vendor_blob_extractor.py
7. Merge SELinux policies using selinux_policy_merger.py
8. Reconstruct super.img
9. Create flashable package
EOF
    
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created README.txt"
    
    cat > "$WORKSPACE_DIR/.gitignore" << 'EOF'
# ROM files
*.img
*.zip
*.tar
*.md5

# Logs
*.log

# Temporary files
*.tmp
*.bak
*~

# Python cache
__pycache__/
*.pyc

# Mount points
mnt_*/
EOF
    
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created .gitignore"
}

check_disk_space() {
    echo ""
    echo "Checking disk space..."
    
    AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    echo "  Available: ${AVAILABLE_GB}GB"
    
    if [ "$AVAILABLE_GB" -lt 30 ]; then
        echo -e "  ${COLOR_YELLOW}WARNING: Less than 30GB available${COLOR_RESET}"
        echo "  ROM porting typically requires 30-50GB of free space"
    else
        echo -e "  ${COLOR_GREEN}✓ Sufficient space${COLOR_RESET}"
    fi
}

create_helper_scripts() {
    echo ""
    echo "Creating helper scripts..."
    
    cat > "$WORKSPACE_DIR/quick_extract.sh" << 'EOF'
#!/bin/bash
# Quick extraction script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Extracting source super.img..."
python3 scripts/super_img_extractor.py \
    --super source/super/super.img \
    --output source/partitions \
    --verbose

echo "Extracting target super.img..."
python3 scripts/super_img_extractor.py \
    --super target/super/super.img \
    --output target/partitions \
    --verbose

echo "Extraction complete!"
EOF
    
    chmod +x "$WORKSPACE_DIR/quick_extract.sh"
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created quick_extract.sh"
    
    cat > "$WORKSPACE_DIR/analyze.sh" << 'EOF'
#!/bin/bash
# Quick analysis script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Analyzing partition differences..."
python3 scripts/partition_analyzer.py \
    --source source/partitions \
    --target target/partitions \
    --output output/analysis \
    --verbose

echo "Creating metadata mapping..."
python3 scripts/metadata_mapper.py \
    --source source/partitions \
    --target target/partitions \
    --output output/device_mapping.json \
    --verbose

echo "Analysis complete!"
EOF
    
    chmod +x "$WORKSPACE_DIR/analyze.sh"
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created analyze.sh"
}

print_summary() {
    echo ""
    echo -e "${COLOR_BLUE}=========================================="
    echo "  Setup Complete!"
    echo -e "==========================================${COLOR_RESET}"
    echo ""
    echo "Workspace created at: $WORKSPACE_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Copy source ROM files to: $WORKSPACE_DIR/source/"
    echo "  2. Copy target ROM files to: $WORKSPACE_DIR/target/"
    echo "  3. Run extraction: cd $WORKSPACE_DIR && ./quick_extract.sh"
    echo "  4. Run analysis: cd $WORKSPACE_DIR && ./analyze.sh"
    echo ""
    echo "For detailed guide, see: PORTING_GUIDE.md"
    echo ""
}

main() {
    check_python_version || exit 1
    check_required_tools || exit 1
    check_optional_tools
    check_disk_space
    setup_workspace
    create_helper_scripts
    print_summary
    
    echo -e "${COLOR_GREEN}Environment setup successful!${COLOR_RESET}"
}

main
