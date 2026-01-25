# Android 13 ROM Porting Toolkit

**Version:** 1.0  
**Target:** Infinix Hot 30 (A13) → Infinix Note 11 (A12 → A13)  
**SoC:** MediaTek MT6769H (Helio G88)  
**Partition Type:** Dynamic A/B Super Partitions

---

## 📋 Overview

This comprehensive toolkit provides everything needed to port Android 13 ROM from Infinix Hot 30 to Infinix Note 11. It includes Python tools for ROM extraction/analysis, bash utilities for validation/flashing, complete documentation, and configuration templates.

## 🎯 What's Included

### Python Tools (`scripts/`)

1. **super_img_extractor.py** - Extract and parse super.img with A/B partition support
2. **partition_analyzer.py** - Compare partitions and identify device-specific files
3. **build_prop_adapter.py** - Adapt build.prop files for target device
4. **vendor_blob_extractor.py** - Extract and categorize vendor HALs/drivers
5. **device_tree_extractor.py** - Extract and compare device tree overlays
6. **selinux_policy_merger.py** - Merge SELinux policies from both ROMs
7. **metadata_mapper.py** - Map device identifiers and hardware configs

### Bash Utilities (`scripts/`)

1. **setup_env.sh** - Validate dependencies and setup working directories
2. **flash_helper.sh** - Helper for flashing via fastboot/ADB
3. **validate_super.sh** - Validate super.img integrity
4. **partition_info.sh** - Print detailed partition information

### Documentation (`docs/`)

1. **A13_PARTITION_LAYOUT.md** - Android 13 partition structure for MT6769H
2. **VENDOR_BLOB_REFERENCE.md** - Device-specific vs SoC-specific blob guide
3. **DEVICETREE_GUIDE.md** - Device tree overlay extraction and comparison
4. **SELINUX_MAPPING.md** - SELinux policy handling for A12→A13 upgrade
5. **SUPER_IMG_FORMAT.md** - Technical breakdown of super.img format

### Guides

1. **PORTING_GUIDE.md** - Complete step-by-step ROM porting guide

### Configuration Templates (`config/`)

1. **note11_device_info.template** - Device identifiers and properties
2. **selinux_rules.template** - SELinux compatibility rules
3. **build.prop.patch** - Detailed build.prop changes reference

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Run environment setup
cd scripts/
./setup_env.sh rom_porting_workspace

# This will:
# - Check Python 3.8+ and required tools
# - Create workspace directory structure
# - Validate system requirements
```

### 2. Place ROM Files

```bash
cd rom_porting_workspace/

# Copy source ROM (Hot 30 - Android 13)
cp /path/to/hot30/super.img source/super/
cp /path/to/hot30/boot.img source/boot/

# Copy target ROM (Note 11 - Android 12)
cp /path/to/note11/super.img target/super/
cp /path/to/note11/boot.img target/boot/
```

### 3. Extract and Analyze

```bash
# Quick extraction
./quick_extract.sh

# Quick analysis
./analyze.sh
```

### 4. Follow Complete Guide

See **[PORTING_GUIDE.md](PORTING_GUIDE.md)** for detailed step-by-step instructions.

---

## 📚 Detailed Tool Usage

### Super Image Extraction

```bash
python3 scripts/super_img_extractor.py \
    --super source/super/super.img \
    --output source/partitions \
    --info source/partition_info.json \
    --verbose
```

**Output:**
- Individual partition images (system_a.img, vendor_a.img, etc.)
- Partition information JSON
- Filesystem type detection

### Partition Analysis

```bash
python3 scripts/partition_analyzer.py \
    --source source/partitions \
    --target target/partitions \
    --output output/analysis \
    --verbose
```

**Output:**
- Analysis report with file differences
- Device-specific file categorization
- Migration recommendations

### Build.prop Adaptation

```bash
python3 scripts/build_prop_adapter.py \
    --source source/system_build.prop \
    --target target/system_build.prop \
    --output adapted_build.prop \
    --patch changes.patch \
    --verbose
```

**Output:**
- Adapted build.prop with correct device identifiers
- Patch file showing all changes
- Compatibility report

### Vendor Blob Extraction

```bash
python3 scripts/vendor_blob_extractor.py \
    --vendor target/vendor_mount \
    --output vendor_blobs \
    --device note11 \
    --extract-critical \
    --generate-files \
    --verbose
```

**Output:**
- Categorized vendor blobs (audio, camera, radio, etc.)
- Critical device-specific HALs
- proprietary-files.txt for device tree
- Android.mk for blob integration

### Device Tree Extraction

```bash
# Extract DTB from boot.img
python3 scripts/device_tree_extractor.py \
    --boot boot.img \
    --output dtb_extracted \
    --decompile \
    --verbose

# Compare device trees
python3 scripts/device_tree_extractor.py \
    --compare source.dts target.dts \
    --diff dt_differences.patch
