#!/usr/bin/env python3
"""
XClipboard Setup Script
Installs all necessary dependencies for the backend
"""

import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("XClipboard Backend Setup")
    print("=" * 60)
    print()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print(f"ERROR: requirements.txt not found at {requirements_file}")
        sys.exit(1)
    
    print("Installing dependencies from requirements.txt...")
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            cwd=script_dir
        )
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("✓ All dependencies installed successfully!")
            print("=" * 60)
            print()
            print("You can now run the backend with:")
            print("  python back/ClipBackend.py")
            print()
            return 0
        else:
            print()
            print("ERROR: Installation failed with exit code", result.returncode)
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
