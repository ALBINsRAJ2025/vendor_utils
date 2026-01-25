# Super.img Format Technical Reference

## Overview

The `super.img` file contains multiple logical partitions managed by Android's Logical Partition Manager (liblp). This document details the binary format and structure.

## File Structure

```
┌─────────────────────────────────────────────────────────┐
│ Offset 0: Primary GPT Header (optional, legacy)        │ 512 bytes
├─────────────────────────────────────────────────────────┤
│ Offset 512: GPT Partition Entries (optional)           │ Variable
├─────────────────────────────────────────────────────────┤
│ Offset 4096: LP Metadata Geometry                      │ 4096 bytes
├─────────────────────────────────────────────────────────┤
│ Offset 8192: LP Primary Metadata (Slot 0)              │ 64 KB (default)
├─────────────────────────────────────────────────────────┤
│ Offset 73728: LP Backup Metadata (Slot 1)              │ 64 KB
├─────────────────────────────────────────────────────────┤
│ Offset 139264: LP Backup Metadata (Slot 2)             │ 64 KB
├─────────────────────────────────────────────────────────┤
│ Offset 204800: Partition Data Start                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Extent 0: system_a (part of data)              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Extent 1: vendor_a (part of data)              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Extent 2: system_ext_a (part of data)          │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Extent 3: product_a (part of data)             │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Extent 4-7: Slot B partitions (minimal)        │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Free space                                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## LP Metadata Geometry

**Location:** Offset 4096  
**Size:** 4096 bytes max

### Structure (C)

```c
struct LpMetadataGeometry {
    uint32_t magic;              /* 0x67446C41 ("gDLA") */
    uint32_t struct_size;        /* sizeof(LpMetadataGeometry) */
    uint8_t checksum[32];        /* SHA256 of remaining bytes */
    uint32_t metadata_max_size;  /* Maximum metadata size (65536) */
    uint32_t metadata_slot_count;/* Number of metadata slots (2-3) */
    uint32_t logical_block_size; /* Logical block size (4096) */
} __attribute__((packed));
```

### Example Values

```
magic: 0x67446C41 (1735127105 decimal)
struct_size: 4096
checksum: [32 bytes SHA256]
metadata_max_size: 65536 (64 KB)
metadata_slot_count: 3
logical_block_size: 4096
```

### Hex Dump Example

```
00001000: 41 6C 44 67 00 10 00 00  [checksum 32 bytes...]
00001020: ...
00001030: 00 00 01 00 03 00 00 00  00 10 00 00
          ^metadata  ^slots    ^block size
           max size
```

## LP Metadata Header

**Location:** Offset 8192 (slot 0), 73728 (slot 1), 139264 (slot 2)  
**Size:** Metadata max size (typically 64 KB)

### Structure (C)

```c
struct LpMetadataHeader {
    uint32_t magic;              /* 0x414C5030 ("ALP0") */
    uint16_t major_version;      /* 10 for Android 10+, 13 for Android 13 */
    uint16_t minor_version;      /* 0, 1, 2 */
    uint32_t header_size;        /* sizeof(LpMetadataHeader) */
    uint8_t header_checksum[32]; /* SHA256 of header */
    uint32_t tables_size;        /* Size of all tables */
    uint8_t tables_checksum[32]; /* SHA256 of tables */
    
    /* Table descriptors */
    struct {
        uint32_t offset;         /* Offset from start of metadata */
        uint32_t num_entries;    /* Number of entries */
        uint32_t entry_size;     /* Size of each entry */
    } partitions;
    
    struct {
        uint32_t offset;
        uint32_t num_entries;
        uint32_t entry_size;
    } extents;
    
    struct {
        uint32_t offset;
        uint32_t num_entries;
        uint32_t entry_size;
    } groups;
    
