# Android 13 ROM Porting Guide
## Infinix Hot 30 (A13) → Infinix Note 11 (A12 → A13)

**Last Updated:** January 2025  
**Target SoC:** MediaTek MT6769H (Helio G88)  
**Partition Type:** Dynamic A/B Super Partitions

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Preparation & Environment Setup](#phase-1-preparation--environment-setup)
4. [Phase 2: ROM Extraction](#phase-2-rom-extraction)
5. [Phase 3: Device-Specific Component Identification](#phase-3-device-specific-component-identification)
6. [Phase 4: Adaptation Process](#phase-4-adaptation-process)
7. [Phase 5: Super.img Reconstruction](#phase-5-superimg-reconstruction)
8. [Phase 6: Testing & Validation](#phase-6-testing--validation)
9. [Phase 7: Troubleshooting](#phase-7-troubleshooting)
10. [Phase 8: Rollback Procedure](#phase-8-rollback-procedure)

---

## Introduction

This guide provides step-by-step instructions for porting Android 13 ROM from **Infinix Hot 30** to **Infinix Note 11**. Both devices share the same chipset (MT6769H/Helio G88) and use dynamic A/B super partitions, making them compatible for ROM porting.

### Device Specifications

| Specification | Hot 30 (Source) | Note 11 (Target) |
|---------------|-----------------|------------------|
| SoC | MT6769H (Helio G88) | MT6769H (Helio G88) |
| Android Version | 13 | 12 → 13 |
| Partition Scheme | Dynamic A/B Super | Dynamic A/B Super |
| Super Partitions | system, system_ext, product, vendor | system, system_ext, product, vendor |
| RAM | 8GB | 6/8GB |
| Storage | 128/256GB | 128GB |

### What This Guide Covers

- Extracting and analyzing super.img from both devices
- Identifying device-specific vs. shared components
- Adapting system, vendor, and product partitions
- Merging SELinux policies for compatibility
- Reconstructing super.img with adapted partitions
- Flashing and testing the ported ROM

---

## Prerequisites

### Hardware Requirements

- **PC/Laptop:** 8GB+ RAM, 50GB+ free storage
- **USB Cable:** Quality USB cable for stable connection
- **Target Device:** Infinix Note 11 with unlocked bootloader
- **Backup:** Full device backup or ability to restore stock ROM

### Software Requirements

#### Essential Tools

```bash
# Python 3.8+
python3 --version

# Android SDK Platform Tools
adb --version
fastboot --version

# Sparse Image Tools
simg2img --version
img2simg --version

# LP Tools (for super.img)
lpunpack --version
lpmake --version

# Filesystem Tools
mke2fs -V
e2fsck -V
resize2fs -V
```

#### Installation (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install essential packages
sudo apt install -y \
    python3 python3-pip \
    android-sdk-platform-tools \
    android-sdk-libsparse-utils \
    android-tools-adb android-tools-fastboot \
    e2fsprogs f2fs-tools \
    device-tree-compiler \
    brotli lz4 zstd

# Install Python dependencies
pip3 install protobuf
```

### ROM Files Required

#### Source Device (Hot 30 - Android 13)

- `super.img` or extracted partitions:
  - `system_a.img`
  - `system_ext_a.img`
  - `product_a.img`
  - `vendor_a.img`
- `boot.img`
- `dtbo.img` (optional but recommended)
- `vbmeta.img`

#### Target Device (Note 11 - Android 12)

- `super.img` or extracted partitions:
  - `system_a.img`
  - `system_ext_a.img`
  - `product_a.img`
  - `vendor_a.img`
- `boot.img`
- `dtbo.img` (optional)
- `vbmeta.img`

---

## Phase 1: Preparation & Environment Setup

### Step 1.1: Setup Working Environment

Run the environment setup script:

```bash
cd scripts/
./setup_env.sh rom_porting_workspace
cd rom_porting_workspace/
```

This creates the following structure:

```
rom_porting_workspace/
├── source/          # Hot 30 ROM files
│   ├── partitions/  # Extracted partition images
│   ├── super/       # Super image
│   └── boot/        # Boot images
├── target/          # Note 11 ROM files
│   ├── partitions/
│   ├── super/
│   └── boot/
├── output/          # Ported ROM output
│   ├── merged/      # Adapted partitions
│   ├── super/       # Reconstructed super.img
│   └── flashable/   # Final flashable package
├── tools/           # Additional tools
└── logs/            # Build logs
```

### Step 1.2: Place ROM Files

```bash
# Copy source ROM (Hot 30)
cp /path/to/hot30/super.img source/super/
cp /path/to/hot30/boot.img source/boot/
cp /path/to/hot30/vbmeta.img source/boot/

# Copy target ROM (Note 11)
cp /path/to/note11/super.img target/super/
cp /path/to/note11/boot.img target/boot/
cp /path/to/note11/vbmeta.img target/boot/
```

### Step 1.3: Validate Super Images

```bash
# Validate source super.img
../scripts/validate_super.sh source/super/super.img

# Validate target super.img
../scripts/validate_super.sh target/super/super.img
```

**Expected Output:**
```
✓ File size: OK
✓ LP metadata: OK
✓ Super image is valid
```

If sparse format is detected:

```bash
# Convert sparse to raw (if needed)
simg2img source/super/super.img source/super/super_raw.img
simg2img target/super/super.img target/super/super_raw.img
```

### Step 1.4: Check Partition Information

```bash
# View source partition layout
../scripts/partition_info.sh source/super/super.img

# View target partition layout
../scripts/partition_info.sh target/super/super.img
```

**Expected partitions:**
- `system_a`, `system_b`
- `system_ext_a`, `system_ext_b`
- `product_a`, `product_b`
- `vendor_a`, `vendor_b`

---

## Phase 2: ROM Extraction

### Step 2.1: Extract Source ROM (Hot 30)

```bash
# Extract all partitions from source super.img
python3 ../scripts/super_img_extractor.py \
    --super source/super/super.img \
    --output source/partitions \
    --info source/partition_info.json \
    --verbose
```

**Expected Output:**
```
[+] Successfully extracted 8 partitions:
    system_a         2048.50 MB  ext4     (slot a)
    system_ext_a      512.25 MB  ext4     (slot a)
    product_a         384.75 MB  ext4     (slot a)
    vendor_a          512.00 MB  ext4     (slot a)
    system_b            0.50 MB  ext4     (slot b)
    system_ext_b        0.50 MB  ext4     (slot b)
    product_b           0.50 MB  ext4     (slot b)
    vendor_b            0.50 MB  ext4     (slot b)
```

### Step 2.2: Extract Target ROM (Note 11)

```bash
# Extract all partitions from target super.img
python3 ../scripts/super_img_extractor.py \
    --super target/super/super.img \
    --output target/partitions \
    --info target/partition_info.json \
    --verbose
```

### Step 2.3: Mount and Explore Partitions

```bash
# Create mount points
mkdir -p mnt_source/{system,vendor,product,system_ext}
mkdir -p mnt_target/{system,vendor,product,system_ext}

# Mount source partitions (requires sudo)
sudo mount -o ro,loop source/partitions/system_a.img mnt_source/system
sudo mount -o ro,loop source/partitions/vendor_a.img mnt_source/vendor
sudo mount -o ro,loop source/partitions/product_a.img mnt_source/product
sudo mount -o ro,loop source/partitions/system_ext_a.img mnt_source/system_ext

# Mount target partitions
sudo mount -o ro,loop target/partitions/system_a.img mnt_target/system
sudo mount -o ro,loop target/partitions/vendor_a.img mnt_target/vendor
sudo mount -o ro,loop target/partitions/product_a.img mnt_target/product
sudo mount -o ro,loop target/partitions/system_ext_a.img mnt_target/system_ext
```

### Step 2.4: Extract Build Properties

```bash
# Extract build.prop files for analysis
cp mnt_source/system/build.prop source/system_build.prop
cp mnt_source/vendor/build.prop source/vendor_build.prop
cp mnt_target/system/build.prop target/system_build.prop
cp mnt_target/vendor/build.prop target/vendor_build.prop
```

---

## Phase 3: Device-Specific Component Identification

### Step 3.1: Analyze Partition Differences

```bash
# Run comprehensive partition analysis
python3 ../scripts/partition_analyzer.py \
    --source source/partitions \
    --target target/partitions \
    --output output/analysis \
    --verbose
```

**Review output files:**
- `output/analysis/analysis_report.txt` - Detailed comparison
- `output/analysis/MIGRATION_SUMMARY.md` - Migration strategy
- `output/analysis/analysis_data.json` - Raw data

**Key sections to review:**

1. **Vendor Partition Analysis** - Identifies critical HALs to preserve
2. **System Partition Analysis** - Android 13 framework files
3. **Device-Specific Files** - Camera, audio, radio, sensors

### Step 3.2: Extract Vendor Blobs (Target Device)

```bash
# Extract and categorize vendor blobs from Note 11
python3 ../scripts/vendor_blob_extractor.py \
    --vendor mnt_target/vendor \
    --output output/vendor_blobs \
    --device note11 \
    --extract-critical \
    --generate-files \
    --verbose
```

**Review output:**
- `output/vendor_blobs/blob_report.txt` - Categorized blobs
- `output/vendor_blobs/critical_blobs/` - Device-specific HALs
- `output/vendor_blobs/proprietary-files.txt` - List for device tree

**Critical blobs to preserve from Note 11:**

```
AUDIO:
  lib64/hw/audio.primary.mt6769.so
  lib64/libaudiocustparam.so
  lib/soundfx/libaudiopreprocessing.so

CAMERA:
  lib64/libcam.*.so
  lib64/libmtkcam_*.so
  lib64/hw/camera.provider@2.4-impl-mediatek.so

RADIO/MODEM:
  lib64/libmtk-ril.so
  lib64/libratconfig.so
  bin/mtk_agpsd

DISPLAY:
  lib64/hw/hwcomposer.mt6769.so
  lib64/libged.so

GPU:
  lib64/libGLES_mali.so
  lib64/egl/libGLES_mali.so

SENSORS:
  lib64/hw/sensors.mt6769.so
  lib64/libhwm.so
```

### Step 3.3: Device Tree Extraction and Comparison

```bash
# Extract device tree from source boot.img
python3 ../scripts/device_tree_extractor.py \
    --boot source/boot/boot.img \
    --output output/dtb_source \
    --decompile \
    --verbose

# Extract device tree from target boot.img
python3 ../scripts/device_tree_extractor.py \
    --boot target/boot/boot.img \
    --output output/dtb_target \
    --decompile \
    --verbose

# Compare device trees
python3 ../scripts/device_tree_extractor.py \
    --compare output/dtb_source/dtb_0.dts output/dtb_target/dtb_0.dts \
    --diff output/device_tree_diff.patch
```

**Review differences** - especially memory, display, and sensor configurations.

### Step 3.4: Create Device Metadata Mapping

```bash
# Generate device identifier mapping
python3 ../scripts/metadata_mapper.py \
    --source source/partitions \
    --target target/partitions \
    --output output/device_mapping.json \
    --script output/apply_substitutions.sh \
    --verbose
```

**Review compatibility report:**
- Chipset match: Should be ✓ YES (both MT6769H)
- Platform match: Should be ✓ YES
- Android version upgrade: SDK 31 → 33

---

## Phase 4: Adaptation Process

### Step 4.1: Adapt Build.prop Files

#### System Build.prop

```bash
# Adapt system build.prop
python3 ../scripts/build_prop_adapter.py \
    --source source/system_build.prop \
    --target target/system_build.prop \
    --output output/merged/system_build.prop \
    --patch output/build_prop_changes.patch \
    --verbose
```

**Key properties adapted:**

```ini
# Device identity (from Note 11)
ro.product.device=X6517
ro.product.model=Infinix NOTE 11
ro.product.name=X6517-OP

# Android version (from Hot 30)
ro.build.version.sdk=33
ro.build.version.release=13
ro.build.version.security_patch=2024-11-05

# Build fingerprint (hybrid)
ro.build.fingerprint=Infinix/X6517-OP/X6517:13/TP1A.220624.014/240115V890:user/release-keys
```

#### Vendor Build.prop

```bash
# Adapt vendor build.prop
python3 ../scripts/build_prop_adapter.py \
    --source source/vendor_build.prop \
    --target target/vendor_build.prop \
    --output output/merged/vendor_build.prop \
    --verbose
```

### Step 4.2: Merge Vendor Partition

Create a hybrid vendor partition preserving Note 11 HALs:

```bash
# Create working directory
mkdir -p output/merged/vendor_work
cd output/merged/vendor_work

# Extract source vendor (Hot 30)
mkdir source_vendor
sudo mount -o loop,rw ../../../source/partitions/vendor_a.img source_vendor

# Copy base vendor from source
sudo cp -a source_vendor/* ./

# Overlay critical Note 11 blobs
sudo cp -a ../../../output/vendor_blobs/critical_blobs/* ./

# Copy adapted vendor build.prop
sudo cp ../vendor_build.prop ./build.prop

# Update SELinux contexts
sudo chcon -R u:object_r:vendor_file:s0 .

cd ../../..
```

### Step 4.3: Adapt System Partition

Use Hot 30 system partition with Note 11 device configs:

```bash
mkdir -p output/merged/system_work
cd output/merged/system_work

# Mount source system
mkdir source_system
sudo mount -o loop,rw ../../../source/partitions/system_a.img source_system

# Copy system partition
sudo cp -a source_system/* ./

# Apply build.prop
sudo cp ../system_build.prop ./build.prop

# Apply device identifier substitutions
sudo ../apply_substitutions.sh .

cd ../../..
```

### Step 4.4: Handle Product and System_ext Partitions

```bash
# Product partition - use source (Hot 30) as-is
cp source/partitions/product_a.img output/merged/

# System_ext partition - use source (Hot 30) as-is
cp source/partitions/system_ext_a.img output/merged/
```

### Step 4.5: Merge SELinux Policies

```bash
# Merge SELinux policies from both ROMs
python3 ../scripts/selinux_policy_merger.py \
    --source mnt_source \
    --target mnt_target \
    --output output/selinux_merged \
    --verbose
```

**Apply merged policies to vendor:**

```bash
cd output/merged/vendor_work

# Copy merged SELinux contexts
sudo cp ../../selinux_merged/file_contexts_merged etc/selinux/vendor_file_contexts
sudo cp ../../selinux_merged/property_contexts_merged etc/selinux/vendor_property_contexts
sudo cp ../../selinux_merged/service_contexts_merged etc/selinux/vndservice_contexts

cd ../../..
```

### Step 4.6: Rebuild Partition Images

#### Rebuild Vendor Image

```bash
cd output/merged

# Calculate vendor partition size
VENDOR_SIZE=$(du -sb vendor_work | awk '{print $1}')
VENDOR_SIZE_PADDED=$((VENDOR_SIZE + 52428800))  # Add 50MB padding

# Create ext4 image
sudo mke2fs -t ext4 \
    -L vendor \
    -b 4096 \
    -m 0 \
    -O ^has_journal \
    -J size=0 \
    -I 256 \
    vendor_a_new.img \
    $((VENDOR_SIZE_PADDED / 4096))

# Mount and populate
mkdir mnt_vendor_new
sudo mount -o loop vendor_a_new.img mnt_vendor_new
sudo cp -a vendor_work/* mnt_vendor_new/
sudo umount mnt_vendor_new

# Resize to exact size
sudo e2fsck -fy vendor_a_new.img
sudo resize2fs -M vendor_a_new.img

cd ../..
```

#### Rebuild System Image

```bash
cd output/merged

# Calculate system partition size
SYSTEM_SIZE=$(du -sb system_work | awk '{print $1}')
SYSTEM_SIZE_PADDED=$((SYSTEM_SIZE + 104857600))  # Add 100MB padding

# Create ext4 image
sudo mke2fs -t ext4 \
    -L system \
    -b 4096 \
    -m 0 \
    -O ^has_journal \
    -J size=0 \
    -I 256 \
    system_a_new.img \
    $((SYSTEM_SIZE_PADDED / 4096))

# Mount and populate
mkdir mnt_system_new
sudo mount -o loop system_a_new.img mnt_system_new
sudo cp -a system_work/* mnt_system_new/
sudo umount mnt_system_new

# Resize
sudo e2fsck -fy system_a_new.img
sudo resize2fs -M system_a_new.img

cd ../..
```

---

## Phase 5: Super.img Reconstruction

### Step 5.1: Prepare Partition Images

```bash
cd output/merged

# Use adapted partitions
mv system_a_new.img system_a.img
mv vendor_a_new.img vendor_a.img

# Copy product and system_ext from source
cp ../../source/partitions/product_a.img .
cp ../../source/partitions/system_ext_a.img .

# Create dummy slot B partitions (required for A/B)
dd if=/dev/zero of=system_b.img bs=4k count=1
dd if=/dev/zero of=vendor_b.img bs=4k count=1
dd if=/dev/zero of=product_b.img bs=4k count=1
dd if=/dev/zero of=system_ext_b.img bs=4k count=1

cd ../..
```

### Step 5.2: Calculate Partition Sizes

```bash
cd output/merged

# Get actual sizes
SYSTEM_SIZE=$(stat -c%s system_a.img)
SYSTEM_EXT_SIZE=$(stat -c%s system_ext_a.img)
PRODUCT_SIZE=$(stat -c%s product_a.img)
VENDOR_SIZE=$(stat -c%s vendor_a.img)

# Calculate super partition size (sum + 10% overhead)
SUPER_SIZE=$(( (SYSTEM_SIZE + SYSTEM_EXT_SIZE + PRODUCT_SIZE + VENDOR_SIZE) * 11 / 10 ))

echo "Super partition size: $SUPER_SIZE bytes ($((SUPER_SIZE / 1024 / 1024)) MB)"

cd ../..
```

### Step 5.3: Build Super Image with lpmake

```bash
cd output/merged

# Build super.img with lpmake
lpmake \
    --metadata-size 65536 \
    --super-name super \
    --metadata-slots 3 \
    --device super:$SUPER_SIZE \
    --group main_a:$((SUPER_SIZE / 2)) \
    --group main_b:$((SUPER_SIZE / 2)) \
    --partition system_a:readonly:$SYSTEM_SIZE:main_a \
    --image system_a=./system_a.img \
    --partition system_b:readonly:4096:main_b \
    --image system_b=./system_b.img \
    --partition system_ext_a:readonly:$SYSTEM_EXT_SIZE:main_a \
    --image system_ext_a=./system_ext_a.img \
    --partition system_ext_b:readonly:4096:main_b \
    --image system_ext_b=./system_ext_b.img \
    --partition product_a:readonly:$PRODUCT_SIZE:main_a \
    --image product_a=./product_a.img \
    --partition product_b:readonly:4096:main_b \
    --image product_b=./product_b.img \
    --partition vendor_a:readonly:$VENDOR_SIZE:main_a \
    --image vendor_a=./vendor_a.img \
    --partition vendor_b:readonly:4096:main_b \
    --image vendor_b=./vendor_b.img \
    --sparse \
    --output ../super/super_new.img

cd ../..
```

### Step 5.4: Validate Reconstructed Super Image

```bash
# Validate the new super.img
../scripts/validate_super.sh output/super/super_new.img

# List partitions
../scripts/partition_info.sh output/super/super_new.img
```

### Step 5.5: Prepare Flashable Package

```bash
cd output

mkdir -p flashable
cd flashable

# Copy super.img
cp ../super/super_new.img ./super.img

# Use source boot.img (Hot 30)
cp ../../../source/boot/boot.img ./boot.img

# Create modified vbmeta (disable verification)
cp ../../../source/boot/vbmeta.img ./vbmeta_original.img

# Disable verified boot
avbtool make_vbmeta_image \
    --flags 2 \
    --padding_size 4096 \
    --output vbmeta.img || \
    cp vbmeta_original.img vbmeta.img

cd ../../..
```

---

## Phase 6: Testing & Validation

### Step 6.1: Pre-Flash Checklist

**CRITICAL: Create Backup First!**

```bash
# Boot device to fastboot
adb reboot bootloader

# Backup current partitions
fastboot getvar all > device_info_backup.txt
```

Ensure you have:
- [ ] Stock ROM backup or recovery available
- [ ] Battery > 60%
- [ ] Good quality USB cable
- [ ] Unlocked bootloader

### Step 6.2: Flash Ported ROM

```bash
cd output/flashable

# Use the flash helper script
../../scripts/flash_helper.sh .
```

**Or manual flashing:**

```bash
# Boot to fastboot mode
adb reboot bootloader

# Flash vbmeta (disable verification)
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img
fastboot flash vbmeta_a vbmeta.img
fastboot flash vbmeta_b vbmeta.img

# Flash super partition
fastboot erase super
fastboot flash super super.img

# Flash boot
fastboot flash boot boot.img

# Wipe data (recommended for major Android version upgrade)
fastboot erase userdata
fastboot erase cache

# Reboot
fastboot reboot
```

### Step 6.3: First Boot Monitoring

**First boot will take 5-15 minutes.**

Monitor boot process:

```bash
# In another terminal, watch logcat
adb wait-for-device
adb logcat -v time > first_boot.log
```

**Watch for:**
- SELinux denials: `avc: denied`
- HAL failures: `hwservicemanager`
- Crashes: `FATAL EXCEPTION`

### Step 6.4: Basic Functionality Testing

Once device boots:

#### Display & Touch

```bash
# Test touch
adb shell input tap 500 500

# Check display info
adb shell dumpsys display | grep -i "built-in screen"
```

#### Audio

```bash
# Test speaker
adb shell "media volume --show --stream 3 --set 10"

# Check audio HAL
adb shell "ps -A | grep audio"
```

#### Camera

```bash
# Check camera HAL
adb shell "ps -A | grep camera"
adb shell "dumpsys media.camera"
```

#### WiFi

```bash
# Check WiFi status
adb shell "dumpsys wifi"
```

#### Mobile Data/Telephony

```bash
# Check RIL status
adb shell "dumpsys telephony.registry"
adb shell "getprop | grep ril"
```

#### Sensors

```bash
# List sensors
adb shell "dumpsys sensorservice"
```

### Step 6.5: Comprehensive Testing Checklist

- [ ] Device boots to Android 13
- [ ] Touchscreen responsive
- [ ] Display renders correctly (no artifacts)
- [ ] WiFi connects and stable
- [ ] Bluetooth pairs and works
- [ ] Mobile data/4G works
- [ ] Voice calls work (outgoing/incoming)
- [ ] SMS send/receive works
- [ ] Camera (front/back) works
- [ ] Flashlight works
- [ ] Audio (speaker, earpiece, mic) works
- [ ] Headphone jack/Bluetooth audio works
- [ ] Sensors (accelerometer, gyro, proximity) work
- [ ] Fingerprint sensor works
- [ ] GPS/location works
- [ ] Charging works
- [ ] USB data transfer works
- [ ] Hotspot works
- [ ] Screen rotation works
- [ ] Volume buttons work
- [ ] Power button works

---

## Phase 7: Troubleshooting

### Issue 1: Device Stuck at Bootloader/Fastboot

**Symptoms:**
- Device immediately boots to fastboot
- Cannot boot to system

**Solution:**

```bash
# Reflash boot partition
fastboot flash boot boot.img

# Check boot slot
fastboot getvar current-slot

# Set active slot
fastboot set_active a

# Reboot
fastboot reboot
```

### Issue 2: Bootloop / Stuck on Logo

**Symptoms:**
- Device shows manufacturer logo
- Continuously reboots

**Diagnosis:**

```bash
# Boot to recovery (if available)
# Or use fastboot boot
fastboot boot recovery.img

# Check last_kmsg
adb shell cat /proc/last_kmsg > last_kmsg.log

# Check logcat
adb logcat -d > bootloop.log
```

**Common Causes:**

1. **SELinux enforcement blocking services**

```bash
# Temporary: Set SELinux to permissive
adb root
adb shell setenforce 0

# If this fixes boot, review SELinux denials:
adb shell "dmesg | grep avc"
```

2. **Missing vendor libraries**

Check for HAL crashes:

```bash
adb logcat | grep "hwservicemanager"
adb logcat | grep "android.hardware"
```

Fix: Re-extract vendor partition preserving Note 11 HALs.

3. **Init script failures**

```bash
adb shell dmesg | grep "init:"
```

### Issue 3: No Mobile Network/Calls

**Symptoms:**
- No signal
- IMEI null/unknown
- Cannot make calls

**Solution:**

```bash
# Check RIL daemon
adb shell "ps -A | grep rild"

# Check modem logs
adb logcat -b radio

# Verify IMEI
adb shell "service call iphonesubinfo 1"
```

**Fix:**

1. Ensure target (Note 11) radio libraries are preserved:

```
lib64/libmtk-ril.so
lib64/libratconfig.so
lib64/libc2k*.so
bin/rild
```

2. Check modem firmware:

```bash
adb shell "ls -l /vendor/firmware/modem*"
```

3. Verify APN settings match your carrier.

### Issue 4: Camera Not Working

**Symptoms:**
- Camera app crashes
- Black screen in camera
- "Cannot connect to camera" error

**Solution:**

```bash
# Check camera HAL
adb logcat | grep camera

# Check HAL service
adb shell "ps -A | grep camera"
```

**Fix:**

Preserve ALL Note 11 camera libraries:

```bash
# Critical camera libs
lib64/libcam*.so
lib64/libmtkcam*.so
lib64/lib3a*.so
lib64/hw/camera.provider*.so
```

Ensure SELinux allows camera access:

```bash
adb shell "dmesg | grep camera | grep avc"
```

### Issue 5: Audio Not Working

**Symptoms:**
- No sound from speaker/earpiece
- Microphone not working
- Audio routes incorrect

**Solution:**

```bash
# Check audio HAL
adb logcat | grep audio

# Check audio policy
adb shell "dumpsys media.audio_policy"
```

**Fix:**

1. Preserve Note 11 audio HALs:

```
lib64/hw/audio.primary.mt6769.so
lib64/libaudiocustparam.so
vendor/etc/audio_policy_configuration.xml
```

2. Check audio routing configs:

```bash
adb shell "cat /vendor/etc/mixer_paths.xml"
```

### Issue 6: WiFi Not Working

**Symptoms:**
- WiFi toggle grayed out
- Cannot scan networks
- WiFi crashes

**Solution:**

```bash
# Check WiFi HAL
adb logcat | grep wifi

# Check WiFi firmware
adb shell "ls -l /vendor/firmware/*wifi*"
```

**Fix:**

```bash
# Ensure WiFi firmware from Note 11
/vendor/firmware/WIFI_RAM_CODE_*
/vendor/etc/wifi/wpa_supplicant.conf
```

### Issue 7: SELinux Denials Preventing Services

**Symptoms:**
- Logcat full of `avc: denied`
- Services fail to start
- Features not working

**Solution:**

```bash
# Collect denials
adb shell "dmesg | grep avc | grep denied" > selinux_denials.log

# Analyze denials
grep "avc: denied" selinux_denials.log | \
  sed 's/avc: denied/\n&/g' | \
  sort | uniq -c | sort -rn > denials_summary.txt
```

**Quick Fix (for testing only):**

```bash
# Set SELinux to permissive (NOT for daily use!)
adb root
adb shell setenforce 0
```

**Proper Fix:**

Create additional SELinux rules based on denials and integrate into vendor policy.

### Issue 8: Incorrect Device Information

**Symptoms:**
- Shows wrong device model
- Play Store incompatibility
- Apps detect wrong device

**Solution:**

```bash
# Check device properties
adb shell getprop | grep product
adb shell getprop | grep build
```

**Fix:**

Re-run build.prop adapter ensuring Note 11 identifiers:

```bash
python3 scripts/build_prop_adapter.py \
    --source source/system_build.prop \
    --target target/system_build.prop \
    --output system_build_fixed.prop
```

Rebuild system partition with corrected build.prop.

### Issue 9: Partition Mounting Failures

**Symptoms:**
- System won't mount
- Boot stuck at "Erasing" or "Formatting"

**Solution:**

```bash
# Check partition status via fastboot
fastboot getvar all | grep partition

# Manually erase and reflash
fastboot erase system
fastboot erase vendor
fastboot flash super super.img
```

**Fix:**

Ensure super.img metadata matches device:

```bash
# Verify partition sizes don't exceed device super size
../scripts/partition_info.sh super.img
```

---

## Phase 8: Rollback Procedure

### Emergency: Restore Stock ROM

If ported ROM fails and device won't boot:

#### Method 1: Fastboot Restore

```bash
# Boot to fastboot
# Hold Vol Down + Power while powered off

# Flash stock super.img
fastboot flash super /path/to/stock/super.img

# Flash stock boot
fastboot flash boot /path/to/stock/boot.img

# Flash stock vbmeta
fastboot flash vbmeta /path/to/stock/vbmeta.img

# Wipe data
fastboot erase userdata
fastboot erase cache

# Reboot
fastboot reboot
```

#### Method 2: SP Flash Tool (MTK)

For MediaTek devices:

1. Download SP Flash Tool
2. Download Note 11 stock firmware (scatter file package)
3. Load scatter file in SP Flash Tool
4. Select "Download Only"
5. Connect device in MTK preloader mode (Vol Up + Power)
6. Wait for flash completion

#### Method 3: OTA/Recovery Restore

If custom recovery installed:

1. Boot to recovery (Vol Up + Power)
2. Wipe → Factory Reset
3. Install → Select stock ROM ZIP
4. Flash and reboot

### Backup Best Practices

**Before porting:**

```bash
# Boot to fastboot
adb reboot bootloader

# Save device info
fastboot getvar all > device_info_original.txt

# If possible, backup partitions
mkdir stock_backup
cd stock_backup

fastboot fetch super super_stock.img
fastboot fetch boot boot_stock.img
fastboot fetch vbmeta vbmeta_stock.img
fastboot fetch dtbo dtbo_stock.img
```

Keep these backups safe!

---

## Advanced Topics

### Custom Kernel Integration

To use a custom kernel with ported ROM:

```bash
# Extract kernel from boot.img
unpack_bootimg --boot_img boot.img --out kernel_extracted/

# Replace kernel
mkbootimg \
    --kernel /path/to/custom/kernel \
    --ramdisk kernel_extracted/ramdisk \
    --dtb kernel_extracted/dtb \
    --header_version 2 \
    --os_version 13 \
    --os_patch_level 2024-11 \
    --output boot_custom.img
```

### Performance Tuning

Optimize ported ROM performance:

```bash
# Edit vendor/build.prop
adb pull /vendor/build.prop
nano build.prop

# Add performance tweaks
debug.sf.hw=1
debug.egl.hw=1
debug.composition.type=gpu
persist.sys.ui.hw=1

# Push back
adb push build.prop /vendor/build.prop
```

### OTA Update Support

To enable OTA updates for ported ROM, configure update engine properties in system/build.prop.

---

## Conclusion

You have now successfully ported Android 13 ROM from Infinix Hot 30 to Infinix Note 11. This process involved:

- Extracting and analyzing super partitions
- Identifying and preserving device-specific HALs
- Merging SELinux policies for compatibility
- Adapting build properties
- Reconstructing super.img with hybrid partitions
- Testing and validating the ported ROM

### Further Resources

- **MTK Device Trees:** [github.com/motorolaandroid/device_mediatek_mt6769](https://github.com)
- **SELinux Policy Guide:** [source.android.com/security/selinux](https://source.android.com)
- **Android Build System:** [source.android.com/setup/build](https://source.android.com)

### Community Support

- **XDA Forums:** Infinix Note 11 section
- **Telegram:** Android Porting communities
- **GitHub:** MediaTek device trees

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Tested On:** Infinix Note 11 (X6517)  
**Source ROM:** Infinix Hot 30 Android 13

**DISCLAIMER:** ROM porting involves risks including potential device bricking. Always maintain backups and proceed at your own risk. This guide is for educational purposes.
