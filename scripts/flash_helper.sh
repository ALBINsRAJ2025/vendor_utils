#!/bin/bash
# flash_helper.sh - Helper script for flashing ported ROM via fastboot/ADB
#
# Usage: ./flash_helper.sh [rom_directory]

set -e

ROM_DIR="${1:-.}"
DEVICE_CONNECTED=false

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}"
echo "=========================================="
echo "  ROM Flashing Helper"
echo "  Infinix Note 11 - MT6769H"
echo "=========================================="
echo -e "${COLOR_RESET}"

check_fastboot() {
    echo -n "Checking for fastboot... "
    
    if ! command -v fastboot &> /dev/null; then
        echo -e "${COLOR_RED}NOT FOUND${COLOR_RESET}"
        echo "Install fastboot: sudo apt install android-tools-fastboot"
        exit 1
    fi
    
    echo -e "${COLOR_GREEN}OK${COLOR_RESET}"
}

check_adb() {
    echo -n "Checking for adb... "
    
    if ! command -v adb &> /dev/null; then
        echo -e "${COLOR_RED}NOT FOUND${COLOR_RESET}"
        echo "Install adb: sudo apt install android-tools-adb"
        exit 1
    fi
    
    echo -e "${COLOR_GREEN}OK${COLOR_RESET}"
}

check_device_fastboot() {
    echo ""
    echo "Checking for device in fastboot mode..."
    
    if fastboot devices | grep -q "fastboot"; then
        echo -e "${COLOR_GREEN}✓ Device detected in fastboot mode${COLOR_RESET}"
        DEVICE_CONNECTED=true
        return 0
    else
        echo -e "${COLOR_YELLOW}⚠ No device in fastboot mode${COLOR_RESET}"
        return 1
    fi
}

check_device_adb() {
    echo ""
    echo "Checking for device in ADB mode..."
    
    if adb devices | grep -q "device$"; then
        echo -e "${COLOR_GREEN}✓ Device detected via ADB${COLOR_RESET}"
        DEVICE_CONNECTED=true
        return 0
    else
        echo -e "${COLOR_YELLOW}⚠ No device via ADB${COLOR_RESET}"
        return 1
    fi
}

reboot_to_fastboot() {
    echo ""
    echo "Attempting to reboot device to fastboot..."
    
    if check_device_adb; then
        adb reboot bootloader
        echo "Waiting for fastboot mode..."
        sleep 5
        
        if check_device_fastboot; then
            return 0
        fi
    fi
    
    echo ""
    echo -e "${COLOR_YELLOW}Please manually boot device to fastboot mode:${COLOR_RESET}"
    echo "  1. Power off device"
    echo "  2. Hold Volume Down + Power button"
    echo "  3. Select 'Fastboot mode' when bootloader appears"
    echo ""
    read -p "Press Enter when device is in fastboot mode..."
    
    if check_device_fastboot; then
        return 0
    else
        echo -e "${COLOR_RED}Device not detected in fastboot mode${COLOR_RESET}"
        exit 1
    fi
}

get_device_info() {
    echo ""
    echo "Device Information:"
    echo "===================="
    
    PRODUCT=$(fastboot getvar product 2>&1 | grep "product:" | awk '{print $2}')
    VARIANT=$(fastboot getvar variant 2>&1 | grep "variant:" | awk '{print $2}')
    
    echo "  Product: $PRODUCT"
    echo "  Variant: $VARIANT"
    echo ""
}

