#!/usr/bin/env python3
"""
partition_analyzer.py - Compare partitions between source and target devices

Identifies device-specific vs shared files, analyzes differences, and generates
migration reports for ROM porting.

Usage:
    python3 partition_analyzer.py --source hot30/ --target note11/ --output analysis/
"""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

class PartitionAnalyzer:
    """Analyze and compare partition images between devices"""
    
    PARTITION_PRIORITY = ['vendor', 'system', 'system_ext', 'product', 'odm']
    DEVICE_SPECIFIC_PATTERNS = [
        'audio', 'camera', 'display', 'fingerprint', 'nfc',
        'sensors', 'thermal', 'touchscreen', 'wifi', 'bluetooth',
        'gps', 'modem', 'radio', 'ril', 'telephony'
    ]
    
    def __init__(self, source_dir: str, target_dir: str, output_dir: str, verbose: bool = False):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.source_mounts = {}
        self.target_mounts = {}
        
    def log(self, message: str):
        if self.verbose:
            print(f"[*] {message}")
    
    def mount_partition(self, image_path: Path, mount_point: Path, fs_type: str = None) -> bool:
        """Mount a partition image"""
        mount_point.mkdir(parents=True, exist_ok=True)
        
        if fs_type is None:
            fs_type = self._detect_filesystem(image_path)
        
        self.log(f"Mounting {image_path.name} as {fs_type}")
        
        try:
            if fs_type == 'ext4':
                result = subprocess.run(
                    ['sudo', 'mount', '-t', 'ext4', '-o', 'ro,loop', str(image_path), str(mount_point)],
                    capture_output=True,
                    text=True
                )
            elif fs_type == 'erofs':
                result = subprocess.run(
                    ['sudo', 'mount', '-t', 'erofs', '-o', 'ro,loop', str(image_path), str(mount_point)],
                    capture_output=True,
                    text=True
                )
            else:
                self.log(f"Unsupported filesystem: {fs_type}, attempting read with debugfs/dump.erofs")
                return False
            
            if result.returncode == 0:
                return True
            else:
                self.log(f"Mount failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"Mount error: {e}")
            return False
    
    def unmount_partition(self, mount_point: Path):
        """Unmount a partition"""
        try:
            subprocess.run(['sudo', 'umount', str(mount_point)], capture_output=True)
        except:
            pass
    
    def _detect_filesystem(self, image_path: Path) -> str:
        """Detect filesystem type"""
        try:
            result = subprocess.run(
                ['file', '-b', str(image_path)],
                capture_output=True,
                text=True
            )
            output = result.stdout.lower()
            
            if 'ext4' in output or 'ext2' in output:
                return 'ext4'
            elif 'erofs' in output:
                return 'erofs'
            elif 'f2fs' in output:
                return 'f2fs'
            
            return 'ext4'
        except:
            return 'ext4'
    
    def extract_file_list(self, mount_point: Path) -> Dict[str, Dict]:
        """Extract file list with metadata from mounted partition"""
        files = {}
        
        for root, dirs, filenames in os.walk(mount_point):
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(mount_point)
                
                try:
                    stat = file_path.stat()
                    files[str(rel_path)] = {
                        'size': stat.st_size,
                        'mode': oct(stat.st_mode),
                        'type': self._get_file_type(file_path),
                        'hash': self._get_file_hash(file_path) if stat.st_size < 100 * 1024 * 1024 else None
                    }
                except Exception as e:
                    self.log(f"Error processing {rel_path}: {e}")
        
        return files
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type"""
        if file_path.suffix in ['.so', '.ko']:
            return 'library'
        elif file_path.suffix in ['.xml', '.conf', '.rc', '.prop']:
            return 'config'
        elif file_path.suffix == '.apk':
            return 'apk'
        elif file_path.name.startswith('lib'):
            return 'library'
        elif 'bin/' in str(file_path):
            return 'binary'
        else:
            return 'other'
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except:
            return None
    
    def compare_partitions(self, partition_name: str) -> Dict:
        """Compare a partition between source and target"""
        self.log(f"Comparing {partition_name} partition")
        
        source_img = self.source_dir / f"{partition_name}.img"
        target_img = self.target_dir / f"{partition_name}.img"
        
        if not source_img.exists():
            source_img = self.source_dir / f"{partition_name}_a.img"
        if not target_img.exists():
            target_img = self.target_dir / f"{partition_name}_a.img"
        
        if not source_img.exists() or not target_img.exists():
            self.log(f"Partition images not found for {partition_name}")
            return None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source_mount = Path(tmpdir) / "source"
            target_mount = Path(tmpdir) / "target"
            
            if not self.mount_partition(source_img, source_mount):
                self.log(f"Failed to mount source {partition_name}")
                return None
            
            if not self.mount_partition(target_img, target_mount):
                self.unmount_partition(source_mount)
                self.log(f"Failed to mount target {partition_name}")
                return None
            
            try:
                source_files = self.extract_file_list(source_mount)
                target_files = self.extract_file_list(target_mount)
                
                analysis = self._analyze_differences(source_files, target_files, partition_name)
                
            finally:
                self.unmount_partition(source_mount)
                self.unmount_partition(target_mount)
        
        return analysis
    
    def _analyze_differences(self, source_files: Dict, target_files: Dict, partition: str) -> Dict:
        """Analyze differences between file lists"""
        source_set = set(source_files.keys())
        target_set = set(target_files.keys())
        
        only_source = source_set - target_set
        only_target = target_set - source_set
        common = source_set & target_set
        
        modified = []
        for file_path in common:
            s_hash = source_files[file_path].get('hash')
            t_hash = target_files[file_path].get('hash')
            
            if s_hash and t_hash and s_hash != t_hash:
                modified.append({
                    'path': file_path,
                    'source_size': source_files[file_path]['size'],
                    'target_size': target_files[file_path]['size'],
                    'type': source_files[file_path]['type']
                })
        
        device_specific_source = self._classify_device_specific(only_source)
        device_specific_target = self._classify_device_specific(only_target)
        
        return {
            'partition': partition,
            'statistics': {
                'source_total': len(source_set),
                'target_total': len(target_set),
                'common': len(common),
                'only_source': len(only_source),
                'only_target': len(only_target),
                'modified': len(modified)
            },
            'only_in_source': sorted(list(only_source)),
            'only_in_target': sorted(list(only_target)),
            'modified_files': modified,
            'device_specific': {
                'source': device_specific_source,
                'target': device_specific_target
            },
            'recommendations': self._generate_recommendations(
                partition, only_source, only_target, modified, 
                device_specific_source, device_specific_target
            )
        }
    
    def _classify_device_specific(self, file_set: Set[str]) -> Dict[str, List[str]]:
        """Classify files by device-specific categories"""
        classified = defaultdict(list)
        
        for file_path in file_set:
            path_lower = file_path.lower()
            
            matched = False
            for pattern in self.DEVICE_SPECIFIC_PATTERNS:
                if pattern in path_lower:
                    classified[pattern].append(file_path)
                    matched = True
                    break
            
            if not matched:
                classified['other'].append(file_path)
        
        return dict(classified)
    
    def _generate_recommendations(self, partition: str, only_source: Set, 
                                  only_target: Set, modified: List,
                                  dev_source: Dict, dev_target: Dict) -> List[str]:
        """Generate porting recommendations"""
        recommendations = []
        
        if partition == 'vendor':
            if dev_target.get('camera'):
                recommendations.append("CRITICAL: Preserve target camera HALs and libraries")
            if dev_target.get('audio'):
                recommendations.append("CRITICAL: Preserve target audio HALs (audio.primary.*.so)")
            if dev_target.get('display'):
                recommendations.append("IMPORTANT: Keep target display/graphics drivers")
            if dev_target.get('modem') or dev_target.get('radio'):
                recommendations.append("CRITICAL: Preserve target modem/radio firmware and libraries")
            
            recommendations.append("Copy source vendor partition as base")
            recommendations.append("Selectively replace with target device-specific HALs")
        
        elif partition == 'system':
            recommendations.append("Use source system partition (Android 13 framework)")
            if modified:
                recommendations.append(f"Review {len(modified)} modified common files")
        
        elif partition == 'product':
            recommendations.append("Use source product partition")
            recommendations.append("May need to adapt overlays for target device")
        
        elif partition == 'system_ext':
            recommendations.append("Use source system_ext partition")
        
        return recommendations
    
    def analyze_all(self) -> Dict:
        """Analyze all partitions"""
        results = {}
        
        for partition in self.PARTITION_PRIORITY:
            self.log(f"\n{'='*60}")
            self.log(f"Analyzing partition: {partition}")
            self.log('='*60)
            
            analysis = self.compare_partitions(partition)
            if analysis:
                results[partition] = analysis
        
        return results
    
    def generate_report(self, results: Dict):
        """Generate comprehensive analysis report"""
        report_path = self.output_dir / "analysis_report.txt"
        json_path = self.output_dir / "analysis_data.json"
        
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("ROM PORTING ANALYSIS REPORT\n")
            f.write("Source: Hot 30 (Android 13) -> Target: Note 11 (Android 12->13)\n")
            f.write("="*80 + "\n\n")
            
            for partition, data in results.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"PARTITION: {partition.upper()}\n")
                f.write(f"{'='*80}\n\n")
                
                stats = data['statistics']
                f.write("Statistics:\n")
                f.write(f"  Source files:    {stats['source_total']}\n")
                f.write(f"  Target files:    {stats['target_total']}\n")
                f.write(f"  Common files:    {stats['common']}\n")
                f.write(f"  Only in source:  {stats['only_source']}\n")
                f.write(f"  Only in target:  {stats['only_target']}\n")
                f.write(f"  Modified:        {stats['modified']}\n\n")
                
                f.write("Device-Specific Files in Target:\n")
                for category, files in data['device_specific']['target'].items():
                    if files and category != 'other':
                        f.write(f"  {category.upper()}: {len(files)} files\n")
                        for file in files[:5]:
                            f.write(f"    - {file}\n")
                        if len(files) > 5:
                            f.write(f"    ... and {len(files)-5} more\n")
                f.write("\n")
                
                f.write("Recommendations:\n")
                for rec in data['recommendations']:
                    f.write(f"  • {rec}\n")
                f.write("\n")
        
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[+] Analysis report saved to: {report_path}")
        print(f"[+] JSON data saved to: {json_path}")
        
        summary_path = self.output_dir / "MIGRATION_SUMMARY.md"
        self._generate_migration_summary(results, summary_path)
        print(f"[+] Migration summary: {summary_path}")
    
    def _generate_migration_summary(self, results: Dict, output_path: Path):
        """Generate migration summary in Markdown"""
        with open(output_path, 'w') as f:
            f.write("# ROM Porting Migration Summary\n\n")
            f.write("**Source:** Infinix Hot 30 (Android 13)\n")
            f.write("**Target:** Infinix Note 11 (Android 12 -> 13)\n\n")
            
            f.write("## Critical Files to Preserve from Target\n\n")
            
            for partition, data in results.items():
                critical = []
                for category in ['camera', 'audio', 'modem', 'radio', 'display']:
                    files = data['device_specific']['target'].get(category, [])
                    if files:
                        critical.extend(files)
                
                if critical:
                    f.write(f"### {partition}\n\n")
                    for file in sorted(critical):
                        f.write(f"- `{file}`\n")
                    f.write("\n")
            
            f.write("## Partition Migration Strategy\n\n")
            
            for partition, data in results.items():
                f.write(f"### {partition}\n\n")
                for rec in data['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze partition differences for ROM porting',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--source', required=True, 
                       help='Source device extracted partitions directory (Hot 30)')
    parser.add_argument('--target', required=True,
                       help='Target device extracted partitions directory (Note 11)')
    parser.add_argument('--output', required=True,
                       help='Output directory for analysis results')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--partitions', nargs='+',
                       help='Specific partitions to analyze (default: all)')
    
    args = parser.parse_args()
    
    try:
        analyzer = PartitionAnalyzer(args.source, args.target, args.output, args.verbose)
        
        if args.partitions:
            analyzer.PARTITION_PRIORITY = args.partitions
        
        results = analyzer.analyze_all()
        
        if results:
            analyzer.generate_report(results)
            print("\n[+] Analysis complete!")
        else:
            print("\n[!] No partitions could be analyzed")
            print("    Make sure partition images are mounted or extracted")
            
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
