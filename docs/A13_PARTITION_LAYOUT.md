# Android 13 Partition Layout for MT6769H Devices

## Overview

Android 13 on MediaTek MT6769H (Helio G88) devices uses **Dynamic Partitions** with **A/B system updates**. All major system partitions are contained within a single `super.img` logical partition.

## Super Partition Structure

### Logical Partition Manager (LPM)

The super partition uses Google's Logical Partition Manager (liblp) to manage multiple logical partitions:

```
┌─────────────────────────────────────────┐
│          SUPER PARTITION                │
│  (Physical partition on eMMC/UFS)       │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   LP Metadata (at offset 4096)    │ │
│  │   - Partition table                │ │
│  │   - Extent allocations             │ │
│  │   - Group information              │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Slot A Partitions                │ │
│  │   ├── system_a                     │ │
│  │   ├── system_ext_a                 │ │
│  │   ├── product_a                    │ │
│  │   └── vendor_a                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Slot B Partitions (minimal)      │ │
│  │   ├── system_b (placeholder)       │ │
│  │   ├── system_ext_b (placeholder)   │ │
│  │   ├── product_b (placeholder)      │ │
│  │   └── vendor_b (placeholder)       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Free Space                       │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Partition Details

### system_a / system_b

**Size:** ~2.0-2.5 GB  
**Filesystem:** ext4 / erofs (read-only)  
**Mount Point:** `/system`

**Contents:**
- Android framework (`/framework/`)
- System applications (`/app/`, `/priv-app/`)
- Core libraries (`/lib64/`, `/lib/`)
- Fonts, media, resources
- System binaries (`/bin/`)

**Key Directories:**
```
/system/
├── app/                    # System apps
├── priv-app/               # Privileged apps
├── framework/              # Android framework JARs
├── lib64/                  # 64-bit libraries
├── lib/                    # 32-bit libraries
├── bin/                    # System binaries
├── etc/                    # System configuration
│   ├── permissions/
│   ├── selinux/
│   └── vintf/
├── fonts/
├── media/
└── build.prop              # System properties
```

**Critical Files:**
- `build.prop` - System build properties
- `etc/vintf/manifest.xml` - HAL interface manifest
- `etc/selinux/plat_*` - Platform SELinux policy

### system_ext_a / system_ext_b

**Size:** ~300-600 MB  
**Filesystem:** ext4 / erofs (read-only)  
**Mount Point:** `/system_ext`

**Purpose:** System extensions - OEM customizations that extend the base system

**Contents:**
- Additional system apps
- Extended framework components
- OEM-specific system libraries

**Key Directories:**
```
/system_ext/
├── app/
├── priv-app/
├── framework/
├── lib64/
├── lib/
└── etc/
```

### product_a / product_b

**Size:** ~200-500 MB  
**Filesystem:** ext4 / erofs (read-only)  
**Mount Point:** `/product`

**Purpose:** Product-specific customizations (OEM branding, regional variants)

**Contents:**
- OEM applications
- Regional apps and content
- Carrier apps
- Product-specific overlays

**Key Directories:**
```
/product/
├── app/                    # Product apps
├── priv-app/
├── overlay/                # Runtime Resource Overlays (RROs)
├── media/
├── etc/
│   └── permissions/
└── build.prop
```

### vendor_a / vendor_b

**Size:** ~300-800 MB  
**Filesystem:** ext4 (read-write on first boot, then read-only)  
**Mount Point:** `/vendor`

**Purpose:** Hardware-specific binaries, libraries, and configuration

**Contents:**
- HAL implementations (Hardware Abstraction Layer)
- Device-specific libraries
- Firmware blobs
- Kernel modules
- Hardware configuration files

**Critical Structure:**
```
/vendor/
├── bin/                    # Hardware binaries
│   ├── hw/                 # HAL binaries
│   ├── mtk_agpsd           # GPS daemon
│   └── rild                # Radio Interface Layer daemon
├── lib64/                  # 64-bit vendor libs
│   ├── hw/                 # HAL libraries
│   │   ├── audio.primary.mt6769.so
│   │   ├── camera.provider@2.6-impl-mediatek.so
│   │   ├── gralloc.mt6769.so
│   │   ├── hwcomposer.mt6769.so
│   │   └── sensors.mt6769.so
│   ├── libmtk*.so          # MediaTek libraries
│   ├── libcam*.so          # Camera libraries
│   └── libGLES_mali.so     # GPU driver
├── lib/                    # 32-bit vendor libs
├── etc/
│   ├── audio_policy_configuration.xml
│   ├── init/               # Init scripts
│   ├── selinux/            # Vendor SELinux policy
│   │   ├── vendor_file_contexts
│   │   ├── vendor_property_contexts
│   │   └── vendor_seapp_contexts
│   ├── permissions/
│   └── vintf/
│       └── manifest.xml    # Vendor HAL manifest
├── firmware/               # Hardware firmware
│   ├── WIFI_RAM_CODE_*
│   ├── bt_fw_*
│   └── modem_*
├── overlay/
└── build.prop              # Vendor properties
```

**Device-Specific Categories in Vendor:**

#### Audio HALs
```
lib64/hw/audio.primary.mt6769.so
lib64/libaudiocustparam.so
lib64/libaudiotoolkit.so
etc/audio_policy_configuration.xml
etc/audio_effects.xml
```

#### Camera HALs
```
lib64/hw/camera.provider@2.6-impl-mediatek.so
lib64/libmtkcam_*.so
lib64/libcam*.so
lib64/lib3a*.so
```

#### Display/Graphics HALs
```
lib64/hw/hwcomposer.mt6769.so
lib64/hw/gralloc.mt6769.so
lib64/libGLES_mali.so
lib64/egl/libGLES_mali.so
lib64/vulkan.mt6769.so
```

#### Radio/Modem HALs
```
lib64/libmtk-ril.so
lib64/libratconfig.so
lib64/libc2kril.so
bin/rild
```

#### Sensors HAL
```
lib64/hw/sensors.mt6769.so
lib64/libhwm.so
```

#### GPS HAL
```
bin/mtk_agpsd
lib64/hw/gps.mt6769.so
lib64/libmnl.so
```

## Partition Groups

Android 13 uses partition groups to manage storage:

### main_a Group
Contains all slot A partitions:
- system_a
- system_ext_a
- product_a
- vendor_a

**Max Size:** ~50% of super partition

### main_b Group
Contains all slot B partitions (usually minimal):
- system_b (placeholder, ~4KB)
- system_ext_b (placeholder, ~4KB)
- product_b (placeholder, ~4KB)
- vendor_b (placeholder, ~4KB)

**Max Size:** ~50% of super partition

## A/B Partition Scheme

### Active vs Inactive Slots

**Slot A (Primary):**
- Contains full Android 13 system
- Used for normal operation
- Updated during OTA to slot B

**Slot B (Secondary/Update):**
- Usually contains minimal placeholders
- Receives OTA updates while slot A is active
- Becomes active after successful update

### Boot Partitions (Outside Super)

These partitions exist separately from super:

```
boot_a / boot_b          # Kernel + ramdisk
dtbo_a / dtbo_b          # Device tree overlay
vbmeta_a / vbmeta_b      # Verified boot metadata
vendor_boot_a / vendor_boot_b  # Vendor ramdisk (Android 11+)
```

## Physical Partition Layout (eMMC/UFS)

Complete partition table for MT6769H devices:

```
┌────────────────────┬──────────┬────────────────────────┐
│ Partition          │ Size     │ Purpose                │
├────────────────────┼──────────┼────────────────────────┤
│ preloader          │ 512KB    │ Bootloader             │
│ pgpt               │ 512KB    │ GUID Partition Table   │
│ boot_para          │ 1MB      │ Boot parameters        │
│ recovery           │ 40MB     │ Recovery ramdisk       │
│ misc               │ 1MB      │ Misc data              │
│ vbmeta_a           │ 1MB      │ Verified boot A        │
│ vbmeta_b           │ 1MB      │ Verified boot B        │
│ boot_a             │ 40MB     │ Kernel/ramdisk A       │
│ boot_b             │ 40MB     │ Kernel/ramdisk B       │
│ dtbo_a             │ 8MB      │ Device tree overlay A  │
│ dtbo_b             │ 8MB      │ Device tree overlay B  │
│ vendor_boot_a      │ 32MB     │ Vendor ramdisk A       │
│ vendor_boot_b      │ 32MB     │ Vendor ramdisk B       │
│ super              │ 6-9GB    │ Logical partitions     │
│ userdata           │ Remaining│ User data              │
│ metadata           │ 2MB      │ Encryption metadata    │
└────────────────────┴──────────┴────────────────────────┘
```

## Mount Points at Runtime

```
/           → rootfs (tmpfs)
/system     → /dev/block/mapper/system_a
/vendor     → /dev/block/mapper/vendor_a
/product    → /dev/block/mapper/product_a
/system_ext → /dev/block/mapper/system_ext_a
/data       → /dev/block/by-name/userdata
/cache      → /dev/block/by-name/cache (if exists)
/metadata   → /dev/block/by-name/metadata
```

## Filesystem Types

### ext4
- Traditional Linux filesystem
- Used for: system, vendor, product (on some builds)
- Read-write capable
- Journaling support

### erofs (Enhanced Read-Only File System)
- Newer read-only filesystem (Android 11+)
- Used for: system, system_ext, product (on newer builds)
- Better compression (saves ~30% space)
- Faster mount times
- Lower memory usage

### f2fs (Flash-Friendly File System)
- Optimized for flash storage
- Used for: userdata, cache
- Wear-leveling
- TRIM support

## LPM Metadata Structure

Location: Offset 4096 in super.img

### Metadata Geometry (at offset 4096)
```c
struct LpMetadataGeometry {
    uint32_t magic;              // 0x67446C41 ("gDLA")
    uint32_t struct_size;
    uint8_t checksum[32];
    uint32_t metadata_max_size;
    uint32_t metadata_slot_count;
    uint32_t logical_block_size;
};
```

### Metadata Header (at offset 8192)
```c
struct LpMetadataHeader {
    uint32_t magic;              // 0x414C5030 ("ALP0")
    uint16_t major_version;
    uint16_t minor_version;
    uint32_t header_size;
    uint8_t header_checksum[32];
    uint32_t tables_size;
    uint8_t tables_checksum[32];
};
```

### Partition Descriptors
```c
struct LpMetadataPartition {
    char name[36];
    uint32_t attributes;         // READONLY, SLOT_SUFFIXED
    uint32_t first_extent_index;
    uint32_t num_extents;
    uint32_t group_index;
};
```

## Partition Attributes

- `READONLY` (0x1): Partition is read-only
- `SLOT_SUFFIXED` (0x2): Partition has _a/_b suffix
- `UPDATED` (0x4): Partition was updated (for OTA)

## Typical Partition Sizes

### Infinix Hot 30 (Source)
```
system_a:      2200 MB
system_ext_a:   550 MB
product_a:      450 MB
vendor_a:       600 MB
Total (slot A): 3800 MB
```

### Infinix Note 11 (Target)
```
system_a:      2000 MB
system_ext_a:   480 MB
product_a:      380 MB
vendor_a:       550 MB
Total (slot A): 3410 MB
```

## Resizing Considerations for ROM Porting

When porting between devices:

1. **Super partition must be large enough** to hold all merged partitions
2. **Group size limits** - Each group (main_a, main_b) has a maximum size
3. **Individual partition sizes** can be adjusted, but total must fit in group
4. **Leave headroom** (~10-15%) for OTA updates

## Command Reference

### Extract Super Partitions
```bash
lpunpack super.img output_dir/
```

### List Partitions
```bash
lpunpack -p super.img
```

### Create Super Image
```bash
lpmake --metadata-size 65536 \
       --super-name super \
       --device super:9126805504 \
       --metadata-slots 3 \
       --group main_a:4563402752 \
       --partition system_a:readonly:2307129344:main_a \
       --image system_a=./system_a.img \
       ...
       --output super_new.img
```

### Resize Partition Image
```bash
# Check filesystem
e2fsck -fy system_a.img

# Resize to minimum
resize2fs -M system_a.img

# Resize to specific size (in 4K blocks)
resize2fs system_a.img 512000
```

## Security Considerations

### Verified Boot (AVB)
- Each partition has dm-verity hash tree
- Stored in vbmeta partition
- Can be disabled for development: `fastboot --disable-verification flash vbmeta vbmeta.img`

### SELinux Contexts
- Each partition has file_contexts
- Must be preserved during porting
- Located in `/vendor/etc/selinux/` and `/system/etc/selinux/`

## References

- [Android Dynamic Partitions](https://source.android.com/devices/tech/ota/dynamic_partitions)
- [Logical Partition Manager](https://android.googlesource.com/platform/system/core/+/refs/heads/master/fs_mgr/liblp/)
- [MediaTek Platform Guide](https://www.mediatek.com/)
