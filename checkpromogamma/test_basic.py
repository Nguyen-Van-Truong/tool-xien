#!/usr/bin/env python3
print("Python is working!")
print("Testing basic functionality...")

# Test basic imports
try:
    import json
    print("✓ json imported")
except ImportError:
    print("✗ json import failed")

try:
    import time
    print("✓ time imported")
except ImportError:
    print("✗ time import failed")

try:
    import urllib.request
    print("✓ urllib imported")
except ImportError:
    print("✗ urllib import failed")

print("Basic test completed.")

