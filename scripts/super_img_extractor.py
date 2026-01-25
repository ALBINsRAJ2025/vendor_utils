#!/usr/bin/env python3
"""
super_img_extractor.py - Extract and parse Android super.img with A/B partition support

Handles sparse images, dynamic partitions, and outputs individual partition images.
Optimized for Android 13 MT6769H devices with A/B partition layout.

Usage:
    python3 super_img_extractor.py --super super.img --output extracted/
"""

import argparse
import os
import struct
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

SPARSE_HEADER_MAGIC = 0xED26FF3A
LP_METADATA_GEOMETRY_MAGIC = 0x616C4467
LP_METADATA_HEADER_MAGIC = 0x414C5030
LP_PARTITION_ATTR_READONLY = (1 << 0)
LP_PARTITION_ATTR_SLOT_SUFFIXED = (1 << 1)

class SparseImageHeader:
    """Android sparse image format header"""
    FORMAT = '<I4H4I'
    SIZE = struct.calcsize(FORMAT)
    
    def __init__(self, data):
        unpacked = struct.unpack(self.FORMAT, data)
        self.magic = unpacked[0]
        self.major_version = unpacked[1]
        self.minor_version = unpacked[2]
        self.file_hdr_sz = unpacked[3]
        self.chunk_hdr_sz = unpacked[4]
        self.blk_sz = unpacked[5]
        self.total_blks = unpacked[6]
        self.total_chunks = unpacked[7]
        self.image_checksum = unpacked[8]
        
    def is_valid(self):
        return (self.magic == SPARSE_HEADER_MAGIC and 
                self.major_version == 1 and
                self.file_hdr_sz == 28 and
                self.chunk_hdr_sz == 12)

class ChunkHeader:
    """Sparse image chunk header"""
    FORMAT = '<2HI'
    SIZE = struct.calcsize(FORMAT)
    
    CHUNK_TYPE_RAW = 0xCAC1
    CHUNK_TYPE_FILL = 0xCAC2
    CHUNK_TYPE_DONT_CARE = 0xCAC3
    
    def __init__(self, data):
        unpacked = struct.unpack(self.FORMAT, data)
        self.chunk_type = unpacked[0]
        self.reserved = unpacked[1]
        self.chunk_sz = unpacked[2]
        self.total_sz = unpacked[3]

class LpMetadataGeometry:
    """Logical partition metadata geometry"""
    FORMAT = '<4I32sI'
    SIZE = struct.calcsize(FORMAT)
    
    def __init__(self, data):
        unpacked = struct.unpack(self.FORMAT, data[:self.SIZE])
        self.magic = unpacked[0]
        self.struct_size = unpacked[1]
        self.checksum = unpacked[2]
        self.metadata_max_size = unpacked[3]
        self.metadata_slot_count = unpacked[5]
        
    def is_valid(self):
        return self.magic == LP_METADATA_GEOMETRY_MAGIC

class LpMetadataHeader:
    """Logical partition metadata header"""
    FORMAT = '<I2H4I32s'
    SIZE = struct.calcsize(FORMAT)
    
    def __init__(self, data):
        unpacked = struct.unpack(self.FORMAT, data[:self.SIZE])
        self.magic = unpacked[0]
        self.major_version = unpacked[1]
        self.minor_version = unpacked[2]
        self.header_size = unpacked[3]
        
