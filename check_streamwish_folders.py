#!/usr/bin/env python3
"""
Check StreamWish folders - diagnostic tool
"""
import os
import sys
import time

# Add jable directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jable'))

from streamwish_folders import list_folders, get_or_create_folder
from load_env import load_env

def main():
    # Load environment
    load_env()
    api_key = os.getenv('STREAMWISH_API_KEY')
    
    if not api_key:
        print("❌ STREAMWISH_API_KEY not found in environment")
        return
    
    print("=" * 60)
    print("StreamWish Folder Diagnostic Tool")
    print("=" * 60)
    
    # List all folders
    print("\n📁 Fetching all folders from StreamWish...")
    folders = list_folders(api_key)
    
    if not folders:
        print("⚠️ No folders found or API error")
        return
    
    print(f"\n✅ Found {len(folders)} folders:\n")
    
    # Group by parent
    root_folders = []
    child_folders = {}
    
    for folder in folders:
        fld_id = folder.get('fld_id')
        name = folder.get('name', 'Unnamed')
        parent_id = folder.get('parent_id', 0)
        
        if parent_id == 0:
            root_folders.append(folder)
        else:
            if parent_id not in child_folders:
                child_folders[parent_id] = []
            child_folders[parent_id].append(folder)
    
    # Display hierarchy
    print("Root Folders:")
    for folder in root_folders:
        fld_id = folder.get('fld_id')
        name = folder.get('name', 'Unnamed')
        print(f"  📁 {name} (ID: {fld_id})")
        
        # Show children
        if fld_id in child_folders:
            for child in child_folders[fld_id]:
                child_name = child.get('name', 'Unnamed')
                child_id = child.get('fld_id')
                print(f"    └─ 📁 {child_name} (ID: {child_id})")
    
    # Test creating a folder
    print("\n" + "=" * 60)
    print("Testing folder creation...")
    print("=" * 60)
    
    test_folder = "TEST_FOLDER_" + str(int(time.time()))
    print(f"\nCreating test folder: {test_folder}")
    
    folder_id = get_or_create_folder(test_folder, api_key)
    
    if folder_id:
        print(f"✅ Successfully created/found folder with ID: {folder_id}")
        
        # Verify it exists
        print("\nVerifying folder exists in list...")
        folders = list_folders(api_key)
        found = False
        for folder in folders:
            if str(folder.get('fld_id')) == str(folder_id):
                found = True
                print(f"✅ Folder verified: {folder.get('name')} (ID: {folder_id})")
                break
        
        if not found:
            print(f"⚠️ Folder {folder_id} not found in list (API delay or pagination issue)")
    else:
        print("❌ Failed to create folder")

if __name__ == "__main__":
    main()
