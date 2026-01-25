#!/usr/bin/env python3
"""
device_tree_extractor.py - Extract and compare device tree overlays (dtbo, dtb)

Handles DTB/DTBO extraction from boot images and compares device tree configurations
between source and target devices.

Usage:
    python3 device_tree_extractor.py --boot boot.img --output dtb_extracted/
"""

import argparse
import os
import struct
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

class DeviceTreeExtractor:
    """Extract and analyze device tree blobs"""
    
    DTB_MAGIC = 0xD00DFEED
    DTBO_MAGIC = 0xD7B7AB1E
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def extract_from_boot(self, boot_img: Path, output_dir: Path) -> bool:
        """Extract DTB from boot.img using unpack tools"""
        self.log(f"Extracting from boot image: {boot_img}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ['unpack_bootimg', '--boot_img', str(boot_img), '--out', str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("Successfully extracted with unpack_bootimg")
                return True
            else:
                self.log("unpack_bootimg failed, trying manual extraction")
                
        except FileNotFoundError:
            self.log("unpack_bootimg not found")
        except subprocess.TimeoutExpired:
            self.log("unpack_bootimg timed out")
        
        return self._extract_dtb_manual(boot_img, output_dir)
    
    def _extract_dtb_manual(self, boot_img: Path, output_dir: Path) -> bool:
        """Manually search for and extract DTB from boot image"""
        self.log("Searching for DTB manually in boot image")
        
        with open(boot_img, 'rb') as f:
            data = f.read()
        
        dtb_offsets = []
        
        for i in range(len(data) - 4):
            magic = struct.unpack('>I', data[i:i+4])[0]
            
            if magic == self.DTB_MAGIC:
                dtb_offsets.append(i)
                self.log(f"Found DTB magic at offset: {i:#x}")
        
        if not dtb_offsets:
            self.log("No DTB found in boot image")
            return False
        
        for idx, offset in enumerate(dtb_offsets):
            dtb_size = self._get_dtb_size(data, offset)
            
            if dtb_size:
                dtb_data = data[offset:offset+dtb_size]
                
                output_file = output_dir / f"dtb_{idx}.dtb"
                with open(output_file, 'wb') as f:
                    f.write(dtb_data)
                
                self.log(f"Extracted DTB {idx}: {output_file} ({dtb_size} bytes)")
        
        return len(dtb_offsets) > 0
    
    def _get_dtb_size(self, data: bytes, offset: int) -> Optional[int]:
        """Calculate DTB size from header"""
        try:
            if offset + 8 > len(data):
                return None
            
            total_size = struct.unpack('>I', data[offset+4:offset+8])[0]
            
            if total_size > 0 and total_size < 1024 * 1024:
                return total_size
            
            return None
        except:
            return None
    
    def extract_dtbo(self, dtbo_img: Path, output_dir: Path) -> bool:
        """Extract DTBO entries"""
        self.log(f"Extracting DTBO: {dtbo_img}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ['mkdtboimg', 'dump', str(dtbo_img), '-b', str(output_dir / 'dtbo')],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("DTBO extracted successfully")
                return True
            else:
                self.log(f"mkdtboimg failed: {result.stderr}")
                
        except FileNotFoundError:
            self.log("mkdtboimg not found")
        except subprocess.TimeoutExpired:
            self.log("mkdtboimg timed out")
        
        return self._extract_dtbo_manual(dtbo_img, output_dir)
    
    def _extract_dtbo_manual(self, dtbo_img: Path, output_dir: Path) -> bool:
        """Manually extract DTBO"""
        self.log("Extracting DTBO manually")
        
        with open(dtbo_img, 'rb') as f:
            magic = struct.unpack('>I', f.read(4))[0]
            
            if magic != self.DTBO_MAGIC:
                self.log(f"Invalid DTBO magic: {magic:#x}")
                return False
            
            self.log("Valid DTBO image detected")
        
        return True
    
    def decompile_dtb(self, dtb_file: Path, output_dts: Path) -> bool:
        """Decompile DTB to DTS (device tree source)"""
        self.log(f"Decompiling DTB: {dtb_file}")
        
        try:
            result = subprocess.run(
                ['dtc', '-I', 'dtb', '-O', 'dts', '-o', str(output_dts), str(dtb_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log(f"DTB decompiled to: {output_dts}")
                return True
            else:
                self.log(f"dtc failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.log("dtc (device tree compiler) not found")
            self.log("Install with: apt install device-tree-compiler")
            return False
        except subprocess.TimeoutExpired:
            self.log("dtc timed out")
            return False
    
    def compare_dts(self, source_dts: Path, target_dts: Path, output_diff: Path):
        """Compare two DTS files and generate diff"""
        self.log(f"Comparing DTS files")
        
        try:
            result = subprocess.run(
                ['diff', '-u', str(target_dts), str(source_dts)],
                capture_output=True,
                text=True
            )
            
            with open(output_diff, 'w') as f:
                f.write(result.stdout)
            
            self.log(f"Diff saved to: {output_diff}")
            
            if result.stdout:
                print(f"\n[+] Differences found between device trees")
                print(f"    Review: {output_diff}")
            else:
                print(f"\n[+] Device trees are identical")
                
        except Exception as e:
            self.log(f"Diff failed: {e}")
    
    def extract_properties(self, dts_file: Path) -> dict:
        """Extract key properties from DTS file"""
        self.log(f"Extracting properties from: {dts_file}")
        
        properties = {
            'model': None,
            'compatible': [],
            'memory': None,
            'cpus': None
        }
        
        try:
            with open(dts_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                import re
                
                model_match = re.search(r'model\s*=\s*"([^"]+)"', content)
                if model_match:
                    properties['model'] = model_match.group(1)
                
                compat_matches = re.findall(r'compatible\s*=\s*"([^"]+)"', content)
                properties['compatible'] = compat_matches
                
        except Exception as e:
            self.log(f"Error parsing DTS: {e}")
        
        return properties

def main():
    parser = argparse.ArgumentParser(
        description='Extract and analyze device tree blobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract DTB from boot image
  %(prog)s --boot boot.img --output dtb_out/
  
  # Extract and decompile
  %(prog)s --boot boot.img --output dtb_out/ --decompile
  
  # Compare two device trees
  %(prog)s --compare source.dts target.dts --diff changes.diff
        """
    )
    
    parser.add_argument('--boot', help='Boot image to extract DTB from')
    parser.add_argument('--dtbo', help='DTBO image to extract')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--decompile', action='store_true',
                       help='Decompile DTB to DTS')
    parser.add_argument('--compare', nargs=2, metavar=('SOURCE', 'TARGET'),
                       help='Compare two DTS files')
    parser.add_argument('--diff', help='Output diff file for comparison')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    extractor = DeviceTreeExtractor(args.verbose)
    
    try:
        if args.boot and args.output:
            boot_path = Path(args.boot)
            output_dir = Path(args.output)
            
            if not boot_path.exists():
                print(f"[!] Boot image not found: {boot_path}")
                return 1
            
            success = extractor.extract_from_boot(boot_path, output_dir)
            
            if success and args.decompile:
                for dtb_file in output_dir.glob('*.dtb'):
                    dts_file = dtb_file.with_suffix('.dts')
                    extractor.decompile_dtb(dtb_file, dts_file)
            
            print(f"\n[+] Extraction complete: {output_dir}")
        
        elif args.dtbo and args.output:
            dtbo_path = Path(args.dtbo)
            output_dir = Path(args.output)
            
            if not dtbo_path.exists():
                print(f"[!] DTBO image not found: {dtbo_path}")
                return 1
            
            extractor.extract_dtbo(dtbo_path, output_dir)
            print(f"\n[+] DTBO extraction complete: {output_dir}")
        
        elif args.compare:
            source_dts = Path(args.compare[0])
            target_dts = Path(args.compare[1])
            
            if not source_dts.exists() or not target_dts.exists():
                print("[!] DTS files not found")
                return 1
            
            diff_file = Path(args.diff) if args.diff else Path('dt_diff.patch')
            
            extractor.compare_dts(source_dts, target_dts, diff_file)
        
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
