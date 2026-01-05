#!/usr/bin/env python3
"""Simple test runner script."""
import sys
import subprocess

def main():
    """Run pytest with appropriate arguments."""
    args = [
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    # Add any additional arguments from command line
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    try:
        result = subprocess.run(args, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: pytest not found. Please install test dependencies:")
        print("  pip install -r requirements-test.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()


