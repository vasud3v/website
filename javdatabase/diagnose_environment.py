"""
Diagnostic script to check if environment is properly configured
"""

import sys
import os

def check_environment():
    """Check if environment is ready for scraping"""
    print("="*60)
    print("JAVDatabase Scraper Environment Diagnostic")
    print("="*60)
    
    issues = []
    warnings = []
    
    # Check Python version
    print("\n1. Python Version")
    print(f"   {sys.version}")
    if sys.version_info < (3, 7):
        issues.append("Python 3.7+ required")
    else:
        print("   ✓ OK")
    
    # Check required packages
    print("\n2. Required Packages")
    packages = {
        'seleniumbase': 'SeleniumBase',
        'bs4': 'BeautifulSoup4',
        'requests': 'Requests'
    }
    
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   ✓ {name} installed")
        except ImportError:
            issues.append(f"{name} not installed")
            print(f"   ✗ {name} NOT installed")
    
    # Check SeleniumBase version
    try:
        import seleniumbase
        version = seleniumbase.__version__
        print(f"\n3. SeleniumBase Version: {version}")
        if version < "4.0.0":
            warnings.append("SeleniumBase version is old, consider upgrading")
    except:
        pass
    
    # Check Chrome/Chromium
    print("\n4. Browser Check")
    try:
        from seleniumbase import Driver
        print("   Attempting to initialize browser...")
        driver = Driver(uc=True, headless=True, no_sandbox=True)
        print("   ✓ Browser initialized successfully")
        driver.quit()
    except Exception as e:
        issues.append(f"Browser initialization failed: {e}")
        print(f"   ✗ Failed: {e}")
    
    # Check network connectivity
    print("\n5. Network Connectivity")
    try:
        import requests
        response = requests.get("https://www.javdatabase.com", timeout=10)
        if response.status_code == 200:
            print("   ✓ Can reach JAVDatabase.com")
        else:
            warnings.append(f"JAVDatabase returned status {response.status_code}")
            print(f"   ⚠ Status code: {response.status_code}")
    except Exception as e:
        issues.append(f"Cannot reach JAVDatabase: {e}")
        print(f"   ✗ Failed: {e}")
    
    # Check database paths
    print("\n6. Database Paths")
    db_path = "../database/combined_videos.json"
    if os.path.exists(db_path):
        print(f"   ✓ Combined database exists: {db_path}")
    else:
        warnings.append("Combined database doesn't exist yet (will be created)")
        print(f"   ⚠ Database will be created: {db_path}")
    
    # Check retry queue
    retry_path = "../database/javdb_retry_queue.json"
    if os.path.exists(retry_path):
        print(f"   ✓ Retry queue exists: {retry_path}")
    else:
        print(f"   ⚠ Retry queue will be created: {retry_path}")
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    if not issues and not warnings:
        print("✅ All checks passed! Environment is ready.")
        print("\nYou can now run:")
        print("  python test_scraper_fix.py")
        return True
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} Warning(s):")
        for w in warnings:
            print(f"   - {w}")
    
    if issues:
        print(f"\n❌ {len(issues)} Issue(s) found:")
        for i in issues:
            print(f"   - {i}")
        
        print("\n📋 Recommended fixes:")
        if any("not installed" in i for i in issues):
            print("   pip install -r requirements.txt")
        if any("Browser" in i for i in issues):
            print("   pip install --upgrade seleniumbase")
            print("   seleniumbase install chromedriver")
        if any("Cannot reach" in i for i in issues):
            print("   Check your internet connection")
            print("   Check firewall/antivirus settings")
        
        return False
    
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
