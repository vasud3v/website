"""
Setup Internet Archive credentials
Run this once to configure your Internet Archive account
"""
import os
import sys
from pathlib import Path

def setup_internet_archive():
    """
    Interactive setup for Internet Archive credentials
    """
    print("="*60)
    print("INTERNET ARCHIVE SETUP")
    print("="*60)
    print("\nYou need an Internet Archive account to upload videos.")
    print("Sign up for free at: https://archive.org/account/signup")
    print("\nAfter signing up, you'll need your:")
    print("  1. Email address")
    print("  2. Password")
    print("\nThese will be stored in a .env file (not committed to git)")
    print("="*60)
    
    # Get credentials
    email = input("\nEnter your Internet Archive email: ").strip()
    password = input("Enter your Internet Archive password: ").strip()
    
    if not email or not password:
        print("\n❌ Email and password are required")
        return False
    
    # Create .env file
    env_path = Path(__file__).parent / ".env"
    
    with open(env_path, 'w') as f:
        f.write(f"# Internet Archive Credentials\n")
        f.write(f"IA_EMAIL={email}\n")
        f.write(f"IA_PASSWORD={password}\n")
    
    print(f"\n✓ Credentials saved to {env_path}")
    
    # Configure internetarchive library
    print("\nConfiguring Internet Archive library...")
    
    try:
        import internetarchive as ia
        ia.configure(email, password)
        print("✓ Internet Archive configured successfully")
        
        # Test the configuration
        print("\nTesting connection...")
        session = ia.get_session()
        print(f"✓ Connected as: {session.user_email}")
        
        print("\n" + "="*60)
        print("SETUP COMPLETE!")
        print("="*60)
        print("\nYou can now upload preview videos using:")
        print("  python upload_to_ia.py <video_file> <video_code>")
        print("\nOr batch upload:")
        print("  python upload_to_ia.py --batch <preview_directory>")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        print("\nPlease check your credentials and try again.")
        return False


if __name__ == "__main__":
    # Check if internetarchive is installed
    try:
        import internetarchive
    except ImportError:
        print("❌ internetarchive library not installed")
        print("\nInstall it with:")
        print("  pip install internetarchive")
        sys.exit(1)
    
    setup_internet_archive()
