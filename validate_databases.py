#!/usr/bin/env python3
"""
Validate database integrity and consistency
Checks for common issues and data corruption
"""

import json
import os
from pathlib import Path


def load_json_safe(path):
    """Load JSON with error handling"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in {path}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")
        return None


def validate_jable_database():
    """Validate Jable database structure"""
    print("\n" + "="*70)
    print("VALIDATING JABLE DATABASE")
    print("="*70)
    
    path = "jable/database/videos_complete.json"
    data = load_json_safe(path)
    
    if data is None:
        return False
    
    if not isinstance(data, list):
        print(f"❌ Invalid format: expected list, got {type(data)}")
        return False
    
    print(f"✅ Found {len(data)} videos")
    
    issues = []
    
    for i, video in enumerate(data):
        code = video.get('code', f'UNKNOWN_{i}')
        
        # Check required fields
        if not video.get('code'):
            issues.append(f"  ⚠️ Video {i}: Missing code")
        
        if not video.get('title'):
            issues.append(f"  ⚠️ {code}: Missing title")
        
        if not video.get('hosting'):
            issues.append(f"  ⚠️ {code}: Missing hosting data")
        elif isinstance(video['hosting'], dict):
            # Check hosting format
            if 'service' in video['hosting']:
                issues.append(f"  ⚠️ {code}: Old hosting format (single service object)")
            elif not video['hosting']:
                issues.append(f"  ⚠️ {code}: Empty hosting dict")
            else:
                # Check if it's the correct format (service_name: data)
                for service, data in video['hosting'].items():
                    if not isinstance(data, dict):
                        issues.append(f"  ⚠️ {code}: Invalid hosting format for {service}")
                    elif not data.get('embed_url'):
                        issues.append(f"  ⚠️ {code}: Missing embed_url for {service}")
    
    if issues:
        print(f"\n⚠️ Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(issue)
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print("✅ No issues found")
        return True


def validate_combined_database():
    """Validate combined database structure"""
    print("\n" + "="*70)
    print("VALIDATING COMBINED DATABASE")
    print("="*70)
    
    path = "database/combined_videos.json"
    data = load_json_safe(path)
    
    if data is None:
        return False
    
    if not isinstance(data, list):
        print(f"❌ Invalid format: expected list, got {type(data)}")
        return False
    
    print(f"✅ Found {len(data)} videos")
    
    issues = []
    javdb_count = 0
    
    for i, video in enumerate(data):
        code = video.get('code', f'UNKNOWN_{i}')
        
        # Check required fields
        if not video.get('code'):
            issues.append(f"  ⚠️ Video {i}: Missing code")
        
        if not video.get('title'):
            issues.append(f"  ⚠️ {code}: Missing title")
        
        if not video.get('hosting'):
            issues.append(f"  ⚠️ {code}: Missing hosting data")
        elif isinstance(video['hosting'], dict):
            # Check hosting format
            if 'service' in video['hosting']:
                issues.append(f"  ⚠️ {code}: Old hosting format (single service object)")
            elif not video['hosting']:
                issues.append(f"  ⚠️ {code}: Empty hosting dict")
            else:
                # Check if it's the correct format (service_name: data)
                for service, data in video['hosting'].items():
                    if not isinstance(data, dict):
                        issues.append(f"  ⚠️ {code}: Invalid hosting format for {service}")
                    elif not data.get('embed_url'):
                        issues.append(f"  ⚠️ {code}: Missing embed_url for {service}")
        
        # Check JAVDatabase integration
        if video.get('javdb_available'):
            javdb_count += 1
            
            if not video.get('source_javdb'):
                issues.append(f"  ⚠️ {code}: javdb_available=true but no source_javdb")
            
            if not video.get('screenshots'):
                issues.append(f"  ⚠️ {code}: javdb_available=true but no screenshots")
    
    print(f"📊 JAVDatabase coverage: {javdb_count}/{len(data)} ({javdb_count*100//len(data) if data else 0}%)")
    
    if issues:
        print(f"\n⚠️ Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(issue)
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print("✅ No issues found")
        return True


def check_consistency():
    """Check consistency between Jable and combined databases"""
    print("\n" + "="*70)
    print("CHECKING CONSISTENCY")
    print("="*70)
    
    jable_data = load_json_safe("jable/database/videos_complete.json")
    combined_data = load_json_safe("database/combined_videos.json")
    
    if not jable_data or not combined_data:
        print("❌ Cannot check consistency - missing databases")
        return False
    
    jable_codes = {v.get('code', '').upper() for v in jable_data if v.get('code')}
    combined_codes = {v.get('code', '').upper() for v in combined_data if v.get('code')}
    
    print(f"Jable videos: {len(jable_codes)}")
    print(f"Combined videos: {len(combined_codes)}")
    
    missing_in_combined = jable_codes - combined_codes
    extra_in_combined = combined_codes - jable_codes
    
    if missing_in_combined:
        print(f"\n⚠️ {len(missing_in_combined)} videos in Jable but not in Combined:")
        for code in list(missing_in_combined)[:5]:
            print(f"  - {code}")
        if len(missing_in_combined) > 5:
            print(f"  ... and {len(missing_in_combined) - 5} more")
    
    if extra_in_combined:
        print(f"\n⚠️ {len(extra_in_combined)} videos in Combined but not in Jable:")
        for code in list(extra_in_combined)[:5]:
            print(f"  - {code}")
        if len(extra_in_combined) > 5:
            print(f"  ... and {len(extra_in_combined) - 5} more")
    
    if not missing_in_combined and not extra_in_combined:
        print("✅ Databases are in sync")
        return True
    else:
        return False


def main():
    print("="*70)
    print("DATABASE VALIDATION TOOL")
    print("="*70)
    
    results = []
    
    # Validate Jable database
    results.append(("Jable Database", validate_jable_database()))
    
    # Validate Combined database
    results.append(("Combined Database", validate_combined_database()))
    
    # Check consistency
    results.append(("Consistency", check_consistency()))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ All validations passed!")
        return 0
    else:
        print("\n❌ Some validations failed")
        return 1


if __name__ == "__main__":
    exit(main())
