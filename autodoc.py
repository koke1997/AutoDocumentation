#!/usr/bin/env python
import sys
import os

# Add parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(".."))

# Import the main function from the CLI module
from autodocumentation.autodocumentation.cli import main

if __name__ == "__main__":
    sys.exit(main())