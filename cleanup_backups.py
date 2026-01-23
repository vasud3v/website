"""
Clean up old backup files, keep only the most recent one
"""

from pathlib import Path
import os

def cleanup_backups():
    """Remove old backup files"""
    print("="*70)
    print("CLEANUP OLD BACKUP FILES")
    print("="*70)
    
    db_folder = Path(__file__).parent / "database"
    
    # Find all backup files
    backup_files = []
    
    # Pattern 1: combined_videos_backup_*.json
    backup_files.extend(list(db_folder.glob("combined_videos_backup_*.json")))
    
    # Pattern 2: combined_videos.json.backup_*
    backup_files.extend(list(db_folder.glob("combined_videos.json.backup_*")))
    
    print(f"\n📂 Found {len(backup_files)} old backup files:")
    for f in backup_files:
        size = f.stat().st_size / 1024  # KB
        print(f"   - {f.name} ({size:.1f} KB)")
    
    if not backup_files:
        print("\n✅ No old backup files to clean up!")
        return
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in backup_files) / (1024 * 1024)  # MB
    print(f"\n💾 Total size: {total_size:.2f} MB")
    
    # Ask for confirmation
    response = input("\nDelete all these backup files? (y/n): ")
    
    if response.lower() == 'y':
        deleted = 0
        for f in backup_files:
            try:
                f.unlink()
                deleted += 1
            except Exception as e:
                print(f"   ❌ Failed to delete {f.name}: {e}")
        
        print(f"\n✅ Deleted {deleted} backup files")
        print(f"   Freed up {total_size:.2f} MB")
        
        # Check if main backup exists
        main_backup = db_folder / "combined_videos.json.backup"
        if main_backup.exists():
            size = main_backup.stat().st_size / 1024
            print(f"\n📋 Kept main backup: {main_backup.name} ({size:.1f} KB)")
        else:
            print(f"\n⚠️  No main backup file found")
            print(f"   A new backup will be created on next save")
    else:
        print("\n⏭️  Cancelled")


if __name__ == "__main__":
    cleanup_backups()
