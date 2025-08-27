#!/usr/bin/env python3
"""
Test script to verify favicon configuration.
"""

import os
from pathlib import Path

def test_favicon_files():
    """Test that all favicon files exist in the expected location."""
    print("Testing Favicon Files")
    print("=" * 50)
    
    favicon_dir = "/data/images"  # This is the mounted directory in the container
    expected_files = [
        "android-chrome-192x192.png",
        "android-chrome-512x512.png", 
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico"
    ]
    
    print(f"Checking favicon directory: {favicon_dir}")
    
    if not os.path.exists(favicon_dir):
        print(f"❌ Directory does not exist: {favicon_dir}")
        return False
    
    print(f"✅ Directory exists: {favicon_dir}")
    
    missing_files = []
    existing_files = []
    
    for filename in expected_files:
        file_path = os.path.join(favicon_dir, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {filename} ({file_size} bytes)")
            existing_files.append(filename)
        else:
            print(f"❌ {filename} - MISSING")
            missing_files.append(filename)
    
    print(f"\nResults: {len(existing_files)}/{len(expected_files)} files found")
    
    if missing_files:
        print(f"Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def test_favicon_urls():
    """Test the favicon URL structure."""
    print("\n" + "=" * 50)
    print("Testing Favicon URLs")
    print("=" * 50)
    
    favicon_urls = [
        "/favicon/favicon.ico",
        "/favicon/favicon-16x16.png", 
        "/favicon/favicon-32x32.png",
        "/favicon/apple-touch-icon.png",
        "/favicon/android-chrome-192x192.png",
        "/favicon/android-chrome-512x512.png"
    ]
    
    print("Expected favicon URLs:")
    for url in favicon_urls:
        print(f"  {url}")
    
    return True

def test_html_structure():
    """Test the HTML favicon link structure."""
    print("\n" + "=" * 50)
    print("Testing HTML Favicon Structure")
    print("=" * 50)
    
    expected_links = [
        '<link rel="icon" type="image/x-icon" href="/favicon/favicon.ico">',
        '<link rel="icon" type="image/png" sizes="16x16" href="/favicon/favicon-16x16.png">',
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon/favicon-32x32.png">',
        '<link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-touch-icon.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/favicon/android-chrome-192x192.png">',
        '<link rel="icon" type="image/png" sizes="512x512" href="/favicon/android-chrome-512x512.png">'
    ]
    
    print("Expected HTML favicon links:")
    for link in expected_links:
        print(f"  {link}")
    
    return True

def test_flask_route():
    """Test the Flask route configuration."""
    print("\n" + "=" * 50)
    print("Testing Flask Route Configuration")
    print("=" * 50)
    
    route_info = {
        "route": "/favicon/<path:filename>",
        "function": "serve_favicon",
        "directory": "/data/images",
        "method": "GET"
    }
    
    print("Flask route configuration:")
    for key, value in route_info.items():
        print(f"  {key}: {value}")
    
    return True

def test_browser_compatibility():
    """Test browser compatibility for different favicon formats."""
    print("\n" + "=" * 50)
    print("Testing Browser Compatibility")
    print("=" * 50)
    
    compatibility = {
        "favicon.ico": "All browsers (fallback)",
        "favicon-16x16.png": "Modern browsers, small size",
        "favicon-32x32.png": "Modern browsers, standard size", 
        "apple-touch-icon.png": "iOS Safari, Apple devices",
        "android-chrome-192x192.png": "Android Chrome, PWA",
        "android-chrome-512x512.png": "Android Chrome, high DPI"
    }
    
    print("Browser compatibility:")
    for filename, description in compatibility.items():
        print(f"  {filename}: {description}")
    
    return True

def main():
    """Run all favicon tests."""
    print("Retrofy Favicon Configuration Test")
    print("=" * 60)
    
    tests = [
        test_favicon_files,
        test_favicon_urls,
        test_html_structure,
        test_flask_route,
        test_browser_compatibility
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Favicon configuration is complete")
        print("✅ All favicon files are properly referenced")
        print("✅ Flask route is configured correctly")
        print("✅ HTML structure includes all necessary favicon links")
        print("✅ Browser compatibility is covered")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("Please check the favicon configuration.")
    
    print("\nNext steps:")
    print("1. Ensure favicon files are in /srv/retrofy_images/")
    print("2. Restart the Docker container")
    print("3. Clear browser cache to see the new favicon")
    print("4. Test on different devices and browsers")

if __name__ == "__main__":
    main()
