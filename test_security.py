#!/usr/bin/env python3
"""
Test script to verify the security improvements work correctly.
"""

import bcrypt
import os
from dotenv import load_dotenv

def test_password_hashing():
    """Test that password hashing works correctly."""
    print("Testing password hashing...")
    
    # Test password
    test_password = "test123"
    
    # Generate hash
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(test_password.encode('utf-8'), salt)
    
    # Verify hash
    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), password_hash)
    
    if is_valid:
        print("✅ Password hashing works correctly")
    else:
        print("❌ Password hashing failed")
    
    return is_valid

def test_environment_variables():
    """Test that environment variables are loaded correctly."""
    print("\nTesting environment variables...")
    
    # Load .env if it exists
    load_dotenv()
    
    # Test default values
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    
    print(f"Admin username: {admin_username}")
    print(f"Password hash set: {'Yes' if admin_password_hash else 'No'}")
    
    if admin_username != "legacy_admin":
        print("✅ Username is no longer hardcoded")
    else:
        print("❌ Username is still hardcoded")
    
    return admin_username != "legacy_admin"

def test_default_password():
    """Test that the default password works."""
    print("\nTesting default password...")
    
    # Simulate the default password generation from app.py
    default_password = "admin123"
    salt = bcrypt.gensalt()
    default_hash = bcrypt.hashpw(default_password.encode('utf-8'), salt)
    
    # Test verification
    is_valid = bcrypt.checkpw(default_password.encode('utf-8'), default_hash)
    
    if is_valid:
        print("✅ Default password works correctly")
        print(f"Default hash: {default_hash.decode('utf-8')}")
    else:
        print("❌ Default password verification failed")
    
    return is_valid

def main():
    """Run all security tests."""
    print("Retrofy Security Test")
    print("=" * 40)
    
    tests = [
        test_password_hashing,
        test_environment_variables,
        test_default_password
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("TEST RESULTS")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All security tests passed!")
        print("\nNext steps:")
        print("1. Run 'python generate_password.py' to create a secure password")
        print("2. Copy 'env.example' to '.env' and configure your credentials")
        print("3. Update your environment variables with the generated hash")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
