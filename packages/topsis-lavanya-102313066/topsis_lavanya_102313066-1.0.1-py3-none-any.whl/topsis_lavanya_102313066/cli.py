#!/usr/bin/env python3
"""
Command-line interface for TOPSIS package.
"""

import sys
from .topsis import topsis


def main():
    """Entry point for CLI."""
    if len(sys.argv) != 5:
        print("Usage: topsis-cli <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("\nExample:")
        print("  topsis-cli data.csv \"1,1,1,2\" \"+,+,-,+\" output-result.csv")
        print("\nParameters:")
        print("  InputDataFile: CSV file with first column as identifiers")
        print("  Weights: Comma-separated positive numbers (e.g., \"1,1,1,2\")")
        print("  Impacts: Comma-separated + or - (e.g., \"+,+,-,+\")")
        print("  OutputResultFileName: Output file path (required)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]
    
    result = topsis(input_file, weights_str, impacts_str, output_file)
    print("\n" + "="*60)
    print("TOPSIS RESULTS")
    print("="*60)
    print(result.to_string(index=False))
    print("="*60)


if __name__ == '__main__':
    main()
