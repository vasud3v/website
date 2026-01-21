#!/usr/bin/env python3
"""
Continuous Video Scraper - Complete Workflow Per Video
For each video: Scrape metadata → Download → Upload → Get embed URLs → Save → Delete → Next
"""
import os
import sys
import time
from datetime import datetime

print("=" * 60)
print("CONTINUOUS SCRAPER STARTING...")
print("=" * 60)

# Load environment
if os.path.exists('.env'):
    print("Loading .env file...")
    from load_env import load_env
    load_env()

print("Importing modules...")
from jable_scraper import JableScraper
from download_with_decrypt_v2 import HLSDownloaderV2 as HLSDownloader
from upload_all_hosts import upload_all
from auto_download import convert_to_mp4
from utils import sanitize_filename, load_json_safe, save_json_safe, check_disk_space, verify_video_file, cleanup_temp_files, normalize_url, create_process_lock, remove_process_lock
from download_thumbnails import download_thumbnail
from upload_thumbnail import upload_thumbnail_to_streamwish
from set_streamwish_thumbnail import set_streamwish_thumbnail
from set_thumbnail_advanced import set_streamwish_thumbnail_advanced

print("All imports successful!")

# Import JAVDatabase integration
try:
    from javdb_integration import enrich_with_javdb
    JAVDB_INTEGRATION_AVAILABLE = True
    print("✓ JAVDatabase integration available")
except ImportError as e:
    JAVDB_INTEGRATION_AVAILABLE = False
    print(f"⚠️ JAVDatabase integration not available: {e}")

TEMP_DIR = "temp_downloads"
DB_FILE = "database/videos_complete.json"
FAILED_DB_FILE = "database/videos_failed.json"
TIME_LIMIT = 5.5 * 3600
MAX_RETRIES = 3

