#!/usr/bin/env python3
"""
Javmix.TV Batch Scraper - Production Ready
Scrapes all videos from sitemap one by one with full tracking
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from javmix.javmix_scraper import JavmixScraper
from database_manager import db_manager

# Import JAVDatabase enrichment
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'javdatabase'))
    from integrated_pipeline import process_single_video_from_jable
    JAVDB_AVAILABLE = True
    print("✓ JAVDatabase enrichment available")
except ImportError as e:
    JAVDB_AVAILABLE = False
    print(f"⚠️ JAVDatabase enrichment not available: {e}")


class BatchScraper:
    """Production batch scraper with progress tracking"""
    
    def __init__(self, urls_file="sitemap_videos.json", resume=True, enable_javdb=True):
        """
        Initialize batch scraper
        
        Args:
            urls_file: File containing URLs to scrape
            resume: Resume from last position
            enable_javdb: Enable JAVDatabase enrichment
        """
        self.urls_file = urls_file
        self.resume = resume
        self.enable_javdb = enable_javdb and JAVDB_AVAILABLE
        self.scraper = None
        
        if self.enable_javdb:
            print("✓ JAVDatabase enrichment enabled")
        else:
            print("⚠️ JAVDatabase enrichment disabled")
        
        # Load URLs
        self.all_urls = self._load_urls()
        print(f"✓ Loaded {len(self.all_urls):,} URLs from {urls_file}")
        
        # Statistics
        self.stats = {
            'total_urls': len(self.all_urls),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'javdb_enriched': 0,
            'javdb_not_found': 0,
            'start_time': datetime.now().isoformat(),
            'current_url': None,
            'errors': []
        }
    
    def _load_urls(self) -> List[str]:
        """Load URLs from file"""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                urls = data.get('urls', [])
                return urls
        except Exception as e:
            print(f"❌ Error loading URLs: {e}")
            return []
    
    def _is_already_scraped(self, url: str) -> bool:
        """Check if URL is already scraped"""
        return db_manager.is_processed(url=url)
    
    def _save_video_to_database(self, video_data: Dict) -> bool:
        """Save video data to database"""
        try:
            # Add processing timestamp
            video_data['processed_at'] = datetime.now().isoformat()
            
            # Save to database
            success = db_manager.add_or_update_video(video_data)
            
            if success:
                print(f"  💾 Saved to database")
                return True
            else:
                print(f"  ⚠️ Failed to save to database")
                return False
                
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    
    def _check_video_exists(self, url: str) -> bool:
        """Check if video page exists (not deleted/404)"""
        try:
            import requests
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            # Check if page exists
            if response.status_code == 404:
                print(f"  ⚠️ Video deleted (404)")
                return False
            elif response.status_code >= 400:
                print(f"  ⚠️ Video unavailable (status {response.status_code})")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ⚠️ Could not check video: {str(e)[:50]}")
            # If we can't check, assume it exists and let scraper handle it
            return True
    
    def _scrape_single_video(self, url: str, index: int, total: int) -> bool:
        """
        Scrape a single video
        
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"[{index}/{total}] {url}")
        print(f"{'='*70}")
        
        try:
            # Check if video exists first
            if not self._check_video_exists(url):
                print(f"  ❌ SKIPPED - Video deleted or unavailable")
                db_manager.mark_as_failed(url=url, error="Video deleted/unavailable (404)")
                return False
            
            # Initialize scraper if needed
            if self.scraper is None:
                print("🔧 Initializing scraper...")
                self.scraper = JavmixScraper(headless=True)
            
            # Scrape video
            video_data = self.scraper.scrape_video(url)
            
            if video_data:
                # Convert to dict
                video_dict = video_data.__dict__ if hasattr(video_data, '__dict__') else video_data
                
                # Validate video data (must have at least one video URL)
                embed_urls = video_dict.get('embed_urls', {})
                if not embed_urls or len(embed_urls) == 0:
                    print(f"  ⚠️ No video URLs found - video may be deleted")
                    db_manager.mark_as_failed(url=url, error="No video URLs found (deleted?)")
                    return False
                
                # Save to database
                if self._save_video_to_database(video_dict):
                    print(f"  ✅ SUCCESS - Javmix data saved")
                    
                    # Enrich with JAVDatabase if enabled
                    if self.enable_javdb:
                        print(f"\n  🔍 Enriching with JAVDatabase...")
                        try:
                            enriched = process_single_video_from_jable(video_dict, headless=True)
                            if enriched:
                                print(f"  ✅ JAVDatabase enrichment complete")
                                self.stats['javdb_enriched'] += 1
                            else:
                                print(f"  ⚠️ JAVDatabase data not found (will retry later)")
                                self.stats['javdb_not_found'] += 1
                        except Exception as e:
                            print(f"  ⚠️ JAVDatabase enrichment failed: {str(e)[:100]}")
                            self.stats['javdb_not_found'] += 1
                    
                    return True
                else:
                    print(f"  ⚠️ Scraped but failed to save")
                    return False
            else:
                print(f"  ❌ FAILED - No data returned (video may be deleted)")
                db_manager.mark_as_failed(url=url, error="No data returned (deleted?)")
                return False
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)[:100]}")
            traceback.print_exc()
            return False
    
    def _print_progress(self, index: int, total: int):
        """Print progress statistics"""
        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"📊 PROGRESS UPDATE")
        print(f"{'='*70}")
        print(f"Processed: {self.stats['processed']:,} / {total:,} ({self.stats['processed']/total*100:.1f}%)")
        print(f"Successful: {self.stats['successful']:,}")
        print(f"Failed: {self.stats['failed']:,}")
        print(f"Skipped: {self.stats['skipped']:,}")
        
        if self.enable_javdb:
            print(f"\nJAVDatabase Enrichment:")
            print(f"  Enriched: {self.stats['javdb_enriched']:,}")
            print(f"  Not found: {self.stats['javdb_not_found']:,}")
            if self.stats['successful'] > 0:
                enrichment_rate = self.stats['javdb_enriched'] / self.stats['successful'] * 100
                print(f"  Success rate: {enrichment_rate:.1f}%")
        
        if self.stats['processed'] > 0:
            avg_time = elapsed / self.stats['processed']
            remaining = (total - self.stats['processed']) * avg_time
            
            print(f"\nTime:")
            print(f"  Elapsed: {elapsed/3600:.1f} hours")
            print(f"  Avg per video: {avg_time:.1f}s")
            print(f"  Estimated remaining: {remaining/3600:.1f} hours")
            
            success_rate = self.stats['successful'] / self.stats['processed'] * 100
            print(f"\nSuccess rate: {success_rate:.1f}%")
        
        print(f"{'='*70}")
    
    def _save_checkpoint(self, current_index: int):
        """Save checkpoint for resume"""
        checkpoint = {
            'current_index': current_index,
            'stats': self.stats,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open('javmix/batch_checkpoint.json', 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2)
        except:
            pass
    
    def _load_checkpoint(self) -> Optional[int]:
        """Load checkpoint for resume"""
        try:
            if os.path.exists('javmix/batch_checkpoint.json'):
                with open('javmix/batch_checkpoint.json', 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    return checkpoint.get('current_index', 0)
        except:
            pass
        return None
    
    def scrape_all(self, start_index: int = 0, limit: Optional[int] = None, 
                   progress_interval: int = 10):
        """
        Scrape all videos
        
        Args:
            start_index: Start from this index
            limit: Limit number of videos to scrape
            progress_interval: Show progress every N videos
        """
        print("\n" + "="*70)
        print("🚀 BATCH SCRAPER STARTED")
        print("="*70)
        print(f"Total URLs: {len(self.all_urls):,}")
        print(f"Start index: {start_index}")
        print(f"Limit: {limit or 'None (scrape all)'}")
        print(f"Resume: {self.resume}")
        print("="*70)
        
        # Resume from checkpoint if enabled
        if self.resume:
            checkpoint_index = self._load_checkpoint()
            if checkpoint_index is not None and checkpoint_index > start_index:
                start_index = checkpoint_index
                print(f"📍 Resuming from checkpoint: index {start_index}")
        
        # Determine end index
        end_index = len(self.all_urls)
        if limit:
            end_index = min(start_index + limit, len(self.all_urls))
        
        print(f"\n🎯 Will process: {end_index - start_index:,} videos")
        print(f"   From index: {start_index}")
        print(f"   To index: {end_index - 1}")
        print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            for i in range(start_index, end_index):
                url = self.all_urls[i]
                self.stats['current_url'] = url
                
                # Check if already scraped
                if self._is_already_scraped(url):
                    print(f"\n[{i+1}/{len(self.all_urls)}] ⏭️  SKIPPED (already scraped): {url}")
                    self.stats['skipped'] += 1
                    self.stats['processed'] += 1
                    continue
                
                # Scrape video
                success = self._scrape_single_video(url, i + 1, len(self.all_urls))
                
                # Update stats
                self.stats['processed'] += 1
                if success:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
                    # Mark as failed in database
                    db_manager.mark_as_failed(url=url, error="Scraping failed")
                
                # Save checkpoint
                if self.stats['processed'] % 10 == 0:
                    self._save_checkpoint(i + 1)
                
                # Show progress
                if self.stats['processed'] % progress_interval == 0:
                    self._print_progress(i + 1, len(self.all_urls))
                
                # Small delay between videos
                time.sleep(2)
            
            # Final summary
            self._print_final_summary()
            
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("⚠️  INTERRUPTED BY USER")
            print("="*70)
            self._save_checkpoint(i)
            self._print_final_summary()
            print(f"\n💾 Checkpoint saved. Resume with: --resume")
            
        except Exception as e:
            print(f"\n\n❌ FATAL ERROR: {e}")
            traceback.print_exc()
            self._save_checkpoint(i)
            
        finally:
            # Cleanup
            if self.scraper:
                print("\n🔧 Closing scraper...")
                self.scraper.close()
    
    def _print_final_summary(self):
        """Print final summary"""
        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        
        print("\n\n" + "="*70)
        print("🏁 BATCH SCRAPING COMPLETE")
        print("="*70)
        print(f"\n📊 Final Statistics:")
        print(f"   Total processed: {self.stats['processed']:,}")
        print(f"   Successful: {self.stats['successful']:,}")
        print(f"   Failed: {self.stats['failed']:,}")
        print(f"   Skipped: {self.stats['skipped']:,}")
        
        if self.stats['processed'] > 0:
            success_rate = self.stats['successful'] / self.stats['processed'] * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n⏱️  Time:")
        print(f"   Total time: {elapsed/3600:.2f} hours")
        if self.stats['processed'] > 0:
            print(f"   Avg per video: {elapsed/self.stats['processed']:.1f}s")
        
        print(f"\n💾 Database:")
        db_stats = db_manager.get_stats()
        print(f"   Total videos: {db_stats.get('total_videos', 0):,}")
        
        print("\n" + "="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Javmix.TV Batch Scraper - Production Ready',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape first 10 videos (testing)
  python batch_scraper.py --limit 10
  
  # Scrape first 100 videos
  python batch_scraper.py --limit 100
  
  # Scrape all videos (full run)
  python batch_scraper.py
  
  # Resume from checkpoint
  python batch_scraper.py --resume
  
  # Start from specific index
  python batch_scraper.py --start 1000 --limit 100
  
  # Show progress every 5 videos
  python batch_scraper.py --limit 50 --progress 5
        """
    )
    
    parser.add_argument('--urls', default='sitemap_videos.json', 
                       help='URLs file (default: sitemap_videos.json)')
    parser.add_argument('--start', type=int, default=0, 
                       help='Start index (default: 0)')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of videos to scrape')
    parser.add_argument('--resume', action='store_true', 
                       help='Resume from last checkpoint')
    parser.add_argument('--progress', type=int, default=10, 
                       help='Show progress every N videos (default: 10)')
    parser.add_argument('--no-resume', action='store_true',
                       help='Disable resume (start fresh)')
    parser.add_argument('--enable-javdb', action='store_true', default=True,
                       help='Enable JAVDatabase enrichment (default: enabled)')
    parser.add_argument('--no-javdb', action='store_true',
                       help='Disable JAVDatabase enrichment')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = BatchScraper(
        urls_file=args.urls,
        resume=args.resume and not args.no_resume,
        enable_javdb=args.enable_javdb and not args.no_javdb
    )
    
    # Start scraping
    scraper.scrape_all(
        start_index=args.start,
        limit=args.limit,
        progress_interval=args.progress
    )


if __name__ == "__main__":
    main()
