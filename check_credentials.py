"""
Check NASA credentials from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== NASA Credentials Check ===")
print(f"NASA_EARTHDATA_USERNAME: {os.getenv('NASA_EARTHDATA_USERNAME')}")
print(f"NASA_EARTHDATA_PASSWORD: {'Found' if os.getenv('NASA_EARTHDATA_PASSWORD') else 'Missing'}")
print(f"NASA_EARTHDATA_TOKEN: {'Found' if os.getenv('NASA_EARTHDATA_TOKEN') else 'Missing'}")

# Also check direct file existence
print(f"\n.env file exists: {os.path.exists('.env')}")

# Test our config loader
try:
    from app.collectors.config import load_config
    config = load_config()
    print(f"\nConfig loader results:")
    print(f"Username: {config.nasa_username}")
    print(f"Password: {'Found' if config.nasa_password else 'Missing'}")
    print(f"Token: {'Found' if config.nasa_token else 'Missing'}")
except Exception as e:
    print(f"Config loader error: {e}")