os.makedirs("database", exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def initialize_database():
    """Initialize database files if they don't exist - Creates empty databases"""
    import json
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        log(f"   Created directory: {db_dir}")
    
    # Check if database files exist
    db_exists = os.path.exists(DB_FILE)
    failed_db_exists = os.path.exists(FAILED_DB_FILE)
    
    if db_exists and failed_db_exists:
        log("✓ Database files already exist")
        return
    
    log("⚠️ Database files missing, initializing...")
    
    # Create empty databases
    if not db_exists:
        log(f"   Creating {DB_FILE}...")
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        log(f"   ✓ Created empty videos database")
    
    if not failed_db_exists:
        log(f"   Creating {FAILED_DB_FILE}...")
        with open(FAILED_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        log(f"   ✓ Created empty failed database")
    
    log("✓ Database initialization complete")
    log("   Database will be populated as videos are scraped with full metadata")

def commit_database():
    """Commit and push database after each video - Enhanced with better diagnostics"""
    try:
        import subprocess
        
        log("   [commit] Starting database commit process...")
        
        # Check if we're in a git repository
        try:
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                          check=True, capture_output=True, text=True, timeout=10)
            log(f"   [commit] ✓ Git repo detected: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            log("   [commit] ❌ Not in a git repository, skipping commit")
            return False
        except subprocess.TimeoutExpired:
            log("   [commit] ❌ Git check timeout")
            return False
        
        # Check if running in GitHub Actions
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        if is_github_actions:
            log("   [commit] ✓ Running in GitHub Actions")
            
            # In GitHub Actions, ensure we have the right remote URL with token
            github_token = os.getenv('GITHUB_TOKEN')
            github_repository = os.getenv('GITHUB_REPOSITORY')
            
            if github_token and github_repository:
                log(f"   [commit] Setting up authenticated remote for {github_repository}")
                # Set remote URL with token for authentication
                remote_url = f"https://x-access-token:{github_token}@github.com/{github_repository}.git"
                subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url],
                             capture_output=True, timeout=5)
                log(f"   [commit] ✓ Remote URL configured with token")
            else:
                log(f"   [commit] ⚠️ GitHub token or repository not found in environment")
        else:
            log("   [commit] Running locally (not GitHub Actions)")
        
        # Configure git user (needed for GitHub Actions)
        log("   [commit] Configuring git user...")
        subprocess.run(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'],
                      capture_output=True, timeout=5)
        subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'],
                      capture_output=True, timeout=5)
        
        # Check current branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, timeout=5)
        current_branch = result.stdout.strip()
        log(f"   [commit] Current branch: {current_branch}")
        
        # Don't pull in GitHub Actions - we already have the latest from checkout
        if not is_github_actions:
            log("   [commit] Pulling latest changes...")
            result = subprocess.run(['git', 'pull', '--rebase', 'origin', current_branch], 
                                   capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                log(f"   [commit] ⚠️ Pull failed: {result.stderr}")
            else:
                log(f"   [commit] ✓ Pull successful")
        else:
            log("   [commit] Skipping pull (GitHub Actions already has latest)")
        
        # Check which files actually exist and have changes
        files_to_add = [
            'database/videos_complete.json',
            'database/videos_failed.json',
            'database/streamwish_folders.json'
        ]
        added_files = []
        
        log("   [commit] Checking files to add...")
        for file in files_to_add:
            if os.path.exists(file):
                # Handle directories differently
                if os.path.isdir(file):
                    # Count files in directory
                    file_count = len([f for f in os.listdir(file) if os.path.isfile(os.path.join(file, f))])
                    log(f"   [commit]   {file}: {file_count} files")
                else:
                    file_size = os.path.getsize(file)
                    log(f"   [commit]   {file}: {file_size} bytes")
                
                result = subprocess.run(['git', 'add', '-v', file], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    added_files.append(file)
                    if result.stderr:  # git add -v outputs to stderr
                        log(f"   [commit]   ✓ {result.stderr.strip()}")
                else:
                    log(f"   [commit]   ⚠️ Failed to add {file}: {result.stderr}")
            else:
                log(f"   [commit]   ⚠️ {file} does not exist")
        
        if not added_files:
            log("   [commit] ❌ No files to add")
            return False
        
        # Check if there are actual changes
        result = subprocess.run(['git', 'diff', '--staged', '--quiet'], 
                               capture_output=True, timeout=5)
        if result.returncode == 0:
            log("   [commit] ℹ️ No changes to commit (files unchanged)")
            return False
        
        # Show what's staged with details
        result = subprocess.run(['git', 'diff', '--staged', '--stat'], 
                               capture_output=True, text=True, timeout=5)
        if result.stdout:
            log(f"   [commit] Changes to commit:")
            for line in result.stdout.strip().split('\n'):
                log(f"   [commit]   {line}")
        
        # Show actual diff for debugging
        result = subprocess.run(['git', 'diff', '--staged', '--numstat'], 
                               capture_output=True, text=True, timeout=5)
        if result.stdout:
            log(f"   [commit] Diff stats:")
            for line in result.stdout.strip().split('\n'):
                log(f"   [commit]   {line}")
        
        # Commit
        commit_msg = f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        log(f"   [commit] Creating commit: {commit_msg}")
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            log(f"   [commit] ❌ Commit failed!")
            log(f"   [commit]   Error: {result.stderr}")
            log(f"   [commit]   Output: {result.stdout}")
            return False
        
        log(f"   [commit] ✓ Commit created successfully")
        if result.stdout:
            log(f"   [commit]   {result.stdout.strip()}")
        
        # Verify commit was created
        result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log(f"   [commit] Latest commit: {result.stdout.strip()}")
        
        # Get commit hash for verification
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                               capture_output=True, text=True, timeout=5)
        local_commit_before = result.stdout.strip()
        log(f"   [commit] Local commit hash: {local_commit_before[:7]}")
        
        # Pull with rebase before pushing to handle remote changes
        log(f"   [commit] Pulling latest changes with rebase...")
        pull_result = subprocess.run(['git', 'pull', '--rebase', 'origin', current_branch],
                                     capture_output=True, text=True, timeout=60)
        
        if pull_result.returncode == 0:
            log(f"   [commit] ✓ Pull successful")
            if "Already up to date" not in pull_result.stdout:
                log(f"   [commit]   Rebased onto remote changes")
        else:
            log(f"   [commit] ⚠️ Pull failed, attempting to continue...")
            if pull_result.stderr:
                for line in pull_result.stderr.strip().split('\n')[:3]:  # Show first 3 lines
                    log(f"   [commit]     {line}")
        
        # Push with verbose output and force if needed
        log(f"   [commit] Pushing to origin/{current_branch}...")
        
        # Try normal push first
        push_cmd = ['git', 'push', 'origin', current_branch]
        if is_github_actions:
            # In GitHub Actions, be more aggressive
            push_cmd.extend(['--verbose'])
        
        result = subprocess.run(push_cmd, 
                               capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            log(f"   [commit] ✅ Push successful!")
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    log(f"   [commit]   {line}")
            if result.stderr:  # git push outputs to stderr
                for line in result.stderr.strip().split('\n'):
                    log(f"   [commit]   {line}")
            
            # Verify push by checking remote
            time.sleep(2)  # Give remote a moment to update
            
            if not is_github_actions:
                # Only fetch if not in GitHub Actions (to avoid conflicts)
                result = subprocess.run(['git', 'fetch', 'origin'], 
                                       capture_output=True, text=True, timeout=30)
            
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                   capture_output=True, text=True, timeout=5)
            local_commit = result.stdout.strip()
            
            result = subprocess.run(['git', 'rev-parse', f'origin/{current_branch}'], 
                                   capture_output=True, text=True, timeout=5)
            remote_commit = result.stdout.strip()
            
            if local_commit == remote_commit:
                log(f"   [commit] ✅ VERIFIED: Local and remote are in sync!")
                log(f"   [commit]   Commit {local_commit[:7]} is now on GitHub")
                return True
            else:
                log(f"   [commit] ⚠️ Warning: Sync mismatch")
                log(f"   [commit]   Local:  {local_commit[:7]}")
                log(f"   [commit]   Remote: {remote_commit[:7]}")
                # Still return True since push succeeded
                return True
        else:
            log(f"   [commit] ❌ Push failed!")
            log(f"   [commit]   Return code: {result.returncode}")
            
            if result.stderr:
                log(f"   [commit]   Error output:")
                for line in result.stderr.strip().split('\n'):
                    log(f"   [commit]     {line}")
            
            if result.stdout:
                log(f"   [commit]   Standard output:")
                for line in result.stdout.strip().split('\n'):
                    log(f"   [commit]     {line}")
            
            # Diagnose the issue
            log(f"   [commit] Diagnosing push failure...")
            
            # Check git status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                   capture_output=True, text=True, timeout=5)
            if result.stdout:
                log(f"   [commit]   Uncommitted changes:")
                for line in result.stdout.strip().split('\n'):
                    log(f"   [commit]     {line}")
            
            # Check remote configuration
            result = subprocess.run(['git', 'remote', '-v'], 
                                   capture_output=True, text=True, timeout=5)
            if result.stdout:
                log(f"   [commit]   Remote configuration:")
                for line in result.stdout.strip().split('\n'):
                    # Mask token in output
                    line = line.replace(os.getenv('GITHUB_TOKEN', ''), '***TOKEN***')
                    log(f"   [commit]     {line}")
            
            # Check if we're behind remote
            result = subprocess.run(['git', 'status', '-sb'], 
                                   capture_output=True, text=True, timeout=5)
            if result.stdout:
                log(f"   [commit]   Branch status: {result.stdout.strip()}")
            
            # If in GitHub Actions and push failed, try force push (last resort)
            if is_github_actions:
                log(f"   [commit] Attempting force push (GitHub Actions only)...")
                result = subprocess.run(['git', 'push', '--force', 'origin', current_branch], 
                                       capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    log(f"   [commit] ✅ Force push successful!")
                    return True
                else:
                    log(f"   [commit] ❌ Force push also failed: {result.stderr}")
            
            return False
            
    except subprocess.TimeoutExpired as e:
        log(f"   [commit] ⚠️ Timeout: {e}")
        return False
    except Exception as e:
        log(f"   [commit] ⚠️ Exception: {e}")
        import traceback
        log(f"   [commit] Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line:
                log(f"   [commit]   {line}")
        return False

def is_processed(url):
    """Check if video already processed successfully"""
    try:
        normalized_url = normalize_url(url)
        videos = load_json_safe(DB_FILE, [])
        for v in videos:
            if normalize_url(v.get('source_url', '')) == normalized_url:
                # Check if hosting data exists and is not empty
                hosting = v.get('hosting', {})
                if hosting and len(hosting) > 0:
                    return True
    except:
        pass
    return False

def get_retry_count(url):
    """Get number of times this video has been retried"""
    try:
        normalized_url = normalize_url(url)
        failed_videos = load_json_safe(FAILED_DB_FILE, [])
        for v in failed_videos:
            if normalize_url(v.get('source_url', '')) == normalized_url:
                return v.get('retry_count', 0)
    except:
        pass
    return 0

def mark_as_failed(url, error_msg):
    """Mark video as failed with retry count"""
    try:
        normalized_url = normalize_url(url)
        failed_videos = load_json_safe(FAILED_DB_FILE, [])
        
        # Find existing entry or create new
        found = False
        for v in failed_videos:
            if normalize_url(v.get('source_url', '')) == normalized_url:
                v['retry_count'] = v.get('retry_count', 0) + 1
                v['last_error'] = error_msg
                v['last_attempt'] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            failed_videos.append({
                'source_url': url,
                'retry_count': 1,
                'last_error': error_msg,
                'last_attempt': datetime.now().isoformat()
            })
        
        save_json_safe(FAILED_DB_FILE, failed_videos, use_lock=True)
    except Exception as e:
        log(f"⚠️ Could not mark as failed: {e}")

def save_video(video_data, upload_results, thumbnail_hosted_url=None):
    """Save complete video metadata with embed URLs - Enhanced version with detailed logging"""
    try:
        log(f"   [save_video] ========== SAVE VIDEO START ==========")
        log(f"   [save_video] Video code: {video_data.code}")
        log(f"   [save_video] Video title: {video_data.title}")
        
        # Ensure database directory exists (if DB_FILE has a directory)
        db_dir = os.path.dirname(DB_FILE)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            log(f"   [save_video] Created directory: {db_dir}")
        
        log(f"   [save_video] Loading existing database from {DB_FILE}")
        videos = load_json_safe(DB_FILE, [])
        log(f"   [save_video] Current database has {len(videos)} videos")
        
        # Build comprehensive entry with all metadata
        entry = {
            # Basic info
            'code': video_data.code,
            'title': video_data.title,
            'source_url': video_data.source_url,
            
            # Media info
            'thumbnail_url': thumbnail_hosted_url or video_data.thumbnail_url,  # Prefer hosted URL
            'thumbnail_original': video_data.thumbnail_url,  # Keep original Jable URL as backup
            'duration': video_data.duration,
            'hd_quality': video_data.hd_quality if hasattr(video_data, 'hd_quality') else False,
            
            # Stats
            'views': video_data.views,
            'likes': video_data.likes,
            
            # Dates
            'release_date': video_data.release_date,
            'upload_time': video_data.upload_time if hasattr(video_data, 'upload_time') else '',
            'processed_at': datetime.now().isoformat(),
            
            # Categories and tags
            'categories': video_data.categories if video_data.categories else [],
            'models': video_data.models if video_data.models else [],
            'tags': video_data.tags if video_data.tags else [],
            
            # Preview images
            'preview_images': video_data.preview_images if hasattr(video_data, 'preview_images') else [],
            
            # Hosting info
            'hosting': {},
            
            # Processing metadata
            'file_size': None,  # Will be filled from upload results
            'upload_folder': None  # Will be filled from upload results
        }
        
        log(f"   [save_video] Built entry with {len(entry)} fields")
        log(f"   [save_video] Entry has {len(entry.get('models', []))} models, {len(entry.get('categories', []))} categories")
        
        # Validate upload_results structure
        if not upload_results:
            log(f"   [save_video] ❌ ERROR: upload_results is None or empty!")
            return False
        
        if not isinstance(upload_results, dict):
            log(f"   [save_video] ❌ ERROR: upload_results is not a dict! Type: {type(upload_results)}")
            return False
        
        if 'successful' not in upload_results:
            log(f"   [save_video] ❌ ERROR: upload_results missing 'successful' key!")
            log(f"   [save_video]   Available keys: {list(upload_results.keys())}")
            return False
        
        successful_uploads = upload_results.get('successful', [])
        log(f"   [save_video] Processing {len(successful_uploads)} successful uploads")
        
        if len(successful_uploads) == 0:
            log(f"   [save_video] ❌ ERROR: No successful uploads!")
            log(f"   [save_video]   Failed uploads: {len(upload_results.get('failed', []))}")
            return False
        
        # Add embed URLs from uploads
        for idx, result in enumerate(successful_uploads):
            service = result.get('service', 'unknown').lower()
            embed_url = result.get('embed_url', '')
            watch_url = result.get('watch_url', '')
            filecode = result.get('filecode', '')
            download_url = result.get('download_url', '')
            direct_url = result.get('direct_url', '')
            api_url = result.get('api_url', '')
            
            log(f"   [save_video] Upload {idx+1}: {service}")
            log(f"   [save_video]   Embed URL: {embed_url}")
            log(f"   [save_video]   Watch URL: {watch_url}")
            log(f"   [save_video]   Download URL: {download_url}")
            log(f"   [save_video]   Filecode: {filecode}")
            
            entry['hosting'][service] = {
                'embed_url': embed_url,
                'watch_url': watch_url,
                'download_url': download_url,
                'direct_url': direct_url,
                'api_url': api_url,
                'filecode': filecode,
                'upload_time': result.get('time', 0),
                'uploaded_at': datetime.now().isoformat()
            }
            
            # Store file size if available
            if 'file_size' in result and not entry['file_size']:
                entry['file_size'] = result['file_size']
                log(f"   [save_video]   File size: {entry['file_size']} bytes")
            
            # Store folder name if available
            if 'folder' in result and not entry['upload_folder']:
                entry['upload_folder'] = result['folder']
                log(f"   [save_video]   Folder: {entry['upload_folder']}")
        
        log(f"   [save_video] Entry now has {len(entry['hosting'])} hosting services")
        
        # Validate entry has required fields
        if not entry['code']:
            log(f"   [save_video] ❌ ERROR: Missing video code!")
            return False
        
        if not entry['hosting']:
            log(f"   [save_video] ❌ ERROR: No hosting data after processing uploads!")
            return False
        
        log(f"   [save_video] ✓ Entry validation passed")
        
        # Update or append
        found = False
        for i, v in enumerate(videos):
            if v.get('code') == entry['code']:
                # Merge with existing entry (keep old data if new is empty)
                log(f"   [save_video] Found existing entry at index {i}, updating...")
                for key, value in entry.items():
                    if value or key == 'hosting':  # Always update hosting
                        videos[i][key] = value
                found = True
                log(f"   [save_video] Updated existing entry for {entry['code']}")
                break
        
        if not found:
            videos.append(entry)
            log(f"   [save_video] Added new entry for {entry['code']} (total: {len(videos)})")
        
        # Sort by processed_at (newest first)
        videos.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
        log(f"   [save_video] Sorted {len(videos)} videos by processed_at")
        
        log(f"   [save_video] Saving {len(videos)} videos to {DB_FILE} with lock...")
        
        # Show what we're about to save
        log(f"   [save_video] Entry summary:")
        log(f"   [save_video]   Code: {entry['code']}")
        log(f"   [save_video]   Title: {entry['title'][:50]}...")
        log(f"   [save_video]   Models: {entry.get('models', [])}")
        log(f"   [save_video]   Categories: {entry.get('categories', [])}")
        log(f"   [save_video]   Hosting: {list(entry['hosting'].keys())}")
        log(f"   [save_video]   File size: {entry.get('file_size', 'N/A')}")
        log(f"   [save_video]   Folder: {entry.get('upload_folder', 'N/A')}")
        
        result = save_json_safe(DB_FILE, videos, use_lock=True)
        log(f"   [save_video] Save result: {result}")
        
        # Double-check the file was created
        if os.path.exists(DB_FILE):
            size = os.path.getsize(DB_FILE)
            log(f"   [save_video] ✅ File verified: {DB_FILE} ({size} bytes)")
            
            # Verify the content
            try:
                import json
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                log(f"   [save_video] ✅ File contains {len(saved_data)} videos")
                
                # Check if our video is in there
                found_in_file = False
                for v in saved_data:
                    if v.get('code') == entry['code']:
                        found_in_file = True
                        log(f"   [save_video] ✅ Verified: {entry['code']} is in the file")
                        log(f"   [save_video]   Has {len(v.get('hosting', {}))} hosting services")
                        break
                
                if not found_in_file:
                    log(f"   [save_video] ⚠️ WARNING: {entry['code']} NOT found in saved file!")
            except Exception as e:
                log(f"   [save_video] ⚠️ Could not verify file content: {e}")
        else:
            log(f"   [save_video] ❌ WARNING: File does not exist after save!")
        
        log(f"   [save_video] ========== SAVE VIDEO END ==========")
        return result
    except Exception as e:
        log(f"   [save_video] ❌ EXCEPTION in save_video: {e}")
        import traceback
        log(f"   [save_video] Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line:
                log(f"   [save_video]   {line}")
        return False

def process_one_video(scraper, url, num, total):
    """Complete workflow for one video with proper cleanup"""
    log(f"\n{'='*60}")
    log(f"VIDEO {num}/{total}: {url}")
    log(f"{'='*60}")
    
    code = None
    error_msg = ""
    thumbnail_path = None  # Track thumbnail path
    
    try:
        # Check retry count
        retry_count = get_retry_count(url)
        if retry_count >= MAX_RETRIES:
            log(f"⏭️ Skipping - already failed {retry_count} times")
            return False
        
        # STEP 1: Scrape full metadata
        log("📋 Step 1: Scraping metadata...")
        video_data = scraper.scrape_video(url)
        if not video_data:
            error_msg = "Scraping failed"
            log(f"❌ {error_msg}")
            mark_as_failed(url, error_msg)
            return False
        
        log(f"✅ Got: {video_data.code} - {video_data.title[:40]}...")
        log(f"   Duration: {video_data.duration}, Views: {video_data.views}")
        log(f"   Categories: {len(video_data.categories)}, Models: {len(video_data.models)}")
        
        code = sanitize_filename(video_data.code)
        thumbnail_url = video_data.thumbnail_url  # Will be set after upload
        
        log(f"\n🖼️ Thumbnail will be set after video upload")
        log(f"   Thumbnail URL: {thumbnail_url}")
        
        # Check disk space before download
        has_space, free_gb, _ = check_disk_space(min_free_gb=3)
        if not has_space:
            error_msg = f"Low disk space: {free_gb:.1f}GB"
            log(f"❌ {error_msg}")
            mark_as_failed(url, error_msg)
            return False
        
        # STEP 2: Download video with browser restart on high failure rate
        log("\n📥 Step 2: Downloading video...")
        ts_file = f"{TEMP_DIR}/{code}.ts"
        mp4_file = f"{TEMP_DIR}/{code}.mp4"
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Try download with up to 2 retries (3 total attempts), restarting browser each time
        max_download_attempts = 3  # 1 initial + 2 retries
        download_success = False
        
        for download_attempt in range(1, max_download_attempts + 1):
            try:
                log(f"   Download attempt {download_attempt}/{max_download_attempts}")
                
                # Delete partial download if exists
                if os.path.exists(ts_file):
                    try:
                        os.remove(ts_file)
                        log(f"   🗑️ Removed partial download")
                    except:
                        pass
                
                downloader = HLSDownloader(8)  # 8 workers for stability
                download_result = downloader.download(video_data.m3u8_url, ts_file, code)
                
                if download_result:
                    size_gb = os.path.getsize(ts_file) / (1024**3)
                    log(f"✅ Downloaded: {size_gb:.2f}GB")
                    download_success = True
                    break
                else:
                    # Download failed
                    log(f"❌ Download attempt {download_attempt} failed")
                    
                    if download_attempt < max_download_attempts:
                        log(f"🔄 Restarting browser for fresh retry...")
                        
                        # Close current browser
                        try:
                            if hasattr(scraper, 'driver') and scraper.driver:
                                scraper.driver.quit()
                                log(f"   ✓ Browser closed")
                        except Exception as e:
                            log(f"   ⚠️ Browser close warning: {e}")
                        
                        # Wait before restart
                        wait_time = 10
                        log(f"   Waiting {wait_time}s before restart...")
                        time.sleep(wait_time)
                        
                        # Reinitialize browser
                        try:
                            scraper.init_driver()
                            log(f"   ✅ Browser restarted - starting fresh download")
                        except Exception as e:
                            log(f"   ⚠️ Browser restart warning: {e}")
                        
                        # Wait a bit more before retry
                        time.sleep(5)
                    else:
                        error_msg = f"Download failed after {max_download_attempts} attempts (1 initial + 2 retries)"
                        log(f"❌ {error_msg}")
                        log(f"⏭️ Moving on to next video...")
                        mark_as_failed(url, error_msg)
                        return False
                        
            except Exception as e:
                error_msg = f"Download exception: {str(e)[:100]}"
                log(f"❌ {error_msg}")
                
                if download_attempt < max_download_attempts:
                    log(f"🔄 Restarting browser after exception...")
                    
                    # Close current browser
                    try:
                        if hasattr(scraper, 'driver') and scraper.driver:
                            scraper.driver.quit()
                            log(f"   ✓ Browser closed")
                    except:
                        pass
                    
                    # Wait and restart
                    time.sleep(10)
                    try:
                        scraper.init_driver()
                        log(f"   ✅ Browser restarted")
                    except:
                        pass
                    
                    time.sleep(5)
                else:
                    mark_as_failed(url, error_msg)
                    return False
        
        if not download_success:
            error_msg = f"Download failed after {max_download_attempts} attempts with browser restarts"
            log(f"❌ {error_msg}")
            mark_as_failed(url, error_msg)
            return False
        
        # Check disk space before conversion
        has_space, free_gb, _ = check_disk_space(min_free_gb=2)
        if not has_space:
            error_msg = f"Low disk space before conversion: {free_gb:.1f}GB"
            log(f"❌ {error_msg}")
            cleanup_temp_files(code, TEMP_DIR)
            mark_as_failed(url, error_msg)
            return False
        
        # STEP 3: Convert to MP4
        log("\n🔄 Step 3: Converting to MP4...")
        try:
            if not convert_to_mp4(ts_file, mp4_file):
                error_msg = "Conversion failed"
                log(f"❌ {error_msg}")
                cleanup_temp_files(code, TEMP_DIR)
                mark_as_failed(url, error_msg)
                return False
            log("✅ Converted")
        except Exception as e:
            error_msg = f"Conversion exception: {str(e)[:100]}"
            log(f"❌ {error_msg}")
            cleanup_temp_files(code, TEMP_DIR)
            mark_as_failed(url, error_msg)
            return False
        
        # Check disk space before upload
        has_space, free_gb, _ = check_disk_space(min_free_gb=1)
        if not has_space:
            error_msg = f"Low disk space before upload: {free_gb:.1f}GB"
            log(f"❌ {error_msg}")
            cleanup_temp_files(code, TEMP_DIR)
            mark_as_failed(url, error_msg)
            return False
        
        # STEP 4: Upload to hosts
        log("\n📤 Step 4: Uploading to StreamWish...")
        try:
            # Verify MP4 file before upload
            if not os.path.exists(mp4_file):
                error_msg = "MP4 file not found before upload"
                log(f"❌ {error_msg}")
                cleanup_temp_files(code, TEMP_DIR)
                mark_as_failed(url, error_msg)
                return False
            
            mp4_size_gb = os.path.getsize(mp4_file) / (1024**3)
            log(f"   MP4 file size: {mp4_size_gb:.2f} GB")
            
            if mp4_size_gb < 0.1:  # Less than 100 MB
                error_msg = f"MP4 file too small ({mp4_size_gb:.2f} GB) - likely incomplete"
                log(f"❌ {error_msg}")
                cleanup_temp_files(code, TEMP_DIR)
                mark_as_failed(url, error_msg)
                return False
            
            log("   Calling upload_all()...")
            sys.stdout.flush()
            
            upload_results = upload_all(mp4_file, code, video_data.title, video_data)
            
            log(f"   upload_all() returned successfully")
            sys.stdout.flush()
            
            if not upload_results:
                error_msg = "Upload failed - upload_all returned None"
                log(f"❌ {error_msg}")
                cleanup_temp_files(code, TEMP_DIR)
                mark_as_failed(url, error_msg)
                return False
            
            # Check for rate limit
            if upload_results.get('rate_limited'):
                wait_until = upload_results.get('wait_until')
                wait_seconds = upload_results.get('wait_seconds', 24 * 3600)
                fallback_used = upload_results.get('fallback_used')
                
                log(f"\n🚫 ═══════════════════════════════════════════════════")
                log(f"🚫 STREAMWISH UPLOAD LIMIT REACHED!")
                log(f"🚫 ═══════════════════════════════════════════════════")
                log(f"   Error: {upload_results.get('error_msg', 'Upload quota exceeded')}")
                log(f"   Wait time: {wait_seconds / 3600:.1f} hours")
                
                from datetime import datetime, timedelta
                resume_time = datetime.fromtimestamp(wait_until)
                log(f"   Resume at: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Check if fallback succeeded
                if fallback_used and upload_results.get('successful'):
                    log(f"\n✅ ═══════════════════════════════════════════════════")
                    log(f"✅ FALLBACK UPLOAD SUCCESSFUL: {fallback_used}")
                    log(f"✅ ═══════════════════════════════════════════════════")
                    log(f"   Video uploaded to {fallback_used} instead")
                    log(f"   StreamWish will be available again at: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Save rate limit info but continue processing
                    rate_limit_file = "database/rate_limit.json"
                    try:
                        import json
                        with open(rate_limit_file, 'w') as f:
                            json.dump({
                                'wait_until': wait_until,
                                'wait_seconds': wait_seconds,
                                'detected_at': time.time(),
                                'error_msg': upload_results.get('error_msg', 'Upload quota exceeded'),
                                'video_code': code,
                                'fallback_used': fallback_used
                            }, f, indent=2)
                        log(f"   ✓ Rate limit info saved (workflow will continue with {fallback_used})")
                    except Exception as e:
                        log(f"   ⚠️ Could not save rate limit info: {e}")
                    
                    # Continue with the successful fallback upload
                    # Don't return 'RATE_LIMIT' - let it continue to save the video
                else:
                    # Both StreamWish and fallback failed
                    log(f"\n❌ ═══════════════════════════════════════════════════")
                    log(f"❌ ALL UPLOAD OPTIONS FAILED")
                    log(f"❌ ═══════════════════════════════════════════════════")
                    log(f"   StreamWish: Rate limited")
                    log(f"   {fallback_used or 'Fallback'}: Failed")
                    
                    # Save rate limit info
                    rate_limit_file = "database/rate_limit.json"
                    try:
                        import json
                        with open(rate_limit_file, 'w') as f:
                            json.dump({
                                'wait_until': wait_until,
                                'wait_seconds': wait_seconds,
                                'detected_at': time.time(),
                                'error_msg': upload_results.get('error_msg', 'Upload quota exceeded'),
                                'video_code': code
                            }, f, indent=2)
                        log(f"   ✓ Rate limit info saved")
                    except Exception as e:
                        log(f"   ⚠️ Could not save rate limit info: {e}")
                    
                    # Clean up current video
                    cleanup_temp_files(code, TEMP_DIR)
                    
                    # Return special code to stop workflow
                    return 'RATE_LIMIT'
            
            if not upload_results.get('successful'):
                error_msg = "Upload failed - no successful uploads"
                log(f"❌ {error_msg}")
                cleanup_temp_files(code, TEMP_DIR)
                mark_as_failed(url, error_msg)
                return False
            
            log(f"✅ Uploaded successfully")
            folder_name = None  # Will store the folder name
            
            for r in upload_results['successful']:
                log(f"   {r['service']}: {r['embed_url']}")
                
                # Get folder name from upload result
                if r.get('folder'):
                    folder_name = r['folder']
                
            # Note: StreamWish auto-generates thumbnails from videos
            # Their API doesn't support custom thumbnail uploads (only accepts video files)
            # We keep the original Jable thumbnail URL for reference in the database
            thumbnail_url = video_data.thumbnail_url
            
        except Exception as e:
            error_msg = f"Upload exception: {str(e)[:100]}"
            log(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            cleanup_temp_files(code, TEMP_DIR)
            mark_as_failed(url, error_msg)
            return False
        
        # STEP 5: Save metadata with embed URLs
        log("\n💾 Step 5: Saving to database...")
        try:
            log(f"   Video data code: {video_data.code}")
            log(f"   Video data title: {video_data.title}")
            log(f"   Upload results type: {type(upload_results)}")
            log(f"   Upload results keys: {upload_results.keys() if upload_results else 'None'}")
            log(f"   Upload results: {len(upload_results.get('successful', []))} successful")
            
            # Show detailed upload results
            if upload_results and upload_results.get('successful'):
                for idx, result in enumerate(upload_results['successful']):
                    log(f"   Upload {idx+1}: {result.get('service')} - {result.get('embed_url')}")
            else:
                log(f"   ⚠️ WARNING: No successful uploads to save!")
                log(f"   Upload results full: {upload_results}")
            
            if save_video(video_data, upload_results, thumbnail_url):
                log("✅ Saved to database")
                
                # Verify it was saved
                videos = load_json_safe(DB_FILE, [])
                log(f"   Database now has {len(videos)} videos")
                
                # Show the saved entry
                for v in videos:
                    if v.get('code') == video_data.code:
                        log(f"   ✓ Found saved entry:")
                        log(f"     Code: {v.get('code')}")
                        log(f"     Title: {v.get('title', '')[:50]}")
                        log(f"     Hosting services: {list(v.get('hosting', {}).keys())}")
                        for service, data in v.get('hosting', {}).items():
                            log(f"       {service}: {data.get('embed_url', 'N/A')}")
                        break
                
                # Commit and push to git (if in GitHub Actions)
                log("\n📤 Committing to git...")
                commit_result = commit_database()
                if commit_result:
                    log("✅ Committed and pushed to GitHub")
                else:
                    log("⚠️ Commit failed or no changes")
                
                # STEP 5.5: Enrich with JAVDatabase metadata
                if JAVDB_INTEGRATION_AVAILABLE:
                    log("\n🎭 Step 5.5: Enriching with JAVDatabase metadata...")
                    try:
                        # Import datetime for this scope
                        from datetime import datetime as dt
                        
                        # Build hosting dict in correct format (service_name: data)
                        hosting_dict = {}
                        file_size_from_upload = None
                        upload_folder_from_upload = None
                        
                        if upload_results and upload_results.get('successful'):
                            for result in upload_results['successful']:
                                service = result.get('service', 'unknown').lower()
                                hosting_dict[service] = {
                                    'embed_url': result.get('embed_url', ''),
                                    'watch_url': result.get('watch_url', ''),
                                    'download_url': result.get('download_url', ''),
                                    'direct_url': result.get('direct_url', ''),
                                    'api_url': result.get('api_url', ''),
                                    'filecode': result.get('filecode', ''),
                                    'upload_time': result.get('time', 0),
                                    'uploaded_at': dt.now().isoformat()
                                }
                                # Get file size and folder from first result
                                if not file_size_from_upload and result.get('file_size'):
                                    file_size_from_upload = result.get('file_size')
                                if not upload_folder_from_upload and result.get('folder'):
                                    upload_folder_from_upload = result.get('folder')
                        
                        # Build Jable data structure for enrichment
                        jable_data = {
                            "code": video_data.code,
                            "title": video_data.title,
                            "source_url": video_data.source_url,
                            "thumbnail_url": thumbnail_url,
                            "duration": video_data.duration,
                            "hd_quality": video_data.hd_quality if hasattr(video_data, 'hd_quality') else False,
                            "views": video_data.views,
                            "likes": video_data.likes,
                            "release_date": video_data.release_date,
                            "upload_time": video_data.upload_time if hasattr(video_data, 'upload_time') else '',
                            "processed_at": dt.now().isoformat(),
                            "categories": video_data.categories if video_data.categories else [],
                            "models": video_data.models if video_data.models else [],
                            "tags": video_data.tags if video_data.tags else [],
                            "preview_images": video_data.preview_images if hasattr(video_data, 'preview_images') else [],
                            "hosting": hosting_dict,
                            "file_size": file_size_from_upload,
                            "upload_folder": upload_folder_from_upload or video_data.code
                        }
                        
                        log(f"   Calling JAVDatabase enrichment for {video_data.code}...")
                        success = enrich_with_javdb(jable_data, headless=True)
                        
                        if success:
                            log(f"✅ JAVDatabase enrichment successful")
                            log(f"   Combined data saved to database/combined_videos.json")
                        else:
                            log(f"⚠️ JAVDatabase enrichment failed, using Jable data only")
                            
                    except Exception as e:
                        log(f"❌ JAVDatabase enrichment error: {e}")
                        log(f"   Continuing with Jable data only...")
                else:
                    log("\n⏭️ Skipping JAVDatabase enrichment (not available)")
            else:
                log("❌ Save failed!")
                log("   This video will NOT be committed to database")
        except Exception as e:
            log(f"❌ Save exception: {e}")
            import traceback
            traceback.print_exc()
        
        # STEP 6: Delete video file
        log("\n🗑️ Step 6: Cleaning up...")
        cleanup_temp_files(code, TEMP_DIR)
        
        log("✅ Deleted video file")
        
        log(f"\n✅ VIDEO {num}/{total} COMPLETE!")
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)[:100]}"
        log(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on any exception
        if code:
            cleanup_temp_files(code, TEMP_DIR)
        
        # Clean up thumbnail if it exists locally
        if 'thumbnail_local' in locals() and thumbnail_local and os.path.exists(thumbnail_local):
            try:
                os.remove(thumbnail_local)
                log("🗑️ Cleaned up local thumbnail")
            except:
                pass
        
        mark_as_failed(url, error_msg)
        return False

def main():
    log("""
╔══════════════════════════════════════════════════════════╗
║  CONTINUOUS SCRAPER - COMPLETE WORKFLOW PER VIDEO        ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Clean up caches and temporary files at startup
    log("🧹 Cleaning up caches and temporary files...")
    try:
        import shutil
        
        # Clear Python cache
        if os.path.exists('__pycache__'):
            shutil.rmtree('__pycache__')
            log("   ✓ Cleared __pycache__")
        
        # Clear any .pyc files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
        
        # Clear temp downloads folder
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    log(f"   ⚠️ Could not remove {item}: {e}")
            log(f"   ✓ Cleared {TEMP_DIR}")
        
        # Clear any .lock files
        for file in os.listdir('.'):
            if file.endswith('.lock'):
                try:
                    os.remove(file)
                    log(f"   ✓ Removed {file}")
                except:
                    pass
        
        log("✓ Cleanup complete")
    except Exception as e:
        log(f"⚠️ Cleanup warning: {e}")
    
    # Initialize database if missing
    initialize_database()
    
    # Create process lock to prevent multiple instances
    lock_file = create_process_lock("run_continuous")
    if not lock_file:
        log("❌ Another instance is already running. Exiting.")
        return
    
    # Check if we're in a rate limit period
    rate_limit_file = "database/rate_limit.json"
    if os.path.exists(rate_limit_file):
        try:
            import json
            with open(rate_limit_file, 'r') as f:
                rate_limit_data = json.load(f)
            
            wait_until = rate_limit_data.get('wait_until', 0)
            current_time = time.time()
            
            if current_time < wait_until:
                from datetime import datetime
                resume_time = datetime.fromtimestamp(wait_until)
                wait_hours = (wait_until - current_time) / 3600
                
                log(f"\n🚫 ═══════════════════════════════════════════════════")
                log(f"🚫 STREAMWISH UPLOAD LIMIT STILL ACTIVE")
                log(f"🚫 ═══════════════════════════════════════════════════")
                log(f"   Wait time remaining: {wait_hours:.1f} hours")
                log(f"   Resume at: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
                log(f"   Exiting workflow...")
                
                remove_process_lock(lock_file)
                return
            else:
                # Limit has expired, remove the file
                log("✅ Rate limit period has expired, resuming workflow")
                os.remove(rate_limit_file)
        except Exception as e:
            log(f"⚠️ Error checking rate limit: {e}")
    
    log(f"Time limit: {TIME_LIMIT/3600:.1f} hours")
    log("Workflow: Scrape → Download → Upload → Save → Delete → Next")
    
    # Check existing database
    existing_videos = load_json_safe(DB_FILE, [])
    log(f"\n📊 Database status:")
    log(f"   Already processed: {len(existing_videos)} videos")
    log(f"   Database file: {DB_FILE}")
    
    # Check failed videos
    failed_videos = load_json_safe(FAILED_DB_FILE, [])
    if failed_videos:
        log(f"   Failed videos: {len(failed_videos)} (will retry up to {MAX_RETRIES} times)")
    
    start = time.time()
    success = 0
    failed = 0
    skipped = 0
    
    scraper = None
    
    try:
        scraper = JableScraper(headless=True)
        
        page = 1
        while True:
            elapsed = time.time() - start
            if elapsed > TIME_LIMIT:
                log(f"\n⏰ Time limit reached ({elapsed/3600:.1f}h)")
                break
            
            log(f"\n{'#'*60}")
            log(f"PAGE {page} - Time left: {(TIME_LIMIT-elapsed)/3600:.1f}h")
            log(f"{'#'*60}")
            
            url = f"https://jable.tv/new/" if page == 1 else f"https://jable.tv/new/{page}/"
            log(f"Loading: {url}")
            
            try:
                links = scraper.get_video_links_from_page(url)
            except Exception as e:
                log(f"❌ Page load failed: {e}")
                # Try to recover browser
                log("🔄 Attempting to restart browser...")
                try:
                    scraper.close()
                    time.sleep(5)
                    scraper = JableScraper(headless=True)
                    log("✅ Browser restarted")
                    continue
                except Exception as e2:
                    log(f"❌ Browser restart failed: {e2}")
                    break
            
            if not links:
                log("✅ No more videos")
                break
            
            log(f"✅ Found {len(links)} videos")
            
            for i, video_url in enumerate(links, 1):
                # Check time limit BEFORE starting new video (not during)
                if time.time() - start > TIME_LIMIT:
                    log(f"\n⏰ Time limit reached, stopping before next video")
                    break
                
                if is_processed(video_url):
                    # Extract code from URL for better logging
                    import re
                    code_match = re.search(r'/videos/([^/]+)/?', video_url)
                    code_str = code_match.group(1).upper() if code_match else video_url[-20:]
                    log(f"\n[{i}/{len(links)}] ⏭️ Already processed: {code_str}")
                    skipped += 1
                    continue
                
                log(f"\nStats: {success} success, {failed} failed, {skipped} skipped")
                
                # Process video
                video_success = process_one_video(scraper, video_url, i, len(links))
                
                # Check for rate limit
                if video_success == 'RATE_LIMIT':
                    log("\n🚫 ═══════════════════════════════════════════════════")
                    log("🚫 STOPPING WORKFLOW DUE TO STREAMWISH UPLOAD LIMIT")
                    log("🚫 ═══════════════════════════════════════════════════")
                    log("   The workflow will automatically resume when the limit resets")
                    log("   (GitHub Actions will restart the workflow)")
                    
                    # Close browser
                    try:
                        scraper.close()
                    except:
                        pass
                    
                    # Exit the workflow
                    return
                
                if video_success:
                    success += 1
                    # Close browser after successful video to free memory
                    log("\n🔄 Closing browser to free memory...")
                    try:
                        scraper.close()
                        log("✅ Browser closed")
                    except Exception as e:
                        log(f"⚠️ Browser close warning: {e}")
                    
                    # Start fresh browser for next video
                    log("🔄 Starting fresh browser for next video...")
                    try:
                        scraper = JableScraper(headless=True)
                        log("✅ Fresh browser ready")
                    except Exception as e:
                        log(f"❌ Failed to restart browser: {e}")
                        log("Stopping workflow")
                        break
                else:
                    failed += 1
                    # Also restart browser after failure to ensure clean state
                    log("\n🔄 Restarting browser after failure...")
                    try:
                        scraper.close()
                        time.sleep(2)
                        scraper = JableScraper(headless=True)
                        log("✅ Browser restarted")
                    except Exception as e:
                        log(f"⚠️ Browser restart warning: {e}")
                
                time.sleep(3)
            
            # Check time limit after page
            if time.time() - start > TIME_LIMIT:
                break
            
            page += 1
            if page > 50:
                break
            
            # Restart browser between pages for fresh state
            log("\n🔄 Restarting browser for next page...")
            try:
                scraper.close()
                time.sleep(3)
                scraper = JableScraper(headless=True)
                log("✅ Browser ready for next page")
            except Exception as e:
                log(f"⚠️ Browser restart warning: {e}")
                # Try to continue anyway
                try:
                    scraper = JableScraper(headless=True)
                except:
                    log("❌ Cannot continue without browser")
                    break
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        log("\n⚠️ Stopped by user")
    except Exception as e:
        log(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always close browser and remove lock
        if scraper:
            try:
                scraper.close()
            except:
                pass
        
        remove_process_lock(lock_file)
    
    total_time = time.time() - start
    log(f"\n{'='*60}")
    log(f"COMPLETE!")
    log(f"{'='*60}")
    log(f"✅ Success: {success}")
    log(f"❌ Failed: {failed}")
    log(f"⏭️ Skipped: {skipped}")
    log(f"⏱️ Time: {total_time/3600:.2f}h")
    if success > 0:
        log(f"📊 Avg: {total_time/success/60:.1f} min/video")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⚠️ Stopped by user")
    except Exception as e:
        log(f"\n❌ Fatal: {e}")
        import traceback
        traceback.print_exc()