```

**Output:**
- Extracted DTB files
- Decompiled DTS source
- Difference patch file

### SELinux Policy Merging

```bash
python3 scripts/selinux_policy_merger.py \
    --source source/partitions \
    --target target/partitions \
    --output selinux_merged \
    --verbose
```

**Output:**
- Merged file_contexts
- Merged property_contexts
- Merged service_contexts
- Additional compatibility rules

### Device Metadata Mapping

```bash
python3 scripts/metadata_mapper.py \
    --source source/partitions \
    --target target/partitions \
    --output device_mapping.json \
    --script apply_substitutions.sh \
    --verbose
```

**Output:**
- Complete device mapping JSON
- Hardware compatibility report
- Substitution bash script

---

## 🛠️ Bash Utilities

### Environment Setup

```bash
./scripts/setup_env.sh workspace_dir
```

Validates dependencies and creates workspace structure.

### Super Image Validation

```bash
./scripts/validate_super.sh super.img
```

Checks:
- File size and format
- Sparse vs raw format
- LP metadata validity
- Partition integrity

### Partition Information

```bash
./scripts/partition_info.sh super.img
```

Displays:
- Metadata geometry
- Partition list with sizes
- A/B slot configuration
- Extraction commands

### Flashing Helper

```bash
./scripts/flash_helper.sh rom_directory
```

Interactive flashing with:
- Device detection
- Backup creation
- Progressive flashing
- Safety confirmations

---

## 📖 Documentation Guide

### 1. Start Here: PORTING_GUIDE.md

The main guide covers:
- Prerequisites and setup
- Phase-by-phase porting process
- Testing and validation
- Troubleshooting common issues
- Rollback procedures

### 2. Technical References

**A13_PARTITION_LAYOUT.md**
- Super partition structure
- Logical partition manager details
- A/B partition scheme
- Filesystem types

**VENDOR_BLOB_REFERENCE.md**
- Device-specific vs SoC-specific blobs
- Critical HALs to preserve
- Categorized blob lists
- Porting decision matrix

**DEVICETREE_GUIDE.md**
- Device tree structure
- Extraction methods
- DTB/DTBO handling
- Comparison techniques

**SELINUX_MAPPING.md**
- Android 12 → 13 policy changes
- Common denials and solutions
- Policy merging strategies
- Testing procedures

**SUPER_IMG_FORMAT.md**
- Binary format specifications
- Metadata structure
- Creating super images
- Validation techniques

---

## ⚙️ Configuration Templates

### Device Info Template

Edit `config/note11_device_info.template`:

```bash
DEVICE_CODENAME=X6517
DEVICE_MODEL="Infinix NOTE 11"
SOC_MODEL=MT6769H
RAM_SIZE=6144
DISPLAY_DENSITY=480
# ... etc
```

### SELinux Rules

Use `config/selinux_rules.template` as base for additional SELinux rules needed for compatibility.

### Build.prop Patch

Reference `config/build.prop.patch` to see exact changes needed in build.prop files.

---

## 🎯 Typical Workflow

```
1. Setup Environment
   └─> ./scripts/setup_env.sh workspace

2. Place ROM Files
   └─> Copy source and target ROMs to workspace

3. Extract Super Images
   └─> Use super_img_extractor.py

4. Analyze Differences
   └─> Use partition_analyzer.py

5. Extract Vendor Blobs
   └─> Use vendor_blob_extractor.py on target vendor

6. Adapt Build Props
   └─> Use build_prop_adapter.py

7. Merge SELinux Policies
   └─> Use selinux_policy_merger.py

8. Merge Partitions
   └─> Manually merge based on analysis

9. Rebuild Super Image
   └─> Use lpmake to reconstruct

10. Flash and Test
    └─> Use flash_helper.sh

11. Troubleshoot
    └─> Refer to PORTING_GUIDE.md Phase 7
```

---

## 🔧 System Requirements

### Software

- **Python:** 3.8 or higher
- **Android Tools:** adb, fastboot
- **LP Tools:** lpunpack, lpmake
- **Sparse Tools:** simg2img, img2simg
- **Filesystem Tools:** mke2fs, e2fsck, resize2fs
- **Device Tree Tools:** dtc (optional but recommended)

### Hardware

- **PC:** 8GB+ RAM recommended
- **Storage:** 50GB+ free space
- **USB:** Quality USB cable for device connection
- **Target Device:** Infinix Note 11 with unlocked bootloader

### Installation (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
    python3 python3-pip \
    android-sdk-platform-tools \
    android-sdk-libsparse-utils \
    android-tools-adb android-tools-fastboot \
    e2fsprogs f2fs-tools \
    device-tree-compiler \
    brotli lz4 zstd
```

---

## ⚠️ Important Warnings

### Before You Start