    struct {
        uint32_t offset;
        uint32_t num_entries;
        uint32_t entry_size;
    } block_devices;
} __attribute__((packed));
```

### Version History

- **10.0:** Android 10 (initial dynamic partitions)
- **10.1:** Added virtual A/B support
- **10.2:** Enhanced metadata
- **13.0:** Android 13 enhancements

## Metadata Tables

### Partition Table

**Entry Structure:**

```c
struct LpMetadataPartition {
    char name[36];               /* Partition name (e.g., "system_a") */
    uint32_t attributes;         /* Attribute flags */
    uint32_t first_extent_index; /* Index of first extent */
    uint32_t num_extents;        /* Number of extents */
    uint32_t group_index;        /* Partition group index */
} __attribute__((packed));
```

**Attributes:**

```c
#define LP_PARTITION_ATTR_NONE          0x0
#define LP_PARTITION_ATTR_READONLY      0x1  /* Read-only partition */
#define LP_PARTITION_ATTR_SLOT_SUFFIXED 0x2  /* Has _a or _b suffix */
#define LP_PARTITION_ATTR_UPDATED       0x4  /* Was updated (for OTA) */
#define LP_PARTITION_ATTR_DISABLED      0x8  /* Partition is disabled */
```

**Example Entry:**

```
name: "system_a"
attributes: 0x3 (READONLY | SLOT_SUFFIXED)
first_extent_index: 0
num_extents: 1
group_index: 0
```

### Extent Table

**Entry Structure:**

```c
struct LpMetadataExtent {
    uint64_t num_sectors;        /* Number of 512-byte sectors */
    uint32_t target_type;        /* Type of target */
    uint64_t target_data;        /* Target-specific data */
    uint32_t target_source;      /* Source block device index */
} __attribute__((packed));
```

**Target Types:**

```c
#define LP_TARGET_TYPE_ZERO    0  /* All zeros */
#define LP_TARGET_TYPE_LINEAR  1  /* Linear mapping */
```

**Example Entry (Linear):**

```
num_sectors: 4194304 (2GB in sectors)
target_type: 1 (LINEAR)
target_data: 524288 (physical sector offset)
target_source: 0 (super device)
```

### Group Table

**Entry Structure:**

```c
struct LpMetadataPartitionGroup {
    char name[36];               /* Group name (e.g., "main_a") */
    uint32_t flags;              /* Reserved */
    uint64_t maximum_size;       /* Maximum size in bytes */
} __attribute__((packed));
```

**Example Entry:**

```
name: "main_a"
flags: 0
maximum_size: 4563402752 (4.25 GB)
```

### Block Device Table

**Entry Structure:**

```c
struct LpMetadataBlockDevice {
    uint64_t first_logical_sector; /* First usable sector */
    uint64_t alignment;            /* Partition alignment */
    uint64_t alignment_offset;     /* Alignment offset */
    uint64_t size;                 /* Size in bytes */
    char partition_name[36];       /* Physical partition name */
    uint32_t flags;                /* Flags */
} __attribute__((packed));
```

**Example Entry:**

```
first_logical_sector: 400 (starts at 204800 bytes)
alignment: 1048576 (1 MB alignment)
alignment_offset: 0
size: 9126805504 (8.5 GB)
partition_name: "super"
flags: 0
```

## Sparse Image Format

Super images are often in Android sparse format for efficient storage.

### Sparse Header

```c
typedef struct sparse_header {
    uint32_t magic;              /* 0xED26FF3A */
    uint16_t major_version;      /* Major version (1) */
    uint16_t minor_version;      /* Minor version (0) */
    uint16_t file_hdr_sz;        /* 28 bytes */
    uint16_t chunk_hdr_sz;       /* 12 bytes */
    uint32_t blk_sz;             /* Block size (4096) */
    uint32_t total_blks;         /* Total blocks in output */
    uint32_t total_chunks;       /* Number of chunks */
    uint32_t image_checksum;     /* CRC32 checksum */
} __attribute__((packed));
```

### Chunk Header

```c
typedef struct chunk_header {
    uint16_t chunk_type;         /* Chunk type */
    uint16_t reserved1;
    uint32_t chunk_sz;           /* Chunk size in blocks */
    uint32_t total_sz;           /* Total size including header */
} __attribute__((packed));
```

**Chunk Types:**

```c
#define CHUNK_TYPE_RAW       0xCAC1  /* Raw data */
#define CHUNK_TYPE_FILL      0xCAC2  /* Fill with pattern */
#define CHUNK_TYPE_DONT_CARE 0xCAC3  /* Don't care (skip) */
#define CHUNK_TYPE_CRC32     0xCAC4  /* CRC32 chunk */
```

### Sparse to Raw Conversion

```bash
# Using simg2img
simg2img super.img super_raw.img

# Manual check if sparse
hexdump -C super.img -n 4
# If shows: 3a ff 26 ed → Sparse format
# If shows: 41 6c 44 67 → Raw format (at offset 4096)
```

## Practical Examples

### Example 1: Read Metadata Geometry

```python
import struct

with open('super.img', 'rb') as f:
    f.seek(4096)
    geometry_data = f.read(4096)
    
    magic, struct_size = struct.unpack('<II', geometry_data[:8])
    
    print(f"Magic: 0x{magic:08x}")
    if magic == 0x67446C41:
        print("Valid LP metadata geometry")
    
    # Skip checksum (32 bytes)
    f.seek(4096 + 8 + 32)
    metadata_max_size, slot_count, block_size = struct.unpack('<III', f.read(12))
    
    print(f"Metadata max size: {metadata_max_size}")
    print(f"Metadata slots: {slot_count}")
    print(f"Logical block size: {block_size}")
```

### Example 2: Read Partition Names

```python
import struct

