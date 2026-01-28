
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("DEBUG: Starting imports...")

print("DEBUG: Importing JavaGGScraper...")
try:
    from javgg_scraper import JavaGGScraper
    print("DEBUG: JavaGGScraper imported.")
except ImportError as e:
    print(f"DEBUG: JavaGGScraper import failed: {e}")

print("DEBUG: Importing enrich_with_javdb...")
try:
    from javdb_enrichment import enrich_with_javdb
    print("DEBUG: enrich_with_javdb imported.")
except ImportError as e:
    print(f"DEBUG: enrich_with_javdb import failed: {e}")

print("DEBUG: Importing save_video_to_database...")
try:
    from save_to_database import save_video_to_database
    print("DEBUG: save_video_to_database imported.")
except ImportError as e:
    print(f"DEBUG: save_video_to_database import failed: {e}")

print("DEBUG: Importing DatabaseManager...")
try:
    from database_manager import DatabaseManager
    print("DEBUG: DatabaseManager imported.")
except ImportError as e:
    print(f"DEBUG: DatabaseManager import failed: {e}")

# Import preview generator
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools' / 'preview_generator'))
print("DEBUG: Importing PreviewGenerator...")
try:
    from preview_generator import PreviewGenerator
    print("DEBUG: PreviewGenerator imported.")
except ImportError as e:
    print(f"DEBUG: PreviewGenerator import failed: {e}")

# Import upload pipeline
sys.path.insert(0, str(Path(__file__).parent.parent / 'upload_pipeline'))
print("DEBUG: Importing MultiHostUploader...")
try:
    from upload_to_all_hosts import MultiHostUploader
    print("DEBUG: MultiHostUploader imported.")
except ImportError as e:
    print(f"DEBUG: MultiHostUploader import failed: {e}")

print("DEBUG: All imports finished.")
