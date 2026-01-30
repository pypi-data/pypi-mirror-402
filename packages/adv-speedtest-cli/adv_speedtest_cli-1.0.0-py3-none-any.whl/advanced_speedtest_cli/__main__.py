#!/usr/bin/env python3
"""
Command-line entry point for Advanced Speedtest CLI
This module imports and runs the main speedtest application.
"""

import sys
import os

# Add parent directory to path to import speedtest module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speedtest import main

if __name__ == "__main__":
    main()