class SuperImageExtractor:
    """Extract partitions from Android super.img"""
    
    def __init__(self, super_path: str, output_dir: str, verbose: bool = False):
        self.super_path = Path(super_path)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.partitions = {}
        
        if not self.super_path.exists():
            raise FileNotFoundError(f"Super image not found: {super_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def check_sparse_image(self) -> bool:
        """Check if the image is in sparse format"""
        with open(self.super_path, 'rb') as f:
            header_data = f.read(SparseImageHeader.SIZE)
            if len(header_data) < SparseImageHeader.SIZE:
                return False
            
            header = SparseImageHeader(header_data)
            return header.is_valid()
    
    def unsparse_image(self, input_path: Path, output_path: Path):
        """Convert sparse image to raw image"""
        self.log(f"Converting sparse image: {input_path.name}")
        
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            header_data = infile.read(SparseImageHeader.SIZE)
            header = SparseImageHeader(header_data)
            
            if not header.is_valid():
                raise ValueError("Invalid sparse image header")
            
            self.log(f"Sparse image: {header.total_chunks} chunks, {header.total_blks} blocks")
            
            for chunk_idx in range(header.total_chunks):
                chunk_data = infile.read(ChunkHeader.SIZE)
                chunk = ChunkHeader(chunk_data)
                
                if chunk.chunk_type == ChunkHeader.CHUNK_TYPE_RAW:
                    data_size = (chunk.chunk_sz * header.blk_sz)
                    data = infile.read(data_size)
                    outfile.write(data)
                    
                elif chunk.chunk_type == ChunkHeader.CHUNK_TYPE_FILL:
                    fill_data = infile.read(4)
                    fill_value = struct.unpack('<I', fill_data)[0]
                    fill_bytes = fill_value.to_bytes(4, 'little')
                    
                    for _ in range(chunk.chunk_sz * header.blk_sz // 4):
                        outfile.write(fill_bytes)
                        
                elif chunk.chunk_type == ChunkHeader.CHUNK_TYPE_DONT_CARE:
                    skip_size = chunk.chunk_sz * header.blk_sz
                    outfile.seek(skip_size, 1)
                else:
                    raise ValueError(f"Unknown chunk type: {chunk.chunk_type:#x}")
    
    def extract_using_lpunpack(self, super_path: Path) -> bool:
        """Try to extract using lpunpack tool if available"""
        try:
            result = subprocess.run(
                ['lpunpack', '-p', str(super_path), str(self.output_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("Successfully extracted using lpunpack")
                self._discover_extracted_partitions()
                return True
            else:
                self.log(f"lpunpack failed: {result.stderr}")
                return False
        except FileNotFoundError:
            self.log("lpunpack not found, using built-in extractor")
            return False
        except subprocess.TimeoutExpired:
            self.log("lpunpack timed out")
            return False
    
    def _discover_extracted_partitions(self):
        """Discover partitions extracted by lpunpack"""
        for img_file in self.output_dir.glob('*.img'):
            partition_name = img_file.stem
            self.partitions[partition_name] = {
                'path': str(img_file),
                'size': img_file.stat().st_size
            }
            self.log(f"Found partition: {partition_name} ({img_file.stat().st_size / (1024*1024):.2f} MB)")
    
    def parse_metadata_manual(self, super_path: Path) -> Dict:
        """Manually parse LP metadata when lpunpack is not available"""
        self.log("Parsing LP metadata manually")
        
        with open(super_path, 'rb') as f:
            f.seek(4096)
            geometry_data = f.read(LpMetadataGeometry.SIZE)
            geometry = LpMetadataGeometry(geometry_data)
            
            if not geometry.is_valid():
                raise ValueError("Invalid LP metadata geometry")
            
            self.log(f"Metadata max size: {geometry.metadata_max_size}")
            self.log(f"Metadata slots: {geometry.metadata_slot_count}")
            
            f.seek(8192)
            header_data = f.read(LpMetadataHeader.SIZE)
            header = LpMetadataHeader(header_data)
            
            if header.magic != LP_METADATA_HEADER_MAGIC:
                raise ValueError("Invalid LP metadata header magic")
            
            self.log(f"LP version: {header.major_version}.{header.minor_version}")
        
        return {
            'geometry': {
                'metadata_max_size': geometry.metadata_max_size,
                'metadata_slot_count': geometry.metadata_slot_count
            },
            'header': {
                'major_version': header.major_version,
                'minor_version': header.minor_version
            }
        }
    
    def extract(self) -> Dict[str, Dict]:
        """Extract all partitions from super.img"""
        self.log(f"Extracting super image: {self.super_path}")
        
        raw_super = self.super_path
        
        if self.check_sparse_image():
            self.log("Detected sparse image format")
            raw_super = self.output_dir / "super_raw.img"
            self.unsparse_image(self.super_path, raw_super)
        else:
            self.log("Image is already in raw format")
        
        if self.extract_using_lpunpack(raw_super):
            return self.partitions
        
        self.log("WARNING: lpunpack not available or failed")
        self.log("Parsing metadata manually (limited functionality)")
        
        metadata = self.parse_metadata_manual(raw_super)
        
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.log(f"Metadata saved to: {metadata_path}")
        self.log("\nTo extract partitions, please install lpunpack:")
        self.log("  Ubuntu/Debian: apt install android-sdk-libsparse-utils")
        self.log("  Or build from AOSP: system/core/fs_mgr/liblp/")
        
        return self.partitions
    
    def get_partition_info(self) -> Dict[str, Dict]:
        """Get detailed information about extracted partitions"""
        info = {}
        
        for name, data in self.partitions.items():
            path = Path(data['path'])
            
            fs_type = self._detect_filesystem(path)
            
            info[name] = {
                'path': str(path),
                'size': data['size'],
                'size_mb': round(data['size'] / (1024 * 1024), 2),
                'filesystem': fs_type,
                'slot_suffix': self._get_slot_suffix(name)
            }
        
        return info
    
    def _detect_filesystem(self, image_path: Path) -> str:
        """Detect filesystem type of a partition image"""
        try:
            result = subprocess.run(
                ['file', '-b', str(image_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout.lower()
            
            if 'ext4' in output or 'ext2' in output or 'ext3' in output:
                return 'ext4'
            elif 'f2fs' in output:
                return 'f2fs'
            elif 'erofs' in output:
                return 'erofs'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _get_slot_suffix(self, partition_name: str) -> Optional[str]:
        """Determine if partition has A/B slot suffix"""
        if partition_name.endswith('_a'):
            return 'a'
        elif partition_name.endswith('_b'):
            return 'b'
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Extract partitions from Android super.img (A/B support)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract super.img to output directory
  %(prog)s --super super.img --output extracted/
  
  # Verbose output
  %(prog)s --super super.img --output extracted/ --verbose
  
  # Get partition information as JSON
  %(prog)s --super super.img --output extracted/ --info partitions.json
        """
    )
    
    parser.add_argument('--super', required=True, help='Path to super.img file')
    parser.add_argument('--output', required=True, help='Output directory for extracted partitions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--info', help='Save partition info to JSON file')
    
    args = parser.parse_args()
    
    try:
        extractor = SuperImageExtractor(args.super, args.output, args.verbose)
        partitions = extractor.extract()
        
        if partitions:
            print(f"\n[+] Successfully extracted {len(partitions)} partitions:")
            info = extractor.get_partition_info()
            
            for name, data in info.items():
                slot = f" (slot {data['slot_suffix']})" if data['slot_suffix'] else ""
                print(f"    {name:20s} {data['size_mb']:8.2f} MB  {data['filesystem']:8s}{slot}")
            
            if args.info:
                with open(args.info, 'w') as f:
                    json.dump(info, f, indent=2)
                print(f"\n[+] Partition info saved to: {args.info}")
        else:
            print("\n[!] No partitions extracted. Please install lpunpack tool.")
            sys.exit(1)
        
        print(f"\n[+] Output directory: {args.output}")
        
    except Exception as e:
        print(f"\n[!] Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
