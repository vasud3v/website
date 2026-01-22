#!/usr/bin/env python3
"""
Clear all databases and start fresh
"""
import os
import json
from datetime import datetime

# Database files
DB_FILES = [
    'database/videos_complete.json',
    'database/videos_failed.json',
    'jable/database/videos_complete.json',
    'jable/database/videos_failed.json',
    'jable/database/stats.json',
    'database/combined_videos.json'
]

BACKUP_DIR = 'database/backups'

def clear_databases():
    """Clear all database files with backup"""
    print("="*60)
    print("DATABASE CLEANUP UTILITY")
    print("="*60)
    
    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    cleared = 0
    backed_up = 0
    
    for db_file in DB_FILES:
        if os.path.exists(db_file):
            # Create backup
            backup_name = f"{os.path.basename(db_file)}.backup.{timestamp}"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            
            try:
                import shutil
                shutil.copy2(db_file, backup_path)
                print(f"✓ Backed up: {db_file} -> {backup_path}")
                backed_up += 1
            except Exception as e:
                print(f"⚠️ Could not backup {db_file}: {e}")
            
            # Clear the file (write empty array)
            try:
                with open(db_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                print(f"✓ Cleared: {db_file}")
                cleared += 1
            except Exception as e:
                print(f"❌ Could not clear {db_file}: {e}")
        else:
            print(f"⏭️ Not found: {db_file}")
    
    print("\n" + "="*60)
    print(f"SUMMARY")
    print("="*60)
    print(f"Backed up: {backed_up} files")
    print(f"Cleared: {cleared} files")
    print(f"Backups saved to: {BACKUP_DIR}")
    print("\n✅ All databases cleared! Ready for fresh start.")

if __name__ == "__main__":
    clear_databases()
