#!/usr/bin/env python3
"""
Deployment start script for xFGv2
Ensures we run the correct app version
"""

import os
import sys
from pathlib import Path

def main():
    """Start the appropriate app version."""
    
    # Print debug info
    print("🚀 xFGv2 Deployment Start Script")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # List files in current directory
    current_files = list(Path('.').glob('*.py'))
    print(f"Python files found: {[f.name for f in current_files]}")
    
    # Try to import and run the simple app
    try:
        print("Attempting to start web_app_simple.py...")
        import web_app_simple
        # This will run the Flask app
        
    except ImportError as e:
        print(f"❌ Failed to import web_app_simple: {e}")
        
        # Fallback: try to run it directly
        try:
            print("Trying direct execution...")
            os.system("python web_app_simple.py")
        except Exception as e2:
            print(f"❌ Direct execution failed: {e2}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()