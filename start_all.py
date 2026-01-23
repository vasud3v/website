"""
Javcore Full Stack Startup Script
Starts both backend and frontend servers in a single terminal

Usage: python start_all.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("=" * 50)
    print("   Starting Javcore Full Stack")
    print("=" * 50)
    print()

def print_info():
    """Print server information"""
    print()
    print("=" * 50)
    print("   Servers are running!")
    print("=" * 50)
    print("   Backend:  http://localhost:8000")
    print("   Frontend: http://localhost:5173")
    print("=" * 50)
    print()
    print("Press Ctrl+C to stop all servers")
    print()

def start_servers():
    """Start both backend and frontend servers"""
    print_banner()
    
    # Get the root directory
    root_dir = Path(__file__).parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    # Check if directories exist
    if not backend_dir.exists():
        print(f"Error: Backend directory not found at {backend_dir}")
        sys.exit(1)
    
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        sys.exit(1)
    
    print("[1/2] Starting Backend Server...")
    print(f"     Working directory: {backend_dir}")
    print()
    
    try:
        # Start backend process
        backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
        print(f"     Command: {' '.join(backend_cmd)}")
        print()
        
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=str(backend_dir),
            shell=False
        )
        
        # Wait for backend to start
        print("     Waiting for backend to initialize...")
        time.sleep(3)
        
        print()
        print("[2/2] Starting Frontend Dev Server...")
        print(f"     Working directory: {frontend_dir}")
        print()
        
        # Start frontend process
        frontend_cmd = ["npm", "run", "dev"]
        print(f"     Command: {' '.join(frontend_cmd)}")
        print()
        
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=str(frontend_dir),
            shell=True
        )
        
        print_info()
        
        # Keep script running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down servers...")
            backend_process.terminate()
            frontend_process.terminate()
            print("✅ All servers stopped")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            backend_process.terminate()
            frontend_process.terminate()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    start_servers()
