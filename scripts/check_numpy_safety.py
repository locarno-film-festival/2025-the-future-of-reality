#!/usr/bin/env python3
"""Check for unsafe numpy operations in code files."""
import sys
import re
from pathlib import Path

def check_file(filepath):
    """Check a single file for unsafe numpy patterns."""
    warnings = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for unsafe numpy float/int conversions
        if re.search(r'\.astype\((?:int|float)\)', content):
            warnings.append(f"Uses unsafe numpy type conversion. Use safe_float() or safe_int() instead.")
        
        # Check for direct numpy array formatting
        if re.search(r'f[\'\"]\{.*\.ndarray.*\}', content):
            warnings.append(f"May have unsafe numpy array formatting.")
            
    except Exception as e:
        warnings.append(f"Error reading file: {e}")
    
    return warnings

def main():
    """Check all provided files."""
    if len(sys.argv) < 2:
        print("No files to check")
        return 0
    
    total_warnings = 0
    
    for filepath in sys.argv[1:]:
        warnings = check_file(filepath)
        if warnings:
            total_warnings += len(warnings)
            print(f"⚠️  {filepath}:")
            for warning in warnings:
                print(f"   {warning}")
    
    if total_warnings == 0:
        print("✅ No unsafe numpy patterns detected")
    
    return 0  # Don't fail the commit, just warn

if __name__ == "__main__":
    sys.exit(main())
