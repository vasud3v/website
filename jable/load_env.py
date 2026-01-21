"""
Load environment variables from .env file
Use this for local development
"""
import os
from pathlib import Path


def load_env(env_file='.env'):
    """
    Load environment variables from .env file
    
    Args:
        env_file: Path to .env file (default: .env)
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        print(f"⚠️ Warning: {env_file} not found")
        print(f"   Copy .env.example to .env and fill in your API keys")
        return False
    
    print(f"📁 Loading environment from {env_file}")
    
    loaded_count = 0
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value
                loaded_count += 1
                print(f"   ✅ {key}")
    
    print(f"\n✅ Loaded {loaded_count} environment variables")
    return True


def verify_env():
    """Verify all required environment variables are set"""
    required_vars = [
        'STREAMTAPE_LOGIN',
        'STREAMTAPE_API_KEY',
        'LULUSTREAM_API_KEY',
        'STREAMWISH_API_KEY'
    ]
    
    print("\n🔍 Verifying environment variables:")
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 5 chars only for security
            masked = value[:5] + '*' * (len(value) - 5) if len(value) > 5 else '*' * len(value)
            print(f"   ✅ {var} = {masked}")
        else:
            print(f"   ❌ {var} = NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️ Missing {len(missing)} required variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True


if __name__ == "__main__":
    print("="*60)
    print("ENVIRONMENT VARIABLE LOADER")
    print("="*60)
    
    if load_env():
        verify_env()
    else:
        print("\n❌ Failed to load environment variables")
        print("\nTo fix:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env and add your API keys")
        print("3. Run this script again")
