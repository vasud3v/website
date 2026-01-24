#!/usr/bin/env python3
"""
Deep Workflow Verification Script
Checks all components and their connections
"""
import os
import sys
import importlib.util

def check_file_exists(path, description):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_import(module_path, module_name, description):
    """Check if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {description}: Can import")
        return True, module
    except Exception as e:
        print(f"❌ {description}: Import failed - {str(e)[:100]}")
        return False, None

def check_function_exists(module, func_name, description):
    """Check if a function exists in a module"""
    if module and hasattr(module, func_name):
        print(f"✅ {description}: Function '{func_name}' exists")
        return True
    else:
        print(f"❌ {description}: Function '{func_name}' NOT found")
        return False

print("="*60)
print("DEEP WORKFLOW VERIFICATION")
print("="*60)

all_checks_passed = True

# 1. Check core files
print("\n[1] CORE FILES")
print("-"*60)
files_to_check = [
    ("jable/run_continuous.py", "Main workflow"),
    ("jable/jable_scraper.py", "Scraper"),
    ("jable/download_with_decrypt_v2.py", "Downloader"),
    ("jable/upload_all_hosts.py", "Uploader"),
    ("jable/javdb_integration.py", "JAVDatabase integration"),
    ("database_manager.py", "Database manager"),
]

for path, desc in files_to_check:
    if not check_file_exists(path, desc):
        all_checks_passed = False

# 2. Check preview generator
print("\n[2] PREVIEW GENERATOR")
print("-"*60)
preview_files = [
    ("preview_generator/__init__.py", "Preview package init"),
    ("preview_generator/preview_generator.py", "Preview generator"),
    ("preview_generator/adult_scene_detector.py", "Adult scene detector"),
    ("preview_generator/clip_extractor.py", "Clip extractor"),
    ("preview_workflow/generate_and_upload_preview.py", "Preview workflow"),
]

for path, desc in preview_files:
    if not check_file_exists(path, desc):
        all_checks_passed = False

# 3. Check imports
print("\n[3] MODULE IMPORTS")
print("-"*60)

# Check preview generator import
success, preview_gen = check_import(
    "preview_generator/preview_generator.py",
    "preview_generator",
    "Preview Generator"
)
if success:
    check_function_exists(preview_gen, "PreviewGenerator", "Preview Generator class")
else:
    all_checks_passed = False

# Check adult scene detector
success, detector = check_import(
    "preview_generator/adult_scene_detector.py",
    "adult_scene_detector",
    "Adult Scene Detector"
)
if success:
    check_function_exists(detector, "AdultSceneDetector", "Adult Scene Detector class")
else:
    all_checks_passed = False

# 4. Check workflow integration
print("\n[4] WORKFLOW INTEGRATION")
print("-"*60)

# Check if run_continuous imports preview workflow
try:
    with open("jable/run_continuous.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    checks = [
        ("from workflow_integration import integrate_with_workflow", "Workflow integration import"),
        ("ADVANCED_PREVIEW_AVAILABLE", "Preview availability flag"),
        ("generate_and_upload_preview", "Preview generation function"),
        ("JAVDB_INTEGRATION_AVAILABLE", "JAVDatabase integration flag"),
        ("enrich_with_javdb", "JAVDatabase enrichment function"),
        ("preview_result", "Preview result variable"),
        ("save_video(", "Save video function call"),
    ]
    
    for check_str, desc in checks:
        if check_str in content:
            print(f"✅ {desc}: Found in workflow")
        else:
            print(f"❌ {desc}: NOT found in workflow")
            all_checks_passed = False
            
except Exception as e:
    print(f"❌ Could not read workflow file: {e}")
    all_checks_passed = False

# 5. Check database structure
print("\n[5] DATABASE STRUCTURE")
print("-"*60)

db_checks = [
    ("database/combined_videos.json", "Combined database"),
    ("database/failed_videos.json", "Failed videos"),
    ("database/stats.json", "Statistics"),
]

for path, desc in db_checks:
    check_file_exists(path, desc)

# 6. Check preview metadata saving
print("\n[6] PREVIEW METADATA SAVING")
print("-"*60)

try:
    with open("jable/run_continuous.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    metadata_checks = [
        ("'preview_video_url':", "Preview video URL field"),
        ("'preview_duration':", "Preview duration field"),
        ("'preview_clips':", "Preview clips field"),
        ("'preview_file_size_mb':", "Preview file size field"),
        ("'preview_ia':", "Internet Archive metadata field"),
        ("preview_result.get('preview_video_url')", "Preview URL extraction"),
        ("preview_result.get('num_clips'", "Clips count extraction"),
    ]
    
    for check_str, desc in metadata_checks:
        if check_str in content:
            print(f"✅ {desc}: Implemented")
        else:
            print(f"❌ {desc}: NOT implemented")
            all_checks_passed = False
            
except Exception as e:
    print(f"❌ Could not verify metadata saving: {e}")
    all_checks_passed = False

# 7. Check browser restart logic
print("\n[7] BROWSER RESTART ON 403 ERRORS")
print("-"*60)

try:
    with open("jable/run_continuous.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    restart_checks = [
        ("max_download_attempts", "Download retry attempts"),
        ("scraper.driver.quit()", "Browser close"),
        ("scraper._init_driver()", "Browser restart"),
        ("scraper.scrape_video(url)", "Re-scrape after restart"),
        ("Download failed after", "Failure message"),
    ]
    
    for check_str, desc in restart_checks:
        if check_str in content:
            print(f"✅ {desc}: Implemented")
        else:
            print(f"⚠️ {desc}: NOT found (might use different approach)")
            
except Exception as e:
    print(f"❌ Could not verify browser restart: {e}")

# 8. Check preview workflow return values
print("\n[8] PREVIEW WORKFLOW RETURN VALUES")
print("-"*60)

try:
    with open("preview_workflow/generate_and_upload_preview.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    return_checks = [
        ("'preview_video_url':", "preview_video_url key"),
        ("'preview_file_size_mb':", "preview_file_size_mb key"),
        ("'preview_duration':", "preview_duration key"),
        ("'num_clips':", "num_clips key"),
        ("'identifier':", "IA identifier key"),
        ("'details_url':", "IA details URL key"),
    ]
    
    for check_str, desc in return_checks:
        if check_str in content:
            print(f"✅ {desc}: Returned")
        else:
            print(f"❌ {desc}: NOT returned")
            all_checks_passed = False
            
except Exception as e:
    print(f"❌ Could not verify return values: {e}")
    all_checks_passed = False

# Summary
print("\n" + "="*60)
if all_checks_passed:
    print("✅ ALL CRITICAL CHECKS PASSED")
else:
    print("⚠️ SOME CHECKS FAILED - Review above")
print("="*60)

sys.exit(0 if all_checks_passed else 1)
