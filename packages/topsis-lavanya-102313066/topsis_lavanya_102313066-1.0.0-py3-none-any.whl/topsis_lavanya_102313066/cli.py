#!/usr/bin/env python3
"""
Command-line interface for TOPSIS package.
"""

import sys
from .topsis import topsis


def main():
    """Entry point for CLI."""
    if len(sys.argv) < 4:
        print("Usage: topsis-cli <input_file> <weights> <impacts> [output_file]")
        print("\nExample:")
        print("  topsis-cli data.csv 1,2,3,2 +,+,-,+ results.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else 'output.csv'
    
    result = topsis(input_file, weights_str, impacts_str, output_file)
    print("\n" + "="*60)
    print("TOPSIS RESULTS")
    print("="*60)
    print(result.to_string(index=False))
    print("="*60)


if __name__ == '__main__':
    main()
