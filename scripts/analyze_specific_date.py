#!/usr/bin/env python3
"""
Analyze a specific date's health data.
Usage: python analyze_specific_date.py 2026-01-20
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import iCloud helper
try:
    from icloud_helper import read_json_safe, get_icloud_status
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from icloud_helper import read_json_safe, get_icloud_status

HEALTH_DATA_PATH = Path(__file__).parent.parent / "data"

def analyze_date(date_str):
    """Analyze health data for a specific date."""
    file_path = HEALTH_DATA_PATH / f"HealthAutoExport-{date_str}.json"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path.name}")
        return
    
    print(f"📊 Analyzing: {file_path.name}")
    
    # Check iCloud status
    status = get_icloud_status(file_path)
    print(f"   iCloud status: {status}")
    
    # Use safe reading with iCloud handling
    data = read_json_safe(file_path)
    
    if data is None:
        print(f"❌ Could not read file (may still be syncing from iCloud)")
        print(f"   Try: brctl download {file_path}")
        return
    
    print(f"\n🔑 Top-level keys: {', '.join(data.keys())}")
    
    # Analyze metrics
    if 'data' in data:
        print(f"\n📈 Available Metrics:")
        for category in data['data'].keys():
            print(f"  • {category}")
            if isinstance(data['data'][category], dict):
                for metric in list(data['data'][category].keys())[:5]:
                    print(f"    - {metric}")
                if len(data['data'][category]) > 5:
                    print(f"    ... and {len(data['data'][category]) - 5} more")
    
    # Try to extract some interesting stats
    if 'data' in data and 'metrics' in data['data']:
        metrics = data['data']['metrics']
        
        interesting = [
            'step_count',
            'active_energy',
            'resting_heart_rate',
            'sleep_analysis',
            'distance_walking_running',
            'flights_climbed'
        ]
        
        print(f"\n📊 Daily Summary:")
        for key in interesting:
            if key in metrics and isinstance(metrics[key], list) and metrics[key]:
                values = metrics[key]
                if isinstance(values[0], dict) and 'qty' in values[0]:
                    total = sum(float(v['qty']) for v in values if 'qty' in v)
                    print(f"  • {key}: {total:.1f}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        # Default to a week ago
        date = "2026-01-20"
    
    analyze_date(date)
