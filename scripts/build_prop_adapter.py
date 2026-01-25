#!/usr/bin/env python3
"""
build_prop_adapter.py - Parse and adapt build.prop files for ROM porting

Handles device fingerprints, ro.product.* properties, ro.build.* properties,
and generates adapted build.prop for target device.

Usage:
    python3 build_prop_adapter.py --source hot30_build.prop --target note11_build.prop --output adapted_build.prop
"""

import argparse
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple

class BuildPropAdapter:
    """Adapt build.prop files for ROM porting"""
    
    DEVICE_SPECIFIC_PROPS = [
        'ro.product.device',
        'ro.product.model',
        'ro.product.name',
        'ro.product.brand',
        'ro.product.manufacturer',
        'ro.product.board',
        'ro.build.product',
        'ro.product.vendor.device',
        'ro.product.vendor.model',
        'ro.product.vendor.name',
        'ro.product.system.device',
        'ro.product.system.model',
        'ro.product.system.name',
        'ro.product.odm.device',
        'ro.product.odm.model',
        'ro.product.odm.name',
        'ro.build.fingerprint',
        'ro.vendor.build.fingerprint',
        'ro.system.build.fingerprint',
        'ro.bootimage.build.fingerprint',
        'ro.build.description',
        'ro.config.ringtone',
        'ro.config.notification_sound',
        'ro.config.alarm_alert',
        'ro.build.display.id',
        'ro.build.host',
        'ro.build.user',
        'persist.vendor.radio.imei',
        'persist.vendor.radio.meid'
    ]
    
    KEEP_FROM_SOURCE = [
        'ro.build.version.sdk',
        'ro.build.version.release',
        'ro.build.version.security_patch',
        'ro.build.version.base_os',
        'ro.system.build.version.sdk',
        'ro.vendor.build.version.sdk',
        'ro.product.first_api_level',
        'ro.apex.updatable',
        'ro.treble.enabled',
        'ro.actionable_compatible_property.enabled'
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.source_props = OrderedDict()
        self.target_props = OrderedDict()
        self.adapted_props = OrderedDict()
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def parse_build_prop(self, file_path: Path) -> OrderedDict:
        """Parse build.prop file into ordered dictionary"""
        props = OrderedDict()
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    props[key] = value
        
        return props
    
    def load_props(self, source_path: Path, target_path: Path):
        """Load both source and target build.prop files"""
        self.log(f"Loading source build.prop: {source_path}")
        self.source_props = self.parse_build_prop(source_path)
        self.log(f"  Found {len(self.source_props)} properties")
        
        self.log(f"Loading target build.prop: {target_path}")
        self.target_props = self.parse_build_prop(target_path)
        self.log(f"  Found {len(self.target_props)} properties")
    
    def adapt_props(self) -> OrderedDict:
        """Create adapted build.prop combining source and target"""
        self.log("Adapting properties...")
        
        self.adapted_props = OrderedDict()
        
        for key, value in self.source_props.items():
            if key in self.DEVICE_SPECIFIC_PROPS:
                if key in self.target_props:
                    self.adapted_props[key] = self.target_props[key]
                    self.log(f"  Device-specific: {key} = {self.target_props[key]}")
                else:
                    self.adapted_props[key] = value
                    self.log(f"  Missing in target, using source: {key}")
            else:
                self.adapted_props[key] = value
        
        for key, value in self.target_props.items():
            if key in self.DEVICE_SPECIFIC_PROPS and key not in self.adapted_props:
                self.adapted_props[key] = value
                self.log(f"  Adding from target: {key} = {value}")
        
        self._adapt_fingerprint()
        
        return self.adapted_props
    
    def _adapt_fingerprint(self):
        """Adapt build fingerprint for target device"""
        source_fp = self.source_props.get('ro.build.fingerprint', '')
        target_fp = self.target_props.get('ro.build.fingerprint', '')
        
        if not source_fp or not target_fp:
            self.log("  Warning: Missing fingerprint in source or target")
            return
        
        self.log(f"  Source fingerprint: {source_fp}")
        self.log(f"  Target fingerprint: {target_fp}")
        
        source_parts = source_fp.split('/')
        target_parts = target_fp.split('/')
        
        if len(source_parts) >= 5 and len(target_parts) >= 5:
            adapted_fp = f"{target_parts[0]}/{target_parts[1]}/{target_parts[2]}/{source_parts[3]}/{source_parts[4]}"
            
            self.adapted_props['ro.build.fingerprint'] = adapted_fp
            self.log(f"  Adapted fingerprint: {adapted_fp}")
        else:
            self.log("  Warning: Unexpected fingerprint format")
    
    def get_device_info(self, props: OrderedDict) -> Dict[str, str]:
        """Extract device information from properties"""
        return {
            'device': props.get('ro.product.device', 'unknown'),
            'model': props.get('ro.product.model', 'unknown'),
            'manufacturer': props.get('ro.product.manufacturer', 'unknown'),
            'brand': props.get('ro.product.brand', 'unknown'),
            'fingerprint': props.get('ro.build.fingerprint', 'unknown'),
            'android_version': props.get('ro.build.version.release', 'unknown'),
            'sdk_version': props.get('ro.build.version.sdk', 'unknown'),
            'security_patch': props.get('ro.build.version.security_patch', 'unknown')
        }
    
    def generate_patch_file(self, output_path: Path):
        """Generate a patch file showing changes"""
        with open(output_path, 'w') as f:
            f.write("# Build.prop Adaptation Patch\n")
            f.write("# Source: Hot 30 (Android 13) -> Target: Note 11\n\n")
            
            f.write("## Device-Specific Properties Changed:\n\n")
            
            for key in self.DEVICE_SPECIFIC_PROPS:
                source_val = self.source_props.get(key)
                target_val = self.target_props.get(key)
                adapted_val = self.adapted_props.get(key)
                
                if source_val and adapted_val and source_val != adapted_val:
                    f.write(f"### {key}\n")
                    f.write(f"- Source:  {source_val}\n")
                    f.write(f"+ Adapted: {adapted_val}\n\n")
            
            f.write("\n## Properties Preserved from Source (Android 13):\n\n")
            
            for key in self.KEEP_FROM_SOURCE:
                if key in self.adapted_props:
                    f.write(f"- {key} = {self.adapted_props[key]}\n")
    
    def write_build_prop(self, output_path: Path, props: OrderedDict = None):
        """Write build.prop file"""
        if props is None:
            props = self.adapted_props
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("#\n")
            f.write("# SYSTEM BUILD PROPERTIES\n")
            f.write("# Adapted for ROM porting: Hot 30 (A13) -> Note 11\n")
            f.write("# Generated by build_prop_adapter.py\n")
            f.write("#\n\n")
            
            current_section = None
            
            for key, value in props.items():
                section = key.split('.')[0] if '.' in key else 'other'
                
                if section != current_section:
                    f.write(f"\n# {section.upper()} properties\n")
                    current_section = section
                
                f.write(f"{key}={value}\n")
    
    def compare_and_report(self):
        """Generate comparison report"""
        source_info = self.get_device_info(self.source_props)
        target_info = self.get_device_info(self.target_props)
        adapted_info = self.get_device_info(self.adapted_props)
        
        print("\n" + "="*80)
        print("BUILD.PROP ADAPTATION SUMMARY")
        print("="*80 + "\n")
        
        print("SOURCE DEVICE (Hot 30 - Android 13):")
        for key, value in source_info.items():
            print(f"  {key:20s}: {value}")
        
        print("\nTARGET DEVICE (Note 11 - Original):")
        for key, value in target_info.items():
            print(f"  {key:20s}: {value}")
        
        print("\nADAPTED BUILD.PROP:")
        for key, value in adapted_info.items():
            print(f"  {key:20s}: {value}")
        
        print("\n" + "="*80)
        
        changes = 0
        for key in self.DEVICE_SPECIFIC_PROPS:
            source_val = self.source_props.get(key)
            adapted_val = self.adapted_props.get(key)
            if source_val and adapted_val and source_val != adapted_val:
                changes += 1
        
        print(f"\nTotal device-specific properties adapted: {changes}")
        print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Adapt build.prop for ROM porting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic adaptation
  %(prog)s --source hot30/system/build.prop --target note11/system/build.prop --output adapted_build.prop
  
  # With patch file generation
  %(prog)s --source hot30/system/build.prop --target note11/system/build.prop --output adapted_build.prop --patch changes.patch
  
  # Verbose mode
  %(prog)s --source hot30_build.prop --target note11_build.prop --output adapted.prop -v
        """
    )
    
    parser.add_argument('--source', required=True,
                       help='Source build.prop (Hot 30 / Android 13)')
    parser.add_argument('--target', required=True,
                       help='Target build.prop (Note 11 / Android 12)')
    parser.add_argument('--output', required=True,
                       help='Output adapted build.prop file')
    parser.add_argument('--patch', help='Generate patch file showing changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        adapter = BuildPropAdapter(args.verbose)
        
        source_path = Path(args.source)
        target_path = Path(args.target)
        output_path = Path(args.output)
        
        if not source_path.exists():
            print(f"[!] Source file not found: {source_path}")
            return 1
        
        if not target_path.exists():
            print(f"[!] Target file not found: {target_path}")
            return 1
        
        adapter.load_props(source_path, target_path)
        adapter.adapt_props()
        
        adapter.write_build_prop(output_path)
        print(f"[+] Adapted build.prop written to: {output_path}")
        
        if args.patch:
            patch_path = Path(args.patch)
            adapter.generate_patch_file(patch_path)
            print(f"[+] Patch file written to: {patch_path}")
        
        adapter.compare_and_report()
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
