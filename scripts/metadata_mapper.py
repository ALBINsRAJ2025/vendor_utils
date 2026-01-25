#!/usr/bin/env python3
"""
metadata_mapper.py - Map device identifiers, product names, and hardware configs

Creates comprehensive mapping between source and target devices for ROM porting.

Usage:
    python3 metadata_mapper.py --source hot30/ --target note11/ --output device_mapping.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

class MetadataMapper:
    """Map device metadata for ROM porting"""
    
    BUILD_PROP_FILES = [
        'system/build.prop',
        'vendor/build.prop',
        'product/build.prop',
        'system_ext/build.prop',
        'odm/build.prop'
    ]
    
    KEY_PROPERTIES = [
        'ro.product.device',
        'ro.product.model',
        'ro.product.name',
        'ro.product.brand',
        'ro.product.manufacturer',
        'ro.product.board',
        'ro.hardware',
        'ro.hardware.chipset',
        'ro.soc.manufacturer',
        'ro.soc.model',
        'ro.board.platform',
        'ro.build.fingerprint',
        'ro.build.product',
        'ro.product.vendor.device',
        'ro.product.system.device',
        'ro.vendor.product.device'
    ]
    
    def __init__(self, source_dir: str, target_dir: str, verbose: bool = False):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.verbose = verbose
        
        self.source_metadata = {}
        self.target_metadata = {}
        self.mapping = {}
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def parse_build_prop(self, file_path: Path) -> Dict[str, str]:
        """Parse build.prop file"""
        props = {}
        
        if not file_path.exists():
            return props
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip()
        
        return props
    
    def extract_metadata(self, root_dir: Path) -> Dict:
        """Extract all metadata from device"""
        metadata = {
            'device_info': {},
            'hardware_info': {},
            'build_info': {},
            'partition_info': {}
        }
        
        all_props = {}
        for prop_file in self.BUILD_PROP_FILES:
            file_path = root_dir / prop_file
            props = self.parse_build_prop(file_path)
            all_props.update(props)
        
        for key in self.KEY_PROPERTIES:
            if key in all_props:
                if key.startswith('ro.product.'):
                    metadata['device_info'][key] = all_props[key]
                elif key.startswith('ro.hardware') or key.startswith('ro.soc') or key.startswith('ro.board'):
                    metadata['hardware_info'][key] = all_props[key]
                elif key.startswith('ro.build.'):
                    metadata['build_info'][key] = all_props[key]
        
        metadata['build_info']['ro.build.version.sdk'] = all_props.get('ro.build.version.sdk', 'unknown')
        metadata['build_info']['ro.build.version.release'] = all_props.get('ro.build.version.release', 'unknown')
        
        partition_images = list(root_dir.glob('*.img'))
        metadata['partition_info']['partitions'] = [p.stem for p in partition_images]
        
        return metadata
    
    def create_mapping(self):
        """Create mapping between source and target"""
        self.log("Creating device mapping...")
        
        self.mapping = {
            'source': {
                'device': self.source_metadata['device_info'].get('ro.product.device', 'unknown'),
                'model': self.source_metadata['device_info'].get('ro.product.model', 'unknown'),
                'codename': self._extract_codename(self.source_metadata),
                'android_version': self.source_metadata['build_info'].get('ro.build.version.release', 'unknown')
            },
            'target': {
                'device': self.target_metadata['device_info'].get('ro.product.device', 'unknown'),
                'model': self.target_metadata['device_info'].get('ro.product.model', 'unknown'),
                'codename': self._extract_codename(self.target_metadata),
                'android_version': self.target_metadata['build_info'].get('ro.build.version.release', 'unknown')
            },
            'substitutions': {},
            'hardware': {},
            'compatibility': {}
        }
        
        for key, source_val in self.source_metadata['device_info'].items():
            target_val = self.target_metadata['device_info'].get(key)
            
            if source_val and target_val and source_val != target_val:
                self.mapping['substitutions'][key] = {
                    'from': source_val,
                    'to': target_val
                }
        
        source_hw = self.source_metadata['hardware_info']
        target_hw = self.target_metadata['hardware_info']
        
        self.mapping['hardware']['chipset'] = {
            'source': source_hw.get('ro.hardware.chipset', source_hw.get('ro.soc.model', 'unknown')),
            'target': target_hw.get('ro.hardware.chipset', target_hw.get('ro.soc.model', 'unknown'))
        }
        
        self.mapping['hardware']['platform'] = {
            'source': source_hw.get('ro.board.platform', 'unknown'),
            'target': target_hw.get('ro.board.platform', 'unknown')
        }
        
        self.mapping['compatibility'] = self._check_compatibility()
    
    def _extract_codename(self, metadata: Dict) -> str:
        """Extract device codename"""
        device = metadata['device_info'].get('ro.product.device', '')
        name = metadata['device_info'].get('ro.product.name', '')
        
        if device:
            return device.split('-')[0]
        elif name:
            return name.split('-')[0]
        
        return 'unknown'
    
    def _check_compatibility(self) -> Dict:
        """Check hardware compatibility"""
        compatibility = {
            'chipset_match': False,
            'platform_match': False,
            'warnings': [],
            'recommendations': []
        }
        
        source_chip = self.mapping['hardware']['chipset']['source'].lower()
        target_chip = self.mapping['hardware']['chipset']['target'].lower()
        
        if 'mt6769' in source_chip and 'mt6769' in target_chip:
            compatibility['chipset_match'] = True
        elif source_chip == target_chip:
            compatibility['chipset_match'] = True
        else:
            compatibility['warnings'].append(
                f"Chipset mismatch: {source_chip} vs {target_chip}"
            )
        
        source_platform = self.mapping['hardware']['platform']['source']
        target_platform = self.mapping['hardware']['platform']['target']
        
        if source_platform == target_platform:
            compatibility['platform_match'] = True
        else:
            compatibility['warnings'].append(
                f"Platform mismatch: {source_platform} vs {target_platform}"
            )
        
        if compatibility['chipset_match']:
            compatibility['recommendations'].append(
                "Chipsets match - vendor blobs may be partially compatible"
            )
        else:
            compatibility['recommendations'].append(
                "CRITICAL: Preserve ALL target vendor blobs due to chipset difference"
            )
        
        source_sdk = int(self.source_metadata['build_info'].get('ro.build.version.sdk', '0'))
        target_sdk = int(self.target_metadata['build_info'].get('ro.build.version.sdk', '0'))
        
        if source_sdk > target_sdk:
            compatibility['recommendations'].append(
                f"Android upgrade: SDK {target_sdk} -> {source_sdk}"
            )
        elif source_sdk < target_sdk:
            compatibility['warnings'].append(
                f"Android downgrade detected: SDK {target_sdk} -> {source_sdk}"
            )
        
        return compatibility
    
    def generate_substitution_script(self, output_path: Path):
        """Generate bash script for text substitutions"""
        with open(output_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated substitution script for ROM porting\n\n")
            f.write("set -e\n\n")
            
            f.write("TARGET_DIR=\"$1\"\n\n")
            f.write("if [ -z \"$TARGET_DIR\" ]; then\n")
            f.write("    echo \"Usage: $0 <target_directory>\"\n")
            f.write("    exit 1\n")
            f.write("fi\n\n")
            
            f.write("echo \"Applying device-specific substitutions...\"\n\n")
            
            for key, values in self.mapping['substitutions'].items():
                from_val = values['from']
                to_val = values['to']
                
                f.write(f"# Substitute {key}\n")
                f.write(f"find \"$TARGET_DIR\" -type f -exec sed -i 's/{from_val}/{to_val}/g' {{}} + 2>/dev/null || true\n\n")
            
            f.write("echo \"Substitutions complete!\"\n")
        
        output_path.chmod(0o755)
        self.log(f"Generated substitution script: {output_path}")
    
    def save_mapping(self, output_path: Path):
        """Save mapping to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.mapping, f, indent=2)
        
        self.log(f"Saved mapping to: {output_path}")
    
    def print_report(self):
        """Print compatibility report"""
        print("\n" + "="*80)
        print("DEVICE METADATA MAPPING")
        print("="*80 + "\n")
        
        print("SOURCE DEVICE:")
        for key, value in self.mapping['source'].items():
            print(f"  {key:20s}: {value}")
        
        print("\nTARGET DEVICE:")
        for key, value in self.mapping['target'].items():
            print(f"  {key:20s}: {value}")
        
        print("\n" + "="*80)
        print("HARDWARE COMPATIBILITY")
        print("="*80 + "\n")
        
        print("Chipset:")
        print(f"  Source: {self.mapping['hardware']['chipset']['source']}")
        print(f"  Target: {self.mapping['hardware']['chipset']['target']}")
        print(f"  Match:  {'✓ YES' if self.mapping['compatibility']['chipset_match'] else '✗ NO'}")
        
        print("\nPlatform:")
        print(f"  Source: {self.mapping['hardware']['platform']['source']}")
        print(f"  Target: {self.mapping['hardware']['platform']['target']}")
        print(f"  Match:  {'✓ YES' if self.mapping['compatibility']['platform_match'] else '✗ NO'}")
        
        if self.mapping['compatibility']['warnings']:
            print("\n⚠ WARNINGS:")
            for warning in self.mapping['compatibility']['warnings']:
                print(f"  - {warning}")
        
        if self.mapping['compatibility']['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in self.mapping['compatibility']['recommendations']:
                print(f"  - {rec}")
        
        print("\n" + "="*80)
        print(f"SUBSTITUTIONS NEEDED: {len(self.mapping['substitutions'])}")
        print("="*80 + "\n")
        
        for key, values in list(self.mapping['substitutions'].items())[:10]:
            print(f"  {key}:")
            print(f"    {values['from']} -> {values['to']}")
        
        if len(self.mapping['substitutions']) > 10:
            print(f"  ... and {len(self.mapping['substitutions']) - 10} more")
        
        print("\n" + "="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Map device metadata for ROM porting',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--source', required=True,
                       help='Source device directory (Hot 30)')
    parser.add_argument('--target', required=True,
                       help='Target device directory (Note 11)')
    parser.add_argument('--output', required=True,
                       help='Output JSON file for mapping')
    parser.add_argument('--script', help='Generate substitution bash script')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        mapper = MetadataMapper(args.source, args.target, args.verbose)
        
        mapper.log("Extracting source metadata...")
        mapper.source_metadata = mapper.extract_metadata(mapper.source_dir)
        
        mapper.log("Extracting target metadata...")
        mapper.target_metadata = mapper.extract_metadata(mapper.target_dir)
        
        mapper.create_mapping()
        
        output_path = Path(args.output)
        mapper.save_mapping(output_path)
        
        if args.script:
            script_path = Path(args.script)
            mapper.generate_substitution_script(script_path)
        
        mapper.print_report()
        
        print(f"[+] Mapping saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
