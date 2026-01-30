#!/usr/bin/env python3
"""Allow running with: python3 -m wardengui or directly"""
import os
import sys

# Add parent directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .cli import main
except ImportError:
    from cli import main

if __name__ == "__main__":
    main()
