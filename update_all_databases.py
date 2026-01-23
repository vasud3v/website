"""
Update all database tracking files (stats, progress, etc.)
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import db_manager


def update_all_databases():
    """Update all database tracking files"""
    print("="*70)
    print("UPDATE ALL DATABASE FILES")
    print("="*70)
    
    print("\n📂 Checking database structure...")
    db_manager.ensure_structure()
    
    print("\n📊 Updating progress tracking...")
    db_manager.update_progress()
    
    print("\n📈 Updating statistics...")
    db_manager.update_stats()
    
    print("\n🔍 Verifying integrity...")
    integrity = db_manager.verify_integrity()
    
    if integrity['healthy']:
        print("   ✅ Database integrity: HEALTHY")
    else:
        print("   ⚠️  Database integrity: ISSUES FOUND")
        for issue in integrity['issues']:
            print(f"      - {issue}")
    
    print("\n" + "="*70)
    print("DATABASE STATUS")
    print("="*70)
    
    # Show current status
    db_manager.print_status()
    
    print("\n✅ All database files updated!")


if __name__ == "__main__":
    update_all_databases()
