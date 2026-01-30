#!/usr/bin/env python3
"""
Regenerate JSON files for pickle files containing day_shifts.
New pattern: processing_location_rcpX.Y.json
Location is deduced from coordinates (via location name in filename).
"""

import pickle
import json
import re
import time
from pathlib import Path
from typing import Any

# Import functions from convert_pickle_to_json
import sys
sys.path.insert(0, str(Path(__file__).parent))
from convert_pickle_to_json import (
    make_json_serializable, convert_pickle_to_json,
    extract_processing_and_rcp_from_filename,
    get_location_name_from_coordinates,
    get_coordinates_from_location_name
)


def extract_location_from_filename(filename: str) -> str | None:
    """
    Extract location name from pickle filename.
    
    Args:
        filename: The pickle filename
    
    Returns:
        Location name or None if not found
    """
    # Remove extension
    name = filename.replace('.pickle', '').replace('.pkl', '')
    parts = name.split('_')
    
    # Remove hash if present
    if len(parts) > 1:
        last_part = parts[-1]
        if len(last_part) >= 8 and len(last_part) <= 20 and all(c in '0123456789abcdef' for c in last_part.lower()):
            parts = parts[:-1]
    
    model_keywords = ['ALADIN', 'RACMO', 'CM5', 'CNRM', 'CERFACS', 'rcp2.6', 'rcp4.5', 'rcp8.5']
    location_keywords = ['FRANCE', 'METEO', 'ADAMONT', 'SAFRAN', 'day', 'tasmintasmaxtasprtotprsnhussrsdsrldssfcwindevspsblpot']
    
    # Pattern 1: Location_Model_rcp... (e.g., "Grenoble_RACMO22E_rcp8.5")
    first_part = parts[0] if parts else ''
    first_is_model = any(kw in first_part for kw in model_keywords) if first_part else False
    
    if (first_part and first_part[0].isupper() and len(first_part) < 25 and
            not first_is_model and first_part not in location_keywords):
        if len(parts) >= 2 and any(kw in parts[1] for kw in model_keywords):
            return first_part
    
    # Pattern 2: Model_rcp..._Location
    if parts and any(kw in parts[0] for kw in model_keywords):
        processing_parts = []
        location_parts = []
        found_rcp = False
        
        for part in parts:
            if not location_parts and (any(kw in part for kw in model_keywords) or 'rcp' in part.lower()):
                processing_parts.append(part)
                if 'rcp' in part.lower():
                    found_rcp = True
            elif found_rcp and part[0].isupper() and len(part) < 25 and part not in model_keywords and part not in location_keywords:
                location_parts.append(part)
                break
        
        if location_parts:
            return '_'.join(location_parts)
    
    # Pattern 3: LOCATION_very_long_string...
    if parts:
        location = parts[0]
        if location not in location_keywords and len(location) < 25:
            return location
    
    return None


def regenerate_day_shifts_json_files(data_folder: Path):
    """
    Remove JSON files containing day_shifts and regenerate them with new pattern.
    
    New pattern: processing_location_rcpX.Y.json
    """
    # Step 1: Find and remove JSON files with day_shifts
    print("Step 1: Finding JSON files containing 'day_shifts'...")
    json_files = list(data_folder.glob('*.json'))
    day_shifts_json_files = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                content = f.read()
                if 'day_shifts' in content:
                    day_shifts_json_files.append(json_file)
        except Exception:
            pass
    
    print(f"Found {len(day_shifts_json_files)} JSON files with 'day_shifts'")
    
    # Delete them
    deleted_count = 0
    for json_file in day_shifts_json_files:
        try:
            json_file.unlink()
            deleted_count += 1
            print(f"  Deleted: {json_file.name}")
        except Exception as e:
            print(f"  Error deleting {json_file.name}: {e}")
    
    print(f"Deleted {deleted_count} JSON files\n")
    
    # Step 2: Find pickle files with day_shifts
    print("Step 2: Finding pickle files with 'day_shifts'...")
    pickle_files = list(data_folder.glob('*.pickle')) + list(data_folder.glob('*.pkl'))
    day_shifts_pickle_files = []
    
    for pickle_file in pickle_files:
        try:
            with open(pickle_file, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict) and 'day_shifts' in data:
                    day_shifts_pickle_files.append(pickle_file)
        except Exception:
            pass
    
    print(f"Found {len(day_shifts_pickle_files)} pickle files with 'day_shifts'\n")
    
    # Step 3: Regenerate JSON files with new pattern
    print("Step 3: Regenerating JSON files with new pattern: processing_location_rcpX.Y.json")
    print("="*70)
    
    converted = 0
    failed = 0
    skipped = 0
    
    for pickle_file in sorted(day_shifts_pickle_files):
        try:
            # Extract location from filename
            location_name = extract_location_from_filename(pickle_file.name)
            if not location_name:
                print(f"Skipping {pickle_file.name} (could not extract location)")
                skipped += 1
                continue
            
            # Get coordinates from location name (forward geocoding)
            coords = get_coordinates_from_location_name(location_name)
            if coords:
                lat, lon = coords
                # Reverse geocode to get standardized location name
                standardized_location = get_location_name_from_coordinates(lat, lon, delay_seconds=1.0)
                if standardized_location:
                    location_name = standardized_location
            
            # Extract processing and RCP
            processing, rcp = extract_processing_and_rcp_from_filename(pickle_file.name)
            
            if processing == 'unknown' or rcp == 'unknown':
                print(f"Skipping {pickle_file.name} (could not extract processing/RCP)")
                skipped += 1
                continue
            
            # Generate new filename: processing_location_rcpX.Y.json
            new_json_filename = f"{processing}_{location_name}_rcp{rcp}.json"
            new_json_path = data_folder / new_json_filename
            
            # Skip if already exists
            if new_json_path.exists():
                print(f"Skipping {pickle_file.name} (JSON file already exists: {new_json_filename})")
                skipped += 1
                continue
            
            # Convert pickle to JSON
            print(f"Converting {pickle_file.name}...")
            print(f"  -> {new_json_filename}")
            if convert_pickle_to_json(pickle_file, new_json_path):
                print("  ✓ Saved successfully")
                converted += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Error processing {pickle_file.name}: {e}")
            failed += 1
    
    print("="*70)
    print("Regeneration complete:")
    print(f"  - Converted: {converted} files")
    print(f"  - Skipped: {skipped} files")
    print(f"  - Failed: {failed} files")
    print(f"  - Deleted (old JSON files): {deleted_count} files")


if __name__ == '__main__':
    data_folder = Path('data')
    
    if not data_folder.exists():
        print(f"Error: Data folder '{data_folder}' does not exist.")
        sys.exit(1)
    
    regenerate_day_shifts_json_files(data_folder)


