#!/usr/bin/env python3
"""
Disk Space Manager - Atomic disk space reservation to prevent race conditions

This module provides atomic disk space reservation to ensure that multiple
concurrent processes don't race for the same free space, which could lead to
disk full errors during downloads.
"""
import os
import json
import time
import shutil
from datetime import datetime
from typing import Dict, Optional
from utils import FileLock


class DiskSpaceManager:
    """Atomic disk space reservation to prevent race conditions"""
    
    def __init__(self, reservation_file: str = "database/disk_reservations.json"):
        """
        Initialize disk space manager
        
        Args:
            reservation_file: Path to JSON file storing reservations
        """
        self.reservation_file = reservation_file
        self.lock_file = reservation_file + ".lock"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(reservation_file) or '.', exist_ok=True)
        
        # Initialize reservation file if it doesn't exist
        if not os.path.exists(reservation_file):
            self._write_reservations({})
    
    def reserve_space(self, size_gb: float, video_code: str) -> bool:
        """
        Atomically reserve disk space for a download.
        
        This method uses file locking to ensure that only one process can
        reserve space at a time, preventing race conditions where multiple
        processes might think they have enough space.
        
        Args:
            size_gb: Required space in GB
            video_code: Video identifier for tracking
            
        Returns:
            True if reservation successful, False if insufficient space
        """
        lock = FileLock(self.reservation_file)
        
        try:
            # Acquire exclusive lock
            lock.acquire()
            
            # Read current reservations
            reservations = self._read_reservations()
            
            # Calculate available space
            available_gb = self.get_available_space()
            
            # Check if enough space available
            if available_gb < size_gb:
                print(f"⚠️ Insufficient space: {available_gb:.2f}GB available, {size_gb:.2f}GB required")
                return False
            
            # Add reservation
            reservations[video_code] = {
                'size_gb': size_gb,
                'timestamp': time.time(),
                'pid': os.getpid()
            }
            
            # Write reservations atomically
            self._write_reservations(reservations)
            
            print(f"✓ Reserved {size_gb:.2f}GB for {video_code}")
            return True
            
        finally:
            lock.release()
    
    def release_space(self, video_code: str):
        """
        Release reserved space after download completes or fails
        
        Args:
            video_code: Video identifier
        """
        lock = FileLock(self.reservation_file)
        
        try:
            lock.acquire()
            
            reservations = self._read_reservations()
            
            if video_code in reservations:
                size_gb = reservations[video_code]['size_gb']
                del reservations[video_code]
                self._write_reservations(reservations)
                print(f"✓ Released {size_gb:.2f}GB for {video_code}")
            
        finally:
            lock.release()
    
    def get_available_space(self) -> float:
        """
        Get actual available space minus all reservations
        
        Returns:
            Available space in GB
        """
        # Get actual disk free space
        stat = shutil.disk_usage('.')
        disk_free_gb = stat.free / (1024**3)
        
        # Read current reservations
        reservations = self._read_reservations()
        
        # Calculate total reserved
        total_reserved_gb = sum(r['size_gb'] for r in reservations.values())
        
        # Available = disk free - reserved
        available_gb = disk_free_gb - total_reserved_gb
        
        return max(0, available_gb)  # Never return negative
    
    def cleanup_stale_reservations(self, max_age_hours: int = 2):
        """
        Remove reservations older than max_age_hours
        
        This handles cases where a process crashed without releasing its reservation.
        
        Args:
            max_age_hours: Maximum age in hours before considering stale
        """
        lock = FileLock(self.reservation_file)
        
        try:
            lock.acquire()
            
            reservations = self._read_reservations()
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            stale_codes = []
            for code, reservation in reservations.items():
                age_seconds = current_time - reservation['timestamp']
                if age_seconds > max_age_seconds:
                    stale_codes.append(code)
            
            # Remove stale reservations
            for code in stale_codes:
                size_gb = reservations[code]['size_gb']
                age_hours = (current_time - reservations[code]['timestamp']) / 3600
                del reservations[code]
                print(f"🗑️ Removed stale reservation: {code} ({size_gb:.2f}GB, {age_hours:.1f}h old)")
            
            if stale_codes:
                self._write_reservations(reservations)
                print(f"✓ Cleaned up {len(stale_codes)} stale reservations")
            
        finally:
            lock.release()
    
    def get_reservations(self) -> Dict:
        """
        Get current reservations (for debugging/monitoring)
        
        Returns:
            Dictionary of current reservations
        """
        return self._read_reservations()
    
    def print_status(self):
        """Print current disk space status"""
        reservations = self._read_reservations()
        
        stat = shutil.disk_usage('.')
        disk_free_gb = stat.free / (1024**3)
        disk_total_gb = stat.total / (1024**3)
        
        total_reserved_gb = sum(r['size_gb'] for r in reservations.values())
        available_gb = self.get_available_space()
        
        print("\n" + "="*60)
        print("DISK SPACE STATUS")
        print("="*60)
        print(f"Total disk space: {disk_total_gb:.2f} GB")
        print(f"Free disk space: {disk_free_gb:.2f} GB")
        print(f"Reserved space: {total_reserved_gb:.2f} GB")
        print(f"Available space: {available_gb:.2f} GB")
        print(f"Active reservations: {len(reservations)}")
        
        if reservations:
            print("\nReservations:")
            for code, res in reservations.items():
                age_minutes = (time.time() - res['timestamp']) / 60
                print(f"  {code}: {res['size_gb']:.2f}GB ({age_minutes:.1f}m old, PID {res['pid']})")
        
        print("="*60)
    
    def _read_reservations(self) -> Dict:
        """Read reservations from file"""
        try:
            if os.path.exists(self.reservation_file):
                with open(self.reservation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading reservations: {e}")
        return {}
    
    def _write_reservations(self, reservations: Dict):
        """Write reservations to file atomically"""
        try:
            # Write to temp file first
            temp_file = self.reservation_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(reservations, f, indent=2)
            
            # Atomic rename
            if os.path.exists(self.reservation_file):
                os.remove(self.reservation_file)
            os.rename(temp_file, self.reservation_file)
            
        except Exception as e:
            print(f"❌ Error writing reservations: {e}")
            # Clean up temp file
            if os.path.exists(self.reservation_file + '.tmp'):
                try:
                    os.remove(self.reservation_file + '.tmp')
                except:
                    pass


# Global instance
disk_manager = DiskSpaceManager()


if __name__ == "__main__":
    # Test and display status
    print("Testing Disk Space Manager...")
    
    # Clean up stale reservations
    disk_manager.cleanup_stale_reservations()
    
    # Show status
    disk_manager.print_status()
    
    # Test reservation
    print("\nTesting reservation...")
    if disk_manager.reserve_space(1.0, "TEST_VIDEO_001"):
        print("✓ Reservation successful")
        disk_manager.print_status()
        
        print("\nReleasing reservation...")
        disk_manager.release_space("TEST_VIDEO_001")
        disk_manager.print_status()
    else:
        print("✗ Reservation failed")
