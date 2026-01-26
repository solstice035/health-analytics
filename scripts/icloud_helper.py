#!/usr/bin/env python3
"""
iCloud Helper - Handle iCloud Drive file access properly.

macOS iCloud files can be in various states (placeholder, downloading, available).
This module ensures files are downloaded before accessing them.
"""

import subprocess
import time
import os
from pathlib import Path


def ensure_downloaded(file_path, timeout=30):
    """
    Ensure an iCloud file is fully downloaded before accessing.
    
    Args:
        file_path: Path to the iCloud file
        timeout: Maximum seconds to wait for download
    
    Returns:
        True if file is ready, False if timeout or error
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    # Check if file is a zero-byte placeholder
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check file size
        size = file_path.stat().st_size
        
        if size > 0:
            # File has content, verify it's not still syncing
            try:
                # Try to open it to ensure no lock
                with open(file_path, 'rb') as f:
                    f.read(1)  # Read one byte to test access
                return True
            except (OSError, IOError) as e:
                if "Resource deadlock avoided" in str(e):
                    # File is locked by iCloud, trigger download
                    subprocess.run(['brctl', 'download', str(file_path)], 
                                 capture_output=True)
                    time.sleep(0.5)
                    continue
                else:
                    raise
        else:
            # File is a placeholder, trigger download
            subprocess.run(['brctl', 'download', str(file_path)], 
                         capture_output=True)
            time.sleep(0.5)
    
    return False


def list_available_files(directory, pattern="*.json", ensure_downloaded=True):
    """
    List files in an iCloud directory, optionally ensuring they're downloaded.
    
    Args:
        directory: Path to iCloud directory
        pattern: File pattern (glob)
        ensure_downloaded: If True, ensure files are downloaded
    
    Returns:
        List of Path objects for available files
    """
    directory = Path(directory)
    files = sorted(directory.glob(pattern))
    
    if not ensure_downloaded:
        return files
    
    available = []
    for file_path in files:
        # Skip if zero-byte placeholder
        if file_path.stat().st_size == 0:
            # Trigger download
            subprocess.run(['brctl', 'download', str(file_path)], 
                         capture_output=True)
        
        # Check if accessible
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
            available.append(file_path)
        except (OSError, IOError):
            # Skip files that are locked
            continue
    
    return available


def read_json_safe(file_path, max_retries=3, retry_delay=1.0):
    """
    Safely read a JSON file from iCloud with retry logic.

    Args:
        file_path: Path to JSON file
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries

    Returns:
        Parsed JSON data or None if failed
    """
    import json

    file_path = Path(file_path)

    for attempt in range(max_retries):
        try:
            # Ensure file is downloaded
            if not ensure_downloaded(file_path):
                return None

            # Try to read
            with open(file_path, 'r') as f:
                return json.load(f)

        except (OSError, IOError) as e:
            if "Resource deadlock avoided" in str(e):
                if attempt < max_retries - 1:
                    # Trigger explicit download
                    subprocess.run(['brctl', 'download', str(file_path)],
                                 capture_output=True)
                    time.sleep(retry_delay)
                    continue
                else:
                    # Max retries reached
                    return None
            raise
        except json.JSONDecodeError as e:
            # File might still be syncing
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                # Max retries reached, return None instead of raising
                return None

    return None


def get_icloud_status(file_path):
    """
    Get the iCloud download status of a file.
    
    Returns:
        'downloaded', 'downloading', 'placeholder', or 'unknown'
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return 'unknown'
    
    size = file_path.stat().st_size
    
    if size == 0:
        return 'placeholder'
    
    # Try to read to see if it's locked
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
        return 'downloaded'
    except (OSError, IOError) as e:
        if "Resource deadlock avoided" in str(e):
            return 'downloading'
        return 'unknown'


if __name__ == "__main__":
    # Test the helper functions
    import sys
    
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        print(f"Testing: {test_file}")
        print(f"Status: {get_icloud_status(test_file)}")
        
        if ensure_downloaded(test_file):
            print("✓ File is ready")
            data = read_json_safe(test_file)
            if data:
                print(f"✓ Successfully read JSON ({len(str(data))} chars)")
        else:
            print("✗ Could not download file")
    else:
        print("Usage: python icloud_helper.py <file_path>")
