#!/usr/bin/env python3
"""
Local Testing Script for Continuous Workflow
Test the workflow on your local machine before deploying to GitHub Actions
"""

import os
import sys
import argparse
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check Python packages
    packages = [
        'seleniumbase',
        'undetected_chromedriver',
        'deep_translator',
        'requests',
        'beautifulsoup4',
        'python-dotenv'
    ]
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing.append(package)
    
    # Check system tools
    tools = ['ffmpeg', 'yt-dlp']
    for tool in tools:
        result = os.system(f"{tool} --version > /dev/null 2>&1")
        if result == 0:
            print(f"  ✅ {tool}")
        else:
            print(f"  ❌ {tool} - MISSING")
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join([p for p in missing if p not in tools])}")
        print(f"  # Install system tools: {', '.join([t for t in missing if t in tools])}")
        return False
    
    print("\n✅ All dependencies installed")
    return True


def check_environment():
    """Check if environment variables are set"""
    print("\n🔍 Checking environment variables...")
    
    required = [
        'SEEKSTREAMING_API_KEY',
        'STREAMTAPE_USERNAME',
        'STREAMTAPE_PASSWORD',
        'TURBOVIPLAY_API_KEY',
        'VIDOZA_API_KEY',
        'UPLOADY_API_KEY'
    ]
    
    missing = []
    for var in required:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing)}")
        print("\nSet them in upload_pipeline/.env file")
        return False
    
    print("\n✅ All environment variables set")
    return True


def test_scraper():
    """Test video scraper"""
    print("\n🎬 Testing video scraper...")
    
    test_url = "https://javmix.tv/video/mide-486/"
    
    result = os.system(f"python javmix/javmix_scraper.py --url {test_url}")
    
    if result == 0:
        print("✅ Scraper test passed")
        return True
    else:
        print("❌ Scraper test failed")
        return False


def test_monitor():
    """Test new video monitor"""
    print("\n🔍 Testing new video monitor...")
    
    result = os.system("python javmix/monitor_new_videos.py --rss-only")
    
    if result == 0:
        print("✅ Monitor test passed")
        return True
    else:
        print("❌ Monitor test failed")
        return False


def test_enrichment():
    """Test JAVDatabase enrichment"""
    print("\n📚 Testing JAVDatabase enrichment...")
    
    result = os.system("python javdatabase/scrape_by_code.py MIDE-486")
    
    if result == 0:
        print("✅ Enrichment test passed")
        return True
    else:
        print("❌ Enrichment test failed")
        return False


def test_preview():
    """Test preview generator"""
    print("\n🎞️ Testing preview generator...")
    
    # Check if test video exists
    test_video = "test.mp4"
    if not os.path.exists(test_video):
        print(f"⚠️ Test video not found: {test_video}")
        print("  Skipping preview test")
        return True
    
    result = os.system(f"python tools/preview_generator/preview_generator.py {test_video} --workers 4")
    
    if result == 0:
        print("✅ Preview test passed")
        return True
    else:
        print("❌ Preview test failed")
        return False


def test_upload():
    """Test video upload"""
    print("\n📤 Testing video upload...")
    
    # Check if test video exists
    test_video = "test.mp4"
    if not os.path.exists(test_video):
        print(f"⚠️ Test video not found: {test_video}")
        print("  Skipping upload test")
        return True
    
    result = os.system(f"python upload_pipeline/upload_to_all_hosts.py {test_video} 'Test Video'")
    
    if result == 0:
        print("✅ Upload test passed")
        return True
    else:
        print("❌ Upload test failed")
        return False


def run_mini_workflow():
    """Run a mini version of the workflow"""
    print("\n🚀 Running mini workflow (1 video)...")
    
    result = os.system("python .github/workflows/continuous_workflow.py --max-runtime 30 --workers 4 --max-videos 1")
    
    if result == 0:
        print("✅ Mini workflow completed")
        return True
    else:
        print("❌ Mini workflow failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test continuous workflow locally',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python test_workflow_local.py --all
  
  # Check dependencies only
  python test_workflow_local.py --check-deps
  
  # Test specific component
  python test_workflow_local.py --test scraper
  
  # Run mini workflow
  python test_workflow_local.py --mini
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--check-env', action='store_true', help='Check environment')
    parser.add_argument('--test', choices=['scraper', 'monitor', 'enrichment', 'preview', 'upload'],
                       help='Test specific component')
    parser.add_argument('--mini', action='store_true', help='Run mini workflow')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🧪 WORKFLOW LOCAL TESTING")
    print("="*70)
    
    if args.check_deps or args.all:
        if not check_dependencies():
            sys.exit(1)
    
    if args.check_env or args.all:
        if not check_environment():
            sys.exit(1)
    
    if args.test == 'scraper' or args.all:
        if not test_scraper():
            sys.exit(1)
    
    if args.test == 'monitor' or args.all:
        if not test_monitor():
            sys.exit(1)
    
    if args.test == 'enrichment' or args.all:
        if not test_enrichment():
            sys.exit(1)
    
    if args.test == 'preview' or args.all:
        if not test_preview():
            sys.exit(1)
    
    if args.test == 'upload' or args.all:
        if not test_upload():
            sys.exit(1)
    
    if args.mini:
        if not run_mini_workflow():
            sys.exit(1)
    
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\n🎉 Your workflow is ready for GitHub Actions!")
    print("\nNext steps:")
    print("  1. Commit and push the workflow files")
    print("  2. Configure secrets in GitHub repository")
    print("  3. Enable GitHub Actions")
    print("  4. Workflow will run automatically every 5 hours")


if __name__ == "__main__":
    main()