verify_images() {
    echo "Verifying ROM images..."
    
    local missing_images=()
    
    CRITICAL_IMAGES=(
        "super.img"
        "boot.img"
        "vbmeta.img"
    )
    
    OPTIONAL_IMAGES=(
        "dtbo.img"
        "recovery.img"
        "vendor_boot.img"
    )
    
    for img in "${CRITICAL_IMAGES[@]}"; do
        if [ -f "$ROM_DIR/$img" ]; then
            SIZE=$(du -h "$ROM_DIR/$img" | awk '{print $1}')
            echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} $img ($SIZE)"
        else
            echo -e "  ${COLOR_RED}✗${COLOR_RESET} $img (MISSING)"
            missing_images+=("$img")
        fi
    done
    
    for img in "${OPTIONAL_IMAGES[@]}"; do
        if [ -f "$ROM_DIR/$img" ]; then
            SIZE=$(du -h "$ROM_DIR/$img" | awk '{print $1}')
            echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} $img ($SIZE)"
        else
            echo -e "  ${COLOR_YELLOW}○${COLOR_RESET} $img (optional, not found)"
        fi
    done
    
    if [ ${#missing_images[@]} -gt 0 ]; then
        echo ""
        echo -e "${COLOR_RED}ERROR: Missing critical images:${COLOR_RESET}"
        for img in "${missing_images[@]}"; do
            echo "  - $img"
        done
        exit 1
    fi
    
    echo ""
}

create_backup() {
    echo "CREATING BACKUP OF CURRENT ROM"
    echo "==============================="
    echo ""
    echo -e "${COLOR_YELLOW}It is STRONGLY recommended to create a backup before flashing!${COLOR_RESET}"
    echo ""
    
    read -p "Do you want to create a backup? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        echo "Creating backup in: $BACKUP_DIR"
        
        PARTITIONS_TO_BACKUP=(
            "super"
            "boot"
            "dtbo"
            "vbmeta"
        )
        
        for partition in "${PARTITIONS_TO_BACKUP[@]}"; do
            echo -n "  Backing up $partition... "
            
            if fastboot getvar "partition-size:$partition" &>/dev/null; then
                fastboot fetch "$partition" "$BACKUP_DIR/${partition}.img" 2>&1 | grep -v "^$" || \
                    echo -e "${COLOR_YELLOW}(skipped)${COLOR_RESET}" && continue
                echo -e "${COLOR_GREEN}done${COLOR_RESET}"
            else
                echo -e "${COLOR_YELLOW}(partition not found)${COLOR_RESET}"
            fi
        done
        
        echo ""
        echo -e "${COLOR_GREEN}Backup created in: $BACKUP_DIR${COLOR_RESET}"
        echo ""
    fi
}

flash_images() {
    echo ""
    echo "FLASHING ROM"
    echo "============"
    echo ""
    echo -e "${COLOR_YELLOW}WARNING: This will replace your current ROM!${COLOR_RESET}"
    echo "Make sure you have a backup before proceeding."
    echo ""
    
    read -p "Are you sure you want to flash? (yes/NO): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo "Flash cancelled."
        exit 0
    fi
    
    echo "Starting flash process..."
    echo ""
    
    if [ -f "$ROM_DIR/vbmeta.img" ]; then
        echo "Flashing vbmeta (disable verified boot)..."
        fastboot --disable-verity --disable-verification flash vbmeta "$ROM_DIR/vbmeta.img" || {
            echo -e "${COLOR_RED}Failed to flash vbmeta${COLOR_RESET}"
            exit 1
        }
    fi
    
    if [ -f "$ROM_DIR/super.img" ]; then
        echo "Wiping super partition..."
        fastboot erase super || echo "Note: erase super failed (may be normal)"
        
        echo "Flashing super partition (this may take several minutes)..."
        fastboot flash super "$ROM_DIR/super.img" || {
            echo -e "${COLOR_RED}Failed to flash super${COLOR_RESET}"
            exit 1
        }
    fi
    
    if [ -f "$ROM_DIR/boot.img" ]; then
        echo "Flashing boot..."
        fastboot flash boot "$ROM_DIR/boot.img" || {
            echo -e "${COLOR_RED}Failed to flash boot${COLOR_RESET}"
            exit 1
        }
    fi
    
    if [ -f "$ROM_DIR/dtbo.img" ]; then
        echo "Flashing dtbo..."
        fastboot flash dtbo "$ROM_DIR/dtbo.img" || echo "Warning: dtbo flash failed"
    fi
    
    if [ -f "$ROM_DIR/vendor_boot.img" ]; then
        echo "Flashing vendor_boot..."
        fastboot flash vendor_boot "$ROM_DIR/vendor_boot.img" || echo "Warning: vendor_boot flash failed"
    fi
    
    echo ""
    echo -e "${COLOR_GREEN}✓ Flash complete!${COLOR_RESET}"
}

wipe_data() {
    echo ""
    echo "DATA WIPE"
    echo "========="
    echo ""
    echo "It is recommended to wipe data when porting between different Android versions."
    echo ""
    
    read -p "Do you want to wipe data/cache? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Wiping userdata..."
        fastboot erase userdata || echo "Warning: userdata wipe failed"
        
        echo "Wiping cache..."
        fastboot erase cache || echo "Note: cache wipe failed (may not exist)"
        
        echo "Formatting data..."
        fastboot format:ext4 userdata || echo "Warning: format failed"
        
        echo -e "${COLOR_GREEN}✓ Data wiped${COLOR_RESET}"
    else
        echo "Skipping data wipe"
    fi
}

reboot_device() {
    echo ""
    echo "REBOOT"
    echo "======"
    echo ""
    
    read -p "Reboot device now? (Y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Rebooting device..."
        fastboot reboot
        
        echo ""
        echo -e "${COLOR_GREEN}Device rebooting...${COLOR_RESET}"
        echo ""
        echo "First boot may take 5-10 minutes."
        echo "If device is stuck on logo for more than 15 minutes, reboot to recovery and wipe data."
    fi
}

print_summary() {
    echo ""
    echo -e "${COLOR_BLUE}=========================================="
    echo "  Flash Complete!"
    echo -e "==========================================${COLOR_RESET}"
    echo ""
    echo "Post-flash checklist:"
    echo "  □ Device boots to system"
    echo "  □ Touchscreen works"
    echo "  □ WiFi/Bluetooth functional"
    echo "  □ Camera works"
    echo "  □ Audio output/input works"
    echo "  □ Mobile data/calls work"
    echo "  □ Sensors functional"
    echo ""
    echo "If you encounter issues:"
    echo "  - Check logcat: adb logcat"
    echo "  - Check SELinux denials: adb logcat | grep 'avc: denied'"
    echo "  - Review kernel log: adb shell dmesg"
    echo ""
    echo "To restore backup (if created):"
    echo "  fastboot flash super backup_XXXXXX/super.img"
    echo "  fastboot flash boot backup_XXXXXX/boot.img"
    echo ""
}

main() {
    check_fastboot
    check_adb
    
    if ! check_device_fastboot; then
        reboot_to_fastboot
    fi
    
    get_device_info
    verify_images
    create_backup
    flash_images
    wipe_data
    reboot_device
    print_summary
}

if [ ! -d "$ROM_DIR" ]; then
    echo -e "${COLOR_RED}Error: ROM directory not found: $ROM_DIR${COLOR_RESET}"
    echo "Usage: $0 [rom_directory]"
    exit 1
fi

main