1. **Backup Everything:** Always maintain a complete backup of your device
2. **Unlocked Bootloader Required:** Target device must have unlocked bootloader
3. **Risk of Bricking:** ROM porting can brick devices if done incorrectly
4. **Test Incrementally:** Test each phase before proceeding
5. **IMEI Protection:** Never modify or flash over IMEI/EFS partitions

### Critical Partitions

**DO NOT MODIFY:**
- `nvram` - Contains IMEI and calibration data
- `nvdata` - Contains IMEI backup
- `protect1` / `protect2` - Protected data
- `persist` - Persistent data
- `metadata` - Encryption metadata

**Safe to Modify:**
- `super` (contains system, vendor, product, system_ext)
- `boot` - Kernel and ramdisk
- `vbmeta` - Verified boot metadata
- `dtbo` - Device tree overlays

---

## 🐛 Troubleshooting

### Common Issues

1. **Device won't boot**
   - Check PORTING_GUIDE.md Phase 7, Issue 2
   - Try booting with target device boot.img first

2. **No mobile network**
   - Ensure target device radio HALs are preserved
   - Check VENDOR_BLOB_REFERENCE.md radio section

3. **Camera doesn't work**
   - Preserve ALL target camera HALs
   - See VENDOR_BLOB_REFERENCE.md camera section

4. **SELinux denials blocking services**
   - Set to permissive temporarily
   - Check SELINUX_MAPPING.md for solutions

5. **Super.img won't flash**
   - Validate with validate_super.sh
   - Check if sparse format needs conversion

### Getting Help

1. Check PORTING_GUIDE.md troubleshooting section
2. Review relevant documentation in docs/
3. Enable verbose logging in scripts with `--verbose`
4. Collect logs: `adb logcat > bootlog.txt`

---

## 📝 Development Notes

### Testing

All tools have been designed with:
- Verbose output mode for debugging
- Safe defaults (read-only operations where possible)
- Clear error messages
- Validation before destructive operations

### Extending

To add support for other devices:

1. Update `note11_device_info.template` with new device specs
2. Modify `VENDOR_BLOB_REFERENCE.md` for new SoC if different
3. Test partition_analyzer.py on new device partitions
4. Adjust SELinux rules as needed

---

## 🤝 Contributing

This toolkit is designed for the specific Infinix Hot 30 → Note 11 porting scenario but can be adapted for similar devices.

To adapt for other devices:
1. Update configuration templates
2. Modify device-specific patterns in Python tools
3. Update documentation with device-specific info
4. Test thoroughly

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

- **Android Open Source Project** - For dynamic partitions and liblp
- **MediaTek** - For MT6769H platform
- **Community Contributors** - For ROM porting knowledge

---

## 📞 Support

For issues specific to this toolkit:
1. Check documentation thoroughly
2. Review PORTING_GUIDE.md troubleshooting
3. Ensure all prerequisites are met

For general Android ROM porting:
- XDA Forums
- Android AOSP documentation
- MediaTek developer resources

---

## ⚖️ Disclaimer

**This toolkit is for educational purposes.** ROM porting involves risks including potential device bricking, data loss, and warranty voidance. Always:

- Maintain complete backups
- Understand what each step does
- Test in safe environment
- Proceed at your own risk

The authors assume no responsibility for damaged devices, lost data, or any other issues arising from use of this toolkit.

---

**Happy Porting! 🚀**

---

## 📚 Quick Reference

### File Structure

```
.
├── PORTING_GUIDE.md           # Main porting guide
├── ROM_PORTING_TOOLKIT_README.md  # This file
├── scripts/
│   ├── super_img_extractor.py
│   ├── partition_analyzer.py
│   ├── build_prop_adapter.py
│   ├── vendor_blob_extractor.py
│   ├── device_tree_extractor.py
│   ├── selinux_policy_merger.py
│   ├── metadata_mapper.py
│   ├── setup_env.sh
│   ├── flash_helper.sh
│   ├── validate_super.sh
│   └── partition_info.sh
├── docs/
│   ├── A13_PARTITION_LAYOUT.md
│   ├── VENDOR_BLOB_REFERENCE.md
│   ├── DEVICETREE_GUIDE.md
│   ├── SELINUX_MAPPING.md
│   └── SUPER_IMG_FORMAT.md
└── config/
    ├── note11_device_info.template
    ├── selinux_rules.template
    └── build.prop.patch
```

### Key Commands

```bash
# Setup
./scripts/setup_env.sh workspace

# Validate
./scripts/validate_super.sh super.img
./scripts/partition_info.sh super.img

# Extract
python3 scripts/super_img_extractor.py --super super.img --output partitions/ -v

# Analyze
python3 scripts/partition_analyzer.py --source src/ --target tgt/ --output analysis/ -v

# Adapt
python3 scripts/build_prop_adapter.py --source src.prop --target tgt.prop --output out.prop -v

# Flash
./scripts/flash_helper.sh rom_directory
```

---

**Version 1.0** | **Last Updated:** January 2025 | **Platform:** MT6769H (Helio G88)