with open('super.img', 'rb') as f:
    # Read metadata header
    f.seek(8192)
    header_magic = struct.unpack('<I', f.read(4))[0]
    
    if header_magic != 0x414C5030:
        print("Invalid metadata header")
        exit(1)
    
    # Skip to partition table descriptor
    f.seek(8192 + 80)  # Partition table offset in header
    part_offset, part_num, part_size = struct.unpack('<III', f.read(12))
    
    # Read partition table
    f.seek(8192 + part_offset)
    
    for i in range(part_num):
        part_data = f.read(part_size)
        part_name = part_data[:36].decode('utf-8').rstrip('\x00')
        attributes, first_extent, num_extents, group_idx = struct.unpack('<IIII', part_data[36:52])
        
        print(f"Partition: {part_name}")
        print(f"  Attributes: 0x{attributes:x}")
        print(f"  Extents: {num_extents}")
```

### Example 3: Calculate Partition Size

```bash
# Using lpunpack
lpunpack -p super.img | grep -A5 "Name: system_a"

# Output:
# Name: system_a
# Group: main_a
# Attr: readonly
# Extent 1: 4194304 sectors (2048 MB)
```

## Creating Super Images

### Using lpmake

```bash
lpmake \
    --metadata-size 65536 \
    --super-name super \
    --metadata-slots 3 \
    --device super:9663676416 \
    --group main_a:4831838208 \
    --group main_b:4831838208 \
    --partition system_a:readonly:2147483648:main_a \
    --image system_a=./system_a.img \
    --partition vendor_a:readonly:536870912:main_a \
    --image vendor_a=./vendor_a.img \
    --partition product_a:readonly:402653184:main_a \
    --image product_a=./product_a.img \
    --partition system_ext_a:readonly:536870912:main_a \
    --image system_ext_a=./system_ext_a.img \
    --partition system_b:readonly:4096:main_b \
    --image system_b=./system_b.img \
    --partition vendor_b:readonly:4096:main_b \
    --image vendor_b=./vendor_b.img \
    --partition product_b:readonly:4096:main_b \
    --image product_b=./product_b.img \
    --partition system_ext_b:readonly:4096:main_b \
    --image system_ext_b=./system_ext_b.img \
    --sparse \
    --output super_new.img
```

### Parameters Explained

- `--metadata-size 65536`: Metadata region size (64 KB)
- `--super-name super`: Name of super partition
- `--metadata-slots 3`: Number of metadata backup slots
- `--device super:SIZE`: Total super partition size
- `--group NAME:SIZE`: Partition group with max size
- `--partition NAME:ATTRS:SIZE:GROUP`: Partition definition
- `--image NAME=PATH`: Partition image file
- `--sparse`: Output in sparse format
- `--output FILE`: Output file name

## Validation

### Check Magic Numbers

```bash
# LP Geometry magic at offset 4096
hexdump -C super.img -s 4096 -n 4
# Should show: 41 6c 44 67

# LP Metadata magic at offset 8192
hexdump -C super.img -s 8192 -n 4
# Should show: 30 50 4c 41
```

### Verify Checksums

The checksums are SHA256 hashes. To verify:

1. Read geometry/header
2. Extract checksum field
3. Calculate SHA256 of remaining bytes
4. Compare

### List Partitions

```bash
# Using lpunpack
lpunpack -p super.img

# Using Python script
python3 scripts/super_img_extractor.py --super super.img --output temp/ --info info.json
```

## Troubleshooting

### Issue: Invalid LP Magic

**Error:** Magic number mismatch

**Causes:**
1. File is sparse format → convert with simg2img
2. File is corrupted
3. Wrong offset being read

**Solution:**
```bash
# Check if sparse
hexdump -C super.img -n 4

# If 3a ff 26 ed, convert:
simg2img super.img super_raw.img
```

### Issue: Metadata Checksum Fail

**Causes:**
1. Corrupted file
2. Incomplete download

**Solution:**
```bash
# Verify file integrity
md5sum super.img

# Re-download if needed
```

### Issue: Partition Too Large for Group

**Error:** Partition size exceeds group maximum

**Solution:**
```bash
# Reduce partition sizes
resize2fs -M system_a.img

# Or increase group size in lpmake
--group main_a:5000000000  # Larger size
```

## Tools Reference

### lpunpack
```bash
# List partitions
lpunpack -p super.img

# Extract all
lpunpack super.img output_dir/

# Extract specific partition
lpunpack -p partition_name super.img output_dir/
```

### lpmake
```bash
# Build super image (see Creating Super Images section)
```

### simg2img / img2simg
```bash
# Sparse to raw
simg2img sparse.img raw.img

# Raw to sparse
img2simg raw.img sparse.img
```

## References

- [Android Logical Partitions](https://source.android.com/devices/tech/ota/dynamic_partitions)
- [liblp Source Code](https://android.googlesource.com/platform/system/core/+/refs/heads/master/fs_mgr/liblp/)
- [Sparse Image Format](https://android.googlesource.com/platform/system/core/+/master/libsparse/sparse_format.h)
