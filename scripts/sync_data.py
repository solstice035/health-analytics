#!/usr/bin/env python3
"""
Sync health data from iCloud to local directory.
Creates stable copies for analysis.
"""

import shutil
from pathlib import Path
from datetime import datetime
import sys

# Source and destination paths
SOURCE_PATH = Path.home() / "Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/JSON"
DEST_PATH = Path.home() / "clawd/projects/health-analytics/data"

def sync_health_data(force=False):
    """Copy health data files from iCloud to local directory."""
    print("🔄 Syncing health data from iCloud...")
    
    if not SOURCE_PATH.exists():
        print(f"❌ Source path not found: {SOURCE_PATH}")
        return 1
    
    # Ensure destination exists
    DEST_PATH.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files
    source_files = list(SOURCE_PATH.glob("HealthAutoExport-*.json"))
    
    if not source_files:
        print("❌ No health data files found")
        return 1
    
    print(f"📊 Found {len(source_files)} files in iCloud")
    
    copied = 0
    skipped = 0
    failed = 0
    
    for source_file in sorted(source_files):
        dest_file = DEST_PATH / source_file.name
        
        # Skip if already exists and not forcing
        if dest_file.exists() and not force:
            skipped += 1
            continue
        
        try:
            shutil.copy2(source_file, dest_file)
            copied += 1
            
            # Show progress every 25 files
            if copied % 25 == 0:
                print(f"  ✓ Copied {copied} files...")
                
        except Exception as e:
            print(f"  ⚠️  Failed to copy {source_file.name}: {e}")
            failed += 1
    
    print(f"\n✅ Sync complete:")
    print(f"  • Copied: {copied}")
    print(f"  • Skipped: {skipped} (already exist)")
    print(f"  • Failed: {failed}")
    print(f"\n📁 Local data: {DEST_PATH}")
    
    return 0

if __name__ == "__main__":
    force = "--force" in sys.argv
    sys.exit(sync_health_data(force))
