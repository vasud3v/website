#!/usr/bin/env python3
"""
Full Automation System for Javmix.TV
Runs 24/7 with automatic:
- Batch scraping of all videos
- New video monitoring
- Error recovery
- Progress reporting
- Automatic restart on failures
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
import subprocess
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import db_manager


class FullAutomation:
    """Full automation system - runs 24/7"""
    
    def __init__(self):
        self.config_file = "javmix/automation_config.json"
        self.load_config()
        
        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'total_runs': 0,
            'total_scraped': 0,
            'total_failed': 0,
            'last_batch_time': None,
            'last_monitor_time': None,
            'errors': []
        }
    
    def load_config(self):
        """Load or create configuration"""
        default_config = {
            # Batch scraping settings
            'batch_enabled': True,
            'batch_size': 100,  # Videos per batch
            'batch_interval_hours': 0,  # 0 = continuous
            'batch_max_retries': 3,
            
            # New video monitoring settings
            'monitor_enabled': True,
            'monitor_interval_minutes': 60,  # Check every hour
            'monitor_max_videos': 10,  # Max videos to scrape per check
            
            # Error handling
            'auto_restart_on_error': True,
            'max_consecutive_errors': 5,
            'error_cooldown_minutes': 10,
            
            # Progress reporting
            'report_interval_minutes': 60,  # Report every hour
            'save_stats_interval_minutes': 10,  # Save stats every 10 min
            
            # Performance
            'delay_between_batches_seconds': 60,
            'delay_between_videos_seconds': 2,
            
            # Limits (0 = unlimited)
            'max_total_videos': 0,  # 0 = scrape all 296,053
            'max_runtime_hours': 0,  # 0 = run forever
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print(f"✓ Loaded config from {self.config_file}")
            except:
                self.config = default_config
                self.save_config()
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save config: {e}")
    
    def save_stats(self):
        """Save statistics"""
        try:
            stats_file = "javmix/automation_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save stats: {e}")
    
    def print_status(self):
        """Print current status"""
        db_stats = db_manager.get_stats()
        progress = db_manager.get_progress()
        
        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        
        print("\n" + "="*70)
        print("📊 AUTOMATION STATUS")
        print("="*70)
        print(f"Runtime: {elapsed/3600:.1f} hours")
        print(f"Total runs: {self.stats['total_runs']}")
        print(f"Total scraped: {self.stats['total_scraped']}")
        print(f"Total failed: {self.stats['total_failed']}")
        
        print(f"\n💾 Database:")
        print(f"   Total videos: {db_stats.get('total_videos', 0):,}")
        print(f"   Processed: {progress.get('total_processed', 0):,}")
        print(f"   Failed: {progress.get('total_failed', 0):,}")
        print(f"   Success rate: {progress.get('success_rate', 0):.1f}%")
        
        print(f"\n⏰ Last Activities:")
        if self.stats['last_batch_time']:
            print(f"   Last batch: {self.stats['last_batch_time']}")
        if self.stats['last_monitor_time']:
            print(f"   Last monitor: {self.stats['last_monitor_time']}")
        
        print("="*70)
    
    def run_batch_scraper(self):
        """Run batch scraper"""
        try:
            print(f"\n{'='*70}")
            print(f"🎬 RUNNING BATCH SCRAPER")
            print(f"{'='*70}")
            print(f"Batch size: {self.config['batch_size']}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run batch scraper
            cmd = [
                'python', 'javmix/batch_scraper.py',
                '--limit', str(self.config['batch_size']),
                '--resume',
                '--progress', '5'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['batch_size'] * 60  # 1 minute per video
            )
            
            if result.returncode == 0:
                print(f"✅ Batch scraper completed successfully")
                self.stats['total_scraped'] += self.config['batch_size']
                self.stats['last_batch_time'] = datetime.now().isoformat()
                return True
            else:
                print(f"⚠️ Batch scraper failed")
                print(f"Error: {result.stderr[:200]}")
                self.stats['total_failed'] += 1
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Batch scraper timeout")
            self.stats['total_failed'] += 1
            return False
        except Exception as e:
            print(f"❌ Batch scraper error: {e}")
            traceback.print_exc()
            self.stats['total_failed'] += 1
            return False
    
    def run_new_video_monitor(self):
        """Run new video monitor and scraper"""
        try:
            print(f"\n{'='*70}")
            print(f"🔍 CHECKING FOR NEW VIDEOS")
            print(f"{'='*70}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check for new videos
            cmd = ['python', 'javmix/monitor_new_videos.py']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ Monitor completed")
                
                # Check if new videos found
                if os.path.exists('javmix/new_videos.json'):
                    with open('javmix/new_videos.json', 'r') as f:
                        data = json.load(f)
                        new_count = data.get('total_new', 0)
                        
                        if new_count > 0:
                            print(f"🆕 Found {new_count} new videos")
                            
                            # Scrape new videos
                            print(f"🎬 Scraping new videos...")
                            scrape_cmd = [
                                'python', 'javmix/auto_scrape_new.py',
                                '--scrape-pending'
                            ]
                            
                            scrape_result = subprocess.run(
                                scrape_cmd,
                                capture_output=True,
                                text=True,
                                timeout=new_count * 60
                            )
                            
                            if scrape_result.returncode == 0:
                                print(f"✅ New videos scraped")
                            else:
                                print(f"⚠️ Failed to scrape new videos")
                        else:
                            print(f"✓ No new videos found")
                
                self.stats['last_monitor_time'] = datetime.now().isoformat()
                return True
            else:
                print(f"⚠️ Monitor failed")
                return False
                
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            traceback.print_exc()
            return False
    
    def check_limits(self):
        """Check if limits reached"""
        # Check max videos
        if self.config['max_total_videos'] > 0:
            db_stats = db_manager.get_stats()
            if db_stats.get('total_videos', 0) >= self.config['max_total_videos']:
                print(f"✅ Reached max videos limit: {self.config['max_total_videos']}")
                return True
        
        # Check max runtime
        if self.config['max_runtime_hours'] > 0:
            elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
            if elapsed / 3600 >= self.config['max_runtime_hours']:
                print(f"✅ Reached max runtime: {self.config['max_runtime_hours']} hours")
                return True
        
        return False
    
    def run_automation(self):
        """Main automation loop"""
        print("\n" + "="*70)
        print("🤖 FULL AUTOMATION STARTED")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Batch scraping: {'Enabled' if self.config['batch_enabled'] else 'Disabled'}")
        print(f"New video monitoring: {'Enabled' if self.config['monitor_enabled'] else 'Disabled'}")
        print(f"Batch size: {self.config['batch_size']} videos")
        print(f"Monitor interval: {self.config['monitor_interval_minutes']} minutes")
        print(f"Max videos: {self.config['max_total_videos'] or 'Unlimited (296,053)'}")
        print(f"Max runtime: {self.config['max_runtime_hours'] or 'Unlimited'} hours")
        print("="*70)
        print("\n⚠️  Press Ctrl+C to stop gracefully")
        print("="*70)
        
        consecutive_errors = 0
        last_report_time = datetime.now()
        last_stats_save = datetime.now()
        last_monitor_time = datetime.now() - timedelta(hours=1)  # Run monitor immediately
        
        try:
            while True:
                self.stats['total_runs'] += 1
                
                # Check limits
                if self.check_limits():
                    print("\n✅ Limits reached, stopping automation")
                    break
                
                # Run batch scraper
                if self.config['batch_enabled']:
                    success = self.run_batch_scraper()
                    
                    if not success:
                        consecutive_errors += 1
                        if consecutive_errors >= self.config['max_consecutive_errors']:
                            print(f"\n⚠️ Too many consecutive errors ({consecutive_errors})")
                            if self.config['auto_restart_on_error']:
                                print(f"⏳ Cooling down for {self.config['error_cooldown_minutes']} minutes...")
                                time.sleep(self.config['error_cooldown_minutes'] * 60)
                                consecutive_errors = 0
                            else:
                                print("❌ Stopping automation")
                                break
                    else:
                        consecutive_errors = 0
                    
                    # Delay between batches
                    if self.config['batch_interval_hours'] > 0:
                        print(f"\n⏳ Waiting {self.config['batch_interval_hours']} hours before next batch...")
                        time.sleep(self.config['batch_interval_hours'] * 3600)
                    else:
                        print(f"\n⏳ Waiting {self.config['delay_between_batches_seconds']}s before next batch...")
                        time.sleep(self.config['delay_between_batches_seconds'])
                
                # Run new video monitor
                if self.config['monitor_enabled']:
                    elapsed_since_monitor = (datetime.now() - last_monitor_time).total_seconds() / 60
                    
                    if elapsed_since_monitor >= self.config['monitor_interval_minutes']:
                        self.run_new_video_monitor()
                        last_monitor_time = datetime.now()
                
                # Print status report
                elapsed_since_report = (datetime.now() - last_report_time).total_seconds() / 60
                if elapsed_since_report >= self.config['report_interval_minutes']:
                    self.print_status()
                    last_report_time = datetime.now()
                
                # Save stats
                elapsed_since_stats = (datetime.now() - last_stats_save).total_seconds() / 60
                if elapsed_since_stats >= self.config['save_stats_interval_minutes']:
                    self.save_stats()
                    last_stats_save = datetime.now()
                
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("⚠️  AUTOMATION STOPPED BY USER")
            print("="*70)
        except Exception as e:
            print(f"\n\n❌ FATAL ERROR: {e}")
            traceback.print_exc()
        finally:
            # Final status
            self.print_status()
            self.save_stats()
            print("\n✅ Automation stopped gracefully")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Full Automation System for Javmix.TV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (100 videos per batch, check new videos every hour)
  python full_automation.py
  
  # Run with custom batch size
  python full_automation.py --batch-size 50
  
  # Run with custom monitor interval
  python full_automation.py --monitor-interval 30
  
  # Run for specific duration
  python full_automation.py --max-runtime 24
  
  # Run until specific number of videos scraped
  python full_automation.py --max-videos 10000
  
  # Disable new video monitoring (batch only)
  python full_automation.py --no-monitor
  
  # Disable batch scraping (monitor only)
  python full_automation.py --no-batch
        """
    )
    
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Videos per batch (default: 100)')
    parser.add_argument('--batch-interval', type=int, default=0,
                       help='Hours between batches, 0=continuous (default: 0)')
    parser.add_argument('--monitor-interval', type=int, default=60,
                       help='Minutes between new video checks (default: 60)')
    parser.add_argument('--max-videos', type=int, default=0,
                       help='Max total videos to scrape, 0=unlimited (default: 0)')
    parser.add_argument('--max-runtime', type=int, default=0,
                       help='Max runtime in hours, 0=unlimited (default: 0)')
    parser.add_argument('--no-batch', action='store_true',
                       help='Disable batch scraping')
    parser.add_argument('--no-monitor', action='store_true',
                       help='Disable new video monitoring')
    
    args = parser.parse_args()
    
    # Create automation
    automation = FullAutomation()
    
    # Update config from args
    automation.config['batch_size'] = args.batch_size
    automation.config['batch_interval_hours'] = args.batch_interval
    automation.config['monitor_interval_minutes'] = args.monitor_interval
    automation.config['max_total_videos'] = args.max_videos
    automation.config['max_runtime_hours'] = args.max_runtime
    automation.config['batch_enabled'] = not args.no_batch
    automation.config['monitor_enabled'] = not args.no_monitor
    automation.save_config()
    
    # Run automation
    automation.run_automation()


if __name__ == "__main__":
    main()
