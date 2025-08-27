#!/usr/bin/env python3
"""
Simple test script to verify favicon access.
"""

import requests
import sys

def test_favicon_access():
    """Test if favicon files are accessible via HTTP."""
    base_url = "https://www.retrofy.info"
    
    favicon_files = [
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
        "android-chrome-192x192.png",
        "android-chrome-512x512.png"
    ]
    
    print("Testing Favicon Access")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print()
    
    results = []
    
    for filename in favicon_files:
        url = f"{base_url}/favicon/{filename}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {filename} - OK ({response.status_code})")
                results.append(True)
            else:
                print(f"❌ {filename} - Error ({response.status_code})")
                results.append(False)
        except Exception as e:
            print(f"❌ {filename} - Exception: {e}")
            results.append(False)
    
    print()
    print("=" * 50)
    print("RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL FAVICONS ARE ACCESSIBLE!")
        print("✅ Your favicon configuration is working correctly")
    else:
        print("⚠️  SOME FAVICONS ARE NOT ACCESSIBLE!")
        print("Please check:")
        print("1. Files exist in /srv/retrofy_images/ on your server")
        print("2. Docker container is restarted")
        print("3. File permissions are correct")
    
    return passed == total

if __name__ == "__main__":
    success = test_favicon_access()
    sys.exit(0 if success else 1)
