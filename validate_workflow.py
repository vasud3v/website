#!/usr/bin/env python3
"""
Workflow Validation Script
Checks for common issues and validates the workflow setup
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple

class WorkflowValidator:
    """Validates workflow configuration and identifies issues"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def add_issue(self, category: str, message: str, severity: str = "ERROR"):
        """Add an issue to the list"""
        self.issues.append({
            'category': category,
            'message': message,
            'severity': severity
        })
    
    def add_warning(self, category: str, message: str):
        """Add a warning to the list"""
        self.warnings.append({
            'category': category,
            'message': message
        })
    
    def add_passed(self, category: str, message: str):
        """Add a passed check"""
        self.passed.append({
            'category': category,
            'message': message
        })
    
    def check_database_structure(self):
        """Check database directory and files"""
        print("\n🔍 Checking database structure...")
        
        db_dir = Path("database")
        if not db_dir.exists():
            self.add_issue("Database", "database/ directory does not exist", "ERROR")
            return
        
        self.add_passed("Database", "database/ directory exists")
        
        # Check required files
        required_files = [
            "combined_videos.json",
            "progress_tracking.json",
            "failed_videos.json",
            "hosting_status.json",
            "stats.json"
        ]
        
        for filename in required_files:
            filepath = db_dir / filename
            if not filepath.exists():
                self.add_warning("Database", f"Missing {filename}")
            else:
                # Validate JSON
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.add_passed("Database", f"{filename} is valid JSON")
                except json.JSONDecodeError as e:
                    self.add_issue("Database", f"{filename} is corrupted: {e}", "ERROR")
                except Exception as e:
                    self.add_issue("Database", f"Cannot read {filename}: {e}", "ERROR")
    
    def check_environment_variables(self):
        """Check for required environment variables"""
        print("\n🔍 Checking environment variables...")
        
        # Check for .env files
        env_files = [
            "jable/.env",
            "upload_pipeline/.env"
        ]
        
        for env_file in env_files:
            if Path(env_file).exists():
                self.add_passed("Environment", f"{env_file} exists")
            else:
                self.add_warning("Environment", f"{env_file} not found")
        
        # Check critical environment variables
        critical_vars = [
            "STREAMWISH_API_KEY",
            "LULUSTREAM_API_KEY",
            "STREAMTAPE_API_KEY"
        ]
        
        for var in critical_vars:
            if os.getenv(var):
                self.add_passed("Environment", f"{var} is set")
            else:
                self.add_warning("Environment", f"{var} is not set")
    
    def check_dependencies(self):
        """Check for required Python packages"""
        print("\n🔍 Checking Python dependencies...")
        
        required_packages = [
            "seleniumbase",
            "beautifulsoup4",
            "requests",
            "filelock",
            "psutil",
            "pycryptodome"
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.add_passed("Dependencies", f"{package} is installed")
            except ImportError:
                self.add_issue("Dependencies", f"{package} is not installed", "ERROR")
    
    def check_system_commands(self):
        """Check for required system commands"""
        print("\n🔍 Checking system commands...")
        
        import subprocess
        
        commands = ["ffmpeg", "ffprobe", "git"]
        
        for cmd in commands:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    self.add_passed("System", f"{cmd} is available")
                else:
                    self.add_warning("System", f"{cmd} returned non-zero exit code")
            except FileNotFoundError:
                self.add_issue("System", f"{cmd} is not installed", "WARNING")
            except subprocess.TimeoutExpired:
                self.add_warning("System", f"{cmd} command timed out")
    
    def check_file_permissions(self):
        """Check file and directory permissions"""
        print("\n🔍 Checking file permissions...")
        
        # Check write permissions on critical directories
        critical_dirs = [
            "database",
            "downloaded_files",
            "jable/temp_downloads"
        ]
        
        for dir_path in critical_dirs:
            path = Path(dir_path)
            if path.exists():
                if os.access(path, os.W_OK):
                    self.add_passed("Permissions", f"{dir_path} is writable")
                else:
                    self.add_issue("Permissions", f"{dir_path} is not writable", "ERROR")
            else:
                self.add_warning("Permissions", f"{dir_path} does not exist")
    
    def check_disk_space(self):
        """Check available disk space"""
        print("\n🔍 Checking disk space...")
        
        import shutil
        
        try:
            stat = shutil.disk_usage(".")
            free_gb = stat.free / (1024**3)
            
            if free_gb < 5:
                self.add_issue("Disk Space", f"Low disk space: {free_gb:.2f} GB free", "ERROR")
            elif free_gb < 20:
                self.add_warning("Disk Space", f"Disk space getting low: {free_gb:.2f} GB free")
            else:
                self.add_passed("Disk Space", f"Sufficient disk space: {free_gb:.2f} GB free")
        except Exception as e:
            self.add_warning("Disk Space", f"Cannot check disk space: {e}")
    
    def check_database_integrity(self):
        """Check database for common issues"""
        print("\n🔍 Checking database integrity...")
        
        db_file = Path("database/combined_videos.json")
        if not db_file.exists():
            self.add_warning("Integrity", "combined_videos.json does not exist yet")
            return
        
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list):
                videos = data
            elif isinstance(data, dict):
                videos = data.get('videos', [])
            else:
                self.add_issue("Integrity", "Invalid database format", "ERROR")
                return
            
            # Check for duplicates
            codes = [v.get('code') for v in videos if v.get('code')]
            if len(codes) != len(set(codes)):
                duplicates = len(codes) - len(set(codes))
                self.add_issue("Integrity", f"Found {duplicates} duplicate video codes", "WARNING")
            else:
                self.add_passed("Integrity", "No duplicate video codes found")
            
            # Check for videos without hosting
            no_hosting = sum(1 for v in videos if not v.get('hosting') or len(v.get('hosting', {})) == 0)
            if no_hosting > 0:
                self.add_warning("Integrity", f"{no_hosting} videos without hosting data")
            else:
                self.add_passed("Integrity", "All videos have hosting data")
            
            # Check for required fields
            for i, video in enumerate(videos[:10]):  # Check first 10
                if not video.get('code'):
                    self.add_issue("Integrity", f"Video at index {i} missing 'code' field", "WARNING")
                if not video.get('source_url'):
                    self.add_issue("Integrity", f"Video at index {i} missing 'source_url' field", "WARNING")
        
        except Exception as e:
            self.add_issue("Integrity", f"Error checking database: {e}", "ERROR")
    
    def check_lock_files(self):
        """Check for stale lock files"""
        print("\n🔍 Checking for stale lock files...")
        
        import time
        
        lock_files = list(Path(".").rglob("*.lock"))
        
        if not lock_files:
            self.add_passed("Locks", "No lock files found")
            return
        
        stale_locks = []
        for lock_file in lock_files:
            try:
                age = time.time() - lock_file.stat().st_mtime
                if age > 3600:  # Older than 1 hour
                    stale_locks.append((lock_file, age))
            except Exception:
                pass
        
        if stale_locks:
            for lock_file, age in stale_locks:
                age_hours = age / 3600
                self.add_warning("Locks", f"Stale lock file: {lock_file} ({age_hours:.1f} hours old)")
        else:
            self.add_passed("Locks", f"Found {len(lock_files)} lock files, none are stale")
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("="*70)
        print("WORKFLOW VALIDATION")
        print("="*70)
        
        self.check_database_structure()
        self.check_environment_variables()
        self.check_dependencies()
        self.check_system_commands()
        self.check_file_permissions()
        self.check_disk_space()
        self.check_database_integrity()
        self.check_lock_files()
        
        # Print results
        print("\n" + "="*70)
        print("VALIDATION RESULTS")
        print("="*70)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for check in self.passed:
                print(f"   [{check['category']}] {check['message']}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   [{warning['category']}] {warning['message']}")
        
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                severity = issue['severity']
                print(f"   [{issue['category']}] {severity}: {issue['message']}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Issues: {len(self.issues)}")
        
        # Determine overall status
        critical_issues = [i for i in self.issues if i['severity'] == 'ERROR']
        
        if critical_issues:
            print(f"\n❌ VALIDATION FAILED - {len(critical_issues)} critical issues found")
            return False
        elif self.issues or self.warnings:
            print(f"\n⚠️  VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print(f"\n✅ VALIDATION PASSED - All checks successful")
            return True


def main():
    """Main entry point"""
    validator = WorkflowValidator()
    success = validator.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
