#!/usr/bin/env python3
"""
selinux_policy_merger.py - Merge SELinux policies from source and target ROMs

Handles SELinux policy differences between Android 12 and Android 13,
ensures proper contexts for cross-partition dependencies.

Usage:
    python3 selinux_policy_merger.py --source hot30_policy/ --target note11_policy/ --output merged_policy/
"""

import argparse
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

class SELinuxPolicyMerger:
    """Merge and adapt SELinux policies"""
    
    POLICY_DIRS = [
        'vendor/etc/selinux',
        'system/etc/selinux',
        'system_ext/etc/selinux',
        'product/etc/selinux'
    ]
    
    DEVICE_SPECIFIC_CONTEXTS = [
        'vendor_camera',
        'vendor_audio',
        'vendor_radio',
        'vendor_sensors',
        'vendor_fingerprint',
        'vendor_nfc',
        'vendor_thermal',
        'vendor_wifi',
        'vendor_bluetooth'
    ]
    
    def __init__(self, source_root: str, target_root: str, output_dir: str, verbose: bool = False):
        self.source_root = Path(source_root)
        self.target_root = Path(target_root)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        
        self.source_policies = defaultdict(list)
        self.target_policies = defaultdict(list)
        self.merged_policies = defaultdict(list)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def scan_policies(self, root_dir: Path) -> Dict[str, List[Path]]:
        """Scan for SELinux policy files"""
        policies = defaultdict(list)
        
        for policy_dir in self.POLICY_DIRS:
            full_path = root_dir / policy_dir
            
            if full_path.exists():
                self.log(f"Scanning: {full_path}")
                
                for file_path in full_path.rglob('*'):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(root_dir)
                        policy_type = self._classify_policy_file(file_path)
                        policies[policy_type].append(file_path)
        
        return dict(policies)
    
    def _classify_policy_file(self, file_path: Path) -> str:
        """Classify SELinux policy file type"""
        name = file_path.name
        
        if 'file_contexts' in name:
            return 'file_contexts'
        elif 'property_contexts' in name:
            return 'property_contexts'
        elif 'service_contexts' in name:
            return 'service_contexts'
        elif 'hwservice_contexts' in name:
            return 'hwservice_contexts'
        elif 'seapp_contexts' in name:
            return 'seapp_contexts'
        elif name.endswith('.te'):
            return 'te_policy'
        elif name.endswith('.cil'):
            return 'cil_policy'
        else:
            return 'other'
    
    def load_policies(self):
        """Load policies from source and target"""
        self.log("Loading source policies...")
        self.source_policies = self.scan_policies(self.source_root)
        
        self.log("Loading target policies...")
        self.target_policies = self.scan_policies(self.target_root)
        
        for policy_type in self.source_policies:
            self.log(f"  Source {policy_type}: {len(self.source_policies[policy_type])} files")
        
        for policy_type in self.target_policies:
            self.log(f"  Target {policy_type}: {len(self.target_policies[policy_type])} files")
    
    def merge_file_contexts(self) -> List[str]:
        """Merge file_contexts from both ROMs"""
        self.log("Merging file_contexts...")
        
        source_contexts = set()
        target_contexts = set()
        
        for file_path in self.source_policies.get('file_contexts', []):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        source_contexts.add(line)
        
        for file_path in self.target_policies.get('file_contexts', []):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        target_contexts.add(line)
        
        merged = []
        
        merged.append("# Merged file_contexts for ROM porting")
        merged.append("# Source: Hot 30 (A13) + Target: Note 11 (device-specific)\n")
        
        merged.append("# Source (Android 13) contexts")
        for ctx in sorted(source_contexts):
            if not self._is_device_specific_context(ctx):
                merged.append(ctx)
        
        merged.append("\n# Target (device-specific) contexts")
        for ctx in sorted(target_contexts):
            if self._is_device_specific_context(ctx):
                merged.append(ctx)
        
        return merged
    
    def merge_property_contexts(self) -> List[str]:
        """Merge property_contexts"""
        self.log("Merging property_contexts...")
        
        source_props = self._load_context_file(self.source_policies.get('property_contexts', []))
        target_props = self._load_context_file(self.target_policies.get('property_contexts', []))
        
        merged = []
        merged.append("# Merged property_contexts\n")
        
        merged.append("# Android 13 system properties")
        merged.extend(sorted(source_props - target_props))
        
        merged.append("\n# Device-specific properties")
        device_specific = {p for p in target_props if any(d in p for d in self.DEVICE_SPECIFIC_CONTEXTS)}
        merged.extend(sorted(device_specific))
        
        return merged
    
    def merge_service_contexts(self) -> List[str]:
        """Merge service_contexts and hwservice_contexts"""
        self.log("Merging service contexts...")
        
        source_services = self._load_context_file(
            self.source_policies.get('service_contexts', []) +
            self.source_policies.get('hwservice_contexts', [])
        )
        
        target_services = self._load_context_file(
            self.target_policies.get('service_contexts', []) +
            self.target_policies.get('hwservice_contexts', [])
        )
        
        merged = []
        merged.append("# Merged service contexts\n")
        
        merged.append("# System services")
        merged.extend(sorted(source_services))
        
        merged.append("\n# Device HAL services")
        device_hal_services = {s for s in target_services if 'vendor' in s or 'hal' in s.lower()}
        merged.extend(sorted(device_hal_services))
        
        return merged
    
    def _load_context_file(self, file_paths: List[Path]) -> Set[str]:
        """Load context entries from files"""
        contexts = set()
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            contexts.add(line)
            except Exception as e:
                self.log(f"Error reading {file_path}: {e}")
        
        return contexts
    
    def _is_device_specific_context(self, context: str) -> bool:
        """Check if context is device-specific"""
        context_lower = context.lower()
        
        device_keywords = [
            'camera', 'audio', 'radio', 'modem', 'sensor',
            'fingerprint', 'nfc', 'thermal', 'wifi', 'bluetooth',
            'vendor_file', 'vendor_configs'
        ]
        
        return any(keyword in context_lower for keyword in device_keywords)
    
    def generate_selinux_rules(self) -> List[str]:
        """Generate additional SELinux rules for ported ROM"""
        self.log("Generating additional SELinux rules...")
        
        rules = []
        rules.append("# Additional SELinux rules for ROM porting")
        rules.append("# These rules may be needed for cross-version compatibility\n")
        
        rules.append("# Allow vendor HALs to access system libraries")
        rules.append("allow vendor_hal_domain system_lib_file:dir r_dir_perms;")
        rules.append("allow vendor_hal_domain system_lib_file:file r_file_perms;\n")
        
        rules.append("# Allow system processes to access vendor properties")
        rules.append("get_prop(system_server, vendor_default_prop)\n")
        
        rules.append("# Camera HAL access")
        rules.append("allow cameraserver vendor_camera_prop:file r_file_perms;")
        rules.append("allow cameraserver vendor_camera_data_file:dir rw_dir_perms;\n")
        
        rules.append("# Audio HAL access")
        rules.append("allow audioserver vendor_audio_prop:file r_file_perms;\n")
        
        rules.append("# Radio/modem access")
        rules.append("allow radio vendor_radio_prop:property_service set;")
        rules.append("allow rild vendor_radio_data_file:dir rw_dir_perms;\n")
        
        return rules
    
    def merge_all(self):
        """Merge all policy types"""
        self.load_policies()
        
        file_contexts = self.merge_file_contexts()
        output_path = self.output_dir / 'file_contexts_merged'
        with open(output_path, 'w') as f:
            f.write('\n'.join(file_contexts))
        self.log(f"Wrote: {output_path}")
        
        property_contexts = self.merge_property_contexts()
        output_path = self.output_dir / 'property_contexts_merged'
        with open(output_path, 'w') as f:
            f.write('\n'.join(property_contexts))
        self.log(f"Wrote: {output_path}")
        
        service_contexts = self.merge_service_contexts()
        output_path = self.output_dir / 'service_contexts_merged'
        with open(output_path, 'w') as f:
            f.write('\n'.join(service_contexts))
        self.log(f"Wrote: {output_path}")
        
        selinux_rules = self.generate_selinux_rules()
        output_path = self.output_dir / 'additional_rules.te'
        with open(output_path, 'w') as f:
            f.write('\n'.join(selinux_rules))
        self.log(f"Wrote: {output_path}")
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate merge report"""
        report_path = self.output_dir / 'selinux_merge_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("SELINUX POLICY MERGE REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write("Source Policies (Hot 30 - Android 13):\n")
            for ptype, files in self.source_policies.items():
                f.write(f"  {ptype}: {len(files)} files\n")
            
            f.write("\nTarget Policies (Note 11 - Android 12):\n")
            for ptype, files in self.target_policies.items():
                f.write(f"  {ptype}: {len(files)} files\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("MERGED POLICY FILES:\n")
            f.write("="*80 + "\n\n")
            
            for merged_file in self.output_dir.glob('*_merged'):
                f.write(f"  - {merged_file.name}\n")
            
            f.write(f"  - additional_rules.te\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("INTEGRATION INSTRUCTIONS:\n")
            f.write("="*80 + "\n\n")
            
            f.write("1. Copy merged policy files to vendor/etc/selinux/\n")
            f.write("2. Review additional_rules.te and add to vendor policy\n")
            f.write("3. Rebuild vendor partition with updated policies\n")
            f.write("4. Test for SELinux denials in logcat\n")
            f.write("5. Add permissive rules if needed for testing\n\n")
            
            f.write("To check for SELinux denials:\n")
            f.write("  adb logcat | grep 'avc: denied'\n\n")
        
        print(f"\n[+] SELinux merge complete!")
        print(f"    Report: {report_path}")
        print(f"    Merged policies: {self.output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description='Merge SELinux policies for ROM porting',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--source', required=True,
                       help='Source ROM root directory (Hot 30)')
    parser.add_argument('--target', required=True,
                       help='Target ROM root directory (Note 11)')
    parser.add_argument('--output', required=True,
                       help='Output directory for merged policies')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        merger = SELinuxPolicyMerger(
            args.source,
            args.target,
            args.output,
            args.verbose
        )
        
        merger.merge_all()
        
        return 0
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
