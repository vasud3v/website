#!/usr/bin/env python3
"""
Workflow Setup Script
Initializes the workflow environment and creates necessary directories/files
"""
import os
import json
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """Create all required directories"""
    print("📁 Creating directory structure...")
    
    directories = [
        "database",
        "database/backups",
        "downloaded_files",
        "jable/temp_downloads",
        "javgg/downloaded_files",
        "upload_pipeline/upload_results",
        "tools/preview_generator"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory}")
        else:
            print(f"   ℹ️  Exists: {directory}")

def initialize_database_files():
    """Initialize empty database files"""
    print("\n💾 Initializing database files...")
    
    db_dir = Path("database")
    
    # Combined videos database
    combined_db = db_dir / "combined_videos.json"
    if not combined_db.exists():
        with open(combined_db, 'w', encoding='utf-8') as f:
            json.dump({
                "videos": [],
                "stats": {
                    "total_videos": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }, f, indent=2)
        print(f"   ✅ Created: combined_videos.json")
    else:
        print(f"   ℹ️  Exists: combined_videos.json")
    
    # Progress tracking
    progress_db = db_dir / "progress_tracking.json"
    if not progress_db.exists():
        with open(progress_db, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "total_videos": 0,
                "total_processed": 0,
                "total_failed": 0,
                "success_rate": 0,
                "last_video_code": None,
                "last_video_url": None
            }, f, indent=2)
        print(f"   ✅ Created: progress_tracking.json")
    else:
        print(f"   ℹ️  Exists: progress_tracking.json")
    
    # Failed videos
    failed_db = db_dir / "failed_videos.json"
    if not failed_db.exists():
        with open(failed_db, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        print(f"   ✅ Created: failed_videos.json")
    else:
        print(f"   ℹ️  Exists: failed_videos.json")
    
    # Hosting status
    hosting_db = db_dir / "hosting_status.json"
    if not hosting_db.exists():
        with open(hosting_db, 'w', encoding='utf-8') as f:
            json.dump({
                "streamwish": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                },
                "lulustream": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                },
                "streamtape": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                },
                "turboviplay": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                },
                "uploady": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                },
                "mixdrop": {
                    "available": True,
                    "last_check": None,
                    "rate_limited_until": None
                }
            }, f, indent=2)
        print(f"   ✅ Created: hosting_status.json")
    else:
        print(f"   ℹ️  Exists: hosting_status.json")
    
    # Stats
    stats_db = db_dir / "stats.json"
    if not stats_db.exists():
        with open(stats_db, 'w', encoding='utf-8') as f:
            json.dump({
                "total_videos": 0,
                "total_size_bytes": 0,
                "by_hosting": {},
                "by_category": {},
                "by_model": {},
                "by_studio": {},
                "with_javdb": 0,
                "with_cast": 0,
                "with_screenshots": 0,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
        print(f"   ✅ Created: stats.json")
    else:
        print(f"   ℹ️  Exists: stats.json")

def check_environment_files():
    """Check for .env files"""
    print("\n🔐 Checking environment files...")
    
    env_files = [
        ("jable/.env", "jable/.env.example"),
        ("upload_pipeline/.env", None)
    ]
    
    for env_file, example_file in env_files:
        if Path(env_file).exists():
            print(f"   ✅ Found: {env_file}")
        else:
            print(f"   ⚠️  Missing: {env_file}")
            if example_file and Path(example_file).exists():
                print(f"      Copy {example_file} to {env_file} and fill in your credentials")
            else:
                print(f"      Create {env_file} with your API keys")

def create_gitignore_entries():
    """Ensure sensitive files are in .gitignore"""
    print("\n🔒 Checking .gitignore...")
    
    gitignore_path = Path(".gitignore")
    
    required_entries = [
        "# Environment files",
        ".env",
        "*.env",
        "",
        "# Database files (optional - comment out if you want to commit)",
        "database/*.json",
        "database/backups/",
        "",
        "# Downloaded files",
        "downloaded_files/",
        "jable/temp_downloads/",
        "javgg/downloaded_files/",
        "",
        "# Upload results",
        "upload_pipeline/upload_results/",
        "",
        "# Lock files",
        "*.lock",
        "",
        "# Python cache",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "",
        "# Virtual environment",
        ".venv/",
        "venv/",
        "env/"
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Check if entries are already there
        missing_entries = [entry for entry in required_entries if entry and not entry.startswith('#') and entry not in existing_content]
        
        if missing_entries:
            print(f"   ⚠️  Some entries missing from .gitignore")
            print(f"      Consider adding: {', '.join(missing_entries[:3])}...")
        else:
            print(f"   ✅ .gitignore looks good")
    else:
        print(f"   ⚠️  .gitignore not found")
        print(f"      Creating .gitignore with recommended entries...")
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(required_entries))
        print(f"   ✅ Created .gitignore")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*70)
    print("SETUP COMPLETE")
    print("="*70)
    print("\n📋 Next Steps:")
    print("\n1. Install Python dependencies:")
    print("   pip install -r jable/requirements.txt")
    print("   pip install -r javgg/requirements.txt")
    print("   pip install -r upload_pipeline/requirements.txt")
    print("\n2. Configure environment variables:")
    print("   - Copy jable/.env.example to jable/.env")
    print("   - Add your API keys and credentials")
    print("   - Create upload_pipeline/.env with upload service credentials")
    print("\n3. Install system dependencies:")
    print("   - ffmpeg (for video processing)")
    print("   - ffprobe (for video validation)")
    print("   - Chrome/Chromium (for web scraping)")
    print("\n4. Run validation:")
    print("   python validate_workflow.py")
    print("\n5. Start the workflow:")
    print("   - Jable: python jable/run_continuous.py")
    print("   - JavaGG: python javgg/complete_workflow.py")
    print("\n" + "="*70)

def main():
    """Main setup function"""
    print("="*70)
    print("WORKFLOW SETUP")
    print("="*70)
    
    create_directory_structure()
    initialize_database_files()
    check_environment_files()
    create_gitignore_entries()
    print_next_steps()

if __name__ == "__main__":
    main()
