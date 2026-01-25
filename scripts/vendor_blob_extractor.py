#!/usr/bin/env python3
"""
vendor_blob_extractor.py - Extract vendor HALs, libraries, and device-specific drivers

Identifies and categorizes vendor blobs for MT6769H (Helio G88) devices.
Helps preserve device-specific drivers during ROM porting.

Usage:
    python3 vendor_blob_extractor.py --vendor vendor_mount/ --output blobs/ --device note11
"""

import argparse
import json
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

class VendorBlobExtractor:
    """Extract and categorize vendor blobs"""
    
    BLOB_CATEGORIES = {
        'audio': [
            'audio.primary', 'audio.a2dp', 'audio.usb', 'audio.r_submix',
            'libaudiocustparam', 'libaudiopolicy', 'libaudiocomponent',
            'libaudio', 'libalsautils', 'libtinyalsa', 'libtinycompress'
        ],
        'camera': [
            'camera.', 'libcam', 'libmtkcam', 'lib3a', 'libfeature',
            'libcamera_', 'libcamalgo', 'libimageio', 'libispfeature'
        ],
        'display': [
            'hwcomposer', 'gralloc', 'libgui_ext', 'libui_ext',
            'libdpframework', 'libpq_', 'libaal', 'libged'
        ],
        'gpu': [
            'libGLES_mali', 'vulkan.', 'libOpenCL', 'libgpu',
            'libmali', 'libgpud', 'libGpuService'
        ],
        'media': [
            'libstagefright', 'libomx', 'libvcodec', 'libvc1dec',
            'libmpeg2dec', 'libh264dec', 'libh265dec', 'libvp9dec'
        ],
        'sensors': [
            'sensors.', 'libhwm', 'libsensorndkbridge',
            'libsensors', 'libmtklight', 'libmtksensor'
        ],
        'bluetooth': [
            'bluetooth.', 'libbluetooth_mtk', 'libbt-',
            'audio.bluetooth', 'libldacBT'
        ],
        'wifi': [
            'libwifi-hal', 'libwpa_client', 'wpa_supplicant',
            'hostapd', 'libwifitest'
        ],
        'radio': [
            'libril', 'libmtk-ril', 'libratconfig', 'libmtk_vt_service',
            'libc2k', 'libcarrierconfig', 'libsysenv', 'libmdfx'
        ],
        'gps': [
            'gps.', 'libmnl', 'libcurl', 'liblbs_',
            'libgeofence', 'libmtkperf_client'
        ],
        'thermal': [
            'thermal.', 'libthermal', 'libmtcloader',
            'thermald', 'thermal_manager'
        ],
        'power': [
            'power.', 'libpowerhal', 'libperfmgr',
            'libmtkperf', 'android.hardware.power'
        ],
        'fingerprint': [
            'fingerprint.', 'libgf_', 'libfp_', 'fpc_',
            'libegis', 'libgoodix'
        ],
        'nfc': [
            'nfc.', 'libnfc', 'libese', 'nfc_nci'
        ],
        'lights': [
            'lights.', 'liblight'
        ],
        'keymaster': [
            'keymaster.', 'libkeymaster', 'gatekeeper.',
            'libMcGatekeeper', 'libTEECommon'
        ],
        'drm': [
            'libdrm', 'libwvhidl', 'libwvm', 'libdrmclearkey',
            'libplayready', 'liboemcrypto'
        ]
    }
    
    SOC_SPECIFIC_PATTERNS = [
        'mt6769', 'mt6768', 'mt67',
        'mediatek', 'mtk',
        'helio', 'g88'
    ]
    
    def __init__(self, vendor_path: str, output_dir: str, device_name: str, verbose: bool = False):
        self.vendor_path = Path(vendor_path)
        self.output_dir = Path(output_dir)
        self.device_name = device_name
        self.verbose = verbose
        
        self.blobs = defaultdict(list)
        self.categorized_blobs = defaultdict(list)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def scan_vendor(self):
        """Scan vendor partition for blobs"""
        self.log(f"Scanning vendor partition: {self.vendor_path}")
        
        search_dirs = [
            'lib', 'lib64', 'bin', 'etc', 'firmware'
        ]
        
        for search_dir in search_dirs:
            dir_path = self.vendor_path / search_dir
            if dir_path.exists():
                self._scan_directory(dir_path, search_dir)
    
    def _scan_directory(self, dir_path: Path, category: str):
        """Recursively scan directory for blobs"""
        for root, dirs, files in os.walk(dir_path):
            root_path = Path(root)
            
            for filename in files:
                file_path = root_path / filename
                rel_path = file_path.relative_to(self.vendor_path)
                
                self.blobs[category].append(str(rel_path))
    
    def categorize_blobs(self):
        """Categorize blobs by function"""
        self.log("Categorizing blobs by function...")
        
        all_blobs = []
        for category, files in self.blobs.items():
            all_blobs.extend(files)
        
        for blob_path in all_blobs:
            blob_lower = blob_path.lower()
            categorized = False
            
            for category, patterns in self.BLOB_CATEGORIES.items():
                for pattern in patterns:
                    if pattern.lower() in blob_lower:
                        self.categorized_blobs[category].append(blob_path)
                        categorized = True
                        break
                
                if categorized:
                    break
            
            if not categorized:
                self.categorized_blobs['other'].append(blob_path)
    
    def identify_critical_blobs(self) -> Dict[str, List[str]]:
        """Identify critical device-specific blobs that must be preserved"""
        critical = defaultdict(list)
        
        critical_categories = ['camera', 'audio', 'radio', 'sensors', 'display', 'fingerprint']
        
        for category in critical_categories:
            if category in self.categorized_blobs:
                critical[category] = self.categorized_blobs[category]
        
        return dict(critical)
    
    def identify_soc_blobs(self) -> List[str]:
        """Identify SoC-specific blobs (shareable between devices)"""
        soc_blobs = []
        
        all_blobs = []
        for files in self.blobs.values():
            all_blobs.extend(files)
        
        for blob_path in all_blobs:
            blob_lower = blob_path.lower()
            
            for pattern in self.SOC_SPECIFIC_PATTERNS:
                if pattern in blob_lower:
                    soc_blobs.append(blob_path)
                    break
        
        return soc_blobs
    
    def extract_blobs(self, blob_list: List[str], output_subdir: str):
        """Extract specific blobs to output directory"""
        output_path = self.output_dir / output_subdir
        output_path.mkdir(parents=True, exist_ok=True)
        
        extracted = 0
        
        for blob_rel in blob_list:
            source = self.vendor_path / blob_rel
            dest = output_path / blob_rel
            
            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(source, dest)
                    extracted += 1
                except Exception as e:
                    self.log(f"Error copying {blob_rel}: {e}")
        
        self.log(f"Extracted {extracted}/{len(blob_list)} blobs to {output_subdir}")
        return extracted
    
    def generate_proprietary_files_list(self, output_path: Path, blob_list: List[str]):
        """Generate proprietary-files.txt for device tree"""
        with open(output_path, 'w') as f:
            f.write(f"# Proprietary files for {self.device_name}\n")
            f.write(f"# Extracted from vendor partition\n\n")
            
            current_dir = None
            for blob in sorted(blob_list):
                blob_dir = str(Path(blob).parent)
                
                if blob_dir != current_dir:
                    f.write(f"\n# {blob_dir}\n")
                    current_dir = blob_dir
                
                f.write(f"vendor/{blob}\n")
    
    def generate_makefile(self, output_path: Path):
        """Generate Android.mk for blobs"""
        with open(output_path, 'w') as f:
            f.write("# Vendor blobs for " + self.device_name + "\n\n")
            f.write("LOCAL_PATH := $(call my-dir)\n\n")
            f.write("ifneq ($(filter " + self.device_name + ",$(TARGET_DEVICE)),)\n\n")
            
            for category, blobs in self.categorized_blobs.items():
                if category == 'other':
                    continue
                
                libs = [b for b in blobs if b.startswith('lib')]
                
                if libs:
                    f.write(f"# {category.upper()} libraries\n")
                    
                    for lib in libs[:5]:
                        lib_name = Path(lib).stem
                        f.write(f"\ninclude $(CLEAR_VARS)\n")
                        f.write(f"LOCAL_MODULE := {lib_name}\n")
                        f.write(f"LOCAL_SRC_FILES := {lib}\n")
                        f.write(f"LOCAL_MODULE_CLASS := SHARED_LIBRARIES\n")
                        f.write(f"LOCAL_MODULE_SUFFIX := .so\n")
                        f.write(f"LOCAL_MODULE_TAGS := optional\n")
                        f.write(f"LOCAL_VENDOR_MODULE := true\n")
                        f.write(f"include $(BUILD_PREBUILT)\n")
                    
                    if len(libs) > 5:
                        f.write(f"\n# ... and {len(libs)-5} more {category} libraries\n")
                    
                    f.write("\n")
            
            f.write("endif\n")
    
    def generate_report(self):
        """Generate comprehensive blob extraction report"""
        report_path = self.output_dir / "blob_report.txt"
        json_path = self.output_dir / "blob_catalog.json"
        
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"VENDOR BLOB EXTRACTION REPORT - {self.device_name.upper()}\n")
            f.write("="*80 + "\n\n")
            
            total_blobs = sum(len(blobs) for blobs in self.categorized_blobs.values())
            f.write(f"Total blobs found: {total_blobs}\n\n")
            
            f.write("Blobs by Category:\n")
            f.write("-"*80 + "\n")
            
            for category in sorted(self.categorized_blobs.keys()):
                blobs = self.categorized_blobs[category]
                if category != 'other':
                    f.write(f"\n{category.upper()}: {len(blobs)} files\n")
                    
                    for blob in sorted(blobs)[:10]:
                        f.write(f"  - {blob}\n")
                    
                    if len(blobs) > 10:
                        f.write(f"  ... and {len(blobs)-10} more\n")
            
            critical = self.identify_critical_blobs()
            
            f.write("\n" + "="*80 + "\n")
            f.write("CRITICAL DEVICE-SPECIFIC BLOBS (MUST PRESERVE)\n")
            f.write("="*80 + "\n")
            
            for category, blobs in critical.items():
                f.write(f"\n{category.upper()}:\n")
                for blob in sorted(blobs):
                    f.write(f"  ! {blob}\n")
            
            soc_blobs = self.identify_soc_blobs()
            
            f.write("\n" + "="*80 + "\n")
            f.write("SOC-SPECIFIC BLOBS (MT6769H - Shareable)\n")
            f.write("="*80 + "\n\n")
            
            for blob in sorted(soc_blobs)[:20]:
                f.write(f"  ~ {blob}\n")
            
            if len(soc_blobs) > 20:
                f.write(f"  ... and {len(soc_blobs)-20} more\n")
        
        catalog = {
            'device': self.device_name,
            'total_blobs': sum(len(blobs) for blobs in self.categorized_blobs.values()),
            'categorized': {cat: sorted(blobs) for cat, blobs in self.categorized_blobs.items()},
            'critical': {cat: sorted(blobs) for cat, blobs in critical.items()},
            'soc_specific': sorted(soc_blobs)
        }
        
        with open(json_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print(f"\n[+] Blob report: {report_path}")
        print(f"[+] Blob catalog: {json_path}")
        
        print(f"\n[+] Summary:")
        print(f"    Total blobs: {catalog['total_blobs']}")
        print(f"    Critical blobs: {sum(len(b) for b in critical.values())}")
        print(f"    SoC-specific: {len(soc_blobs)}")

def main():
    parser = argparse.ArgumentParser(
        description='Extract and categorize vendor blobs for ROM porting',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--vendor', required=True,
                       help='Path to mounted/extracted vendor partition')
    parser.add_argument('--output', required=True,
                       help='Output directory for extracted blobs and reports')
    parser.add_argument('--device', required=True,
                       help='Device name (e.g., note11)')
    parser.add_argument('--extract-critical', action='store_true',
                       help='Extract critical blobs to output directory')
    parser.add_argument('--generate-files', action='store_true',
                       help='Generate proprietary-files.txt and Android.mk')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        extractor = VendorBlobExtractor(
            args.vendor, 
            args.output, 
            args.device, 
            args.verbose
        )
        
        extractor.scan_vendor()
        extractor.categorize_blobs()
        
        if args.extract_critical:
            critical = extractor.identify_critical_blobs()
            all_critical = []
            for blobs in critical.values():
                all_critical.extend(blobs)
            
            extractor.extract_blobs(all_critical, 'critical_blobs')
        
        if args.generate_files:
            all_blobs = []
            for blobs in extractor.categorized_blobs.values():
                all_blobs.extend(blobs)
            
            prop_files = extractor.output_dir / 'proprietary-files.txt'
            extractor.generate_proprietary_files_list(prop_files, all_blobs)
            print(f"[+] Generated: {prop_files}")
            
            makefile = extractor.output_dir / 'Android.mk'
            extractor.generate_makefile(makefile)
            print(f"[+] Generated: {makefile}")
        
        extractor.generate_report()
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
