#!/usr/bin/env python3
"""
Convert all pickle files to JSON files named proc_location.json
where location comes from pickle_drias_correspondence.json
If location is missing, extract it from coordinates using reverse geocoding.
"""

import pickle
import json
import time
from pathlib import Path
from typing import Any

try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    Nominatim = None


def convert_pickle_to_json(pickle_path: Path, json_path: Path) -> bool:
    """
    Convert a pickle file to JSON format.
    
    Args:
        pickle_path: Path to the pickle file
        json_path: Path where the JSON file will be saved
    
    Returns:
        True if conversion was successful, False otherwise
    """
    try:
        # Load the pickle file
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        
        # Convert to JSON-serializable format
        json_data = make_json_serializable(data)
        
        # Save as JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        return True
    except Exception as e:
        print(f"  Error converting {pickle_path.name}: {e}")
        return False


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert an object to JSON-serializable format.
    """
    import numpy as np
    from datetime import datetime, date
    
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif hasattr(obj, '__dict__'):
        # Try to convert custom objects to dict
        try:
            obj_dict = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    obj_dict[key] = make_json_serializable(value)
            return {
                '__class__': obj.__class__.__name__,
                '__module__': getattr(obj.__class__, '__module__', 'unknown'),
                'data': obj_dict
            }
        except Exception:
            return str(obj)
    else:
        # Fallback: convert to string
        return str(obj)


def sanitize_filename_part(text: str) -> str:
    """Sanitize a string to be used as part of a filename."""
    if not text:
        return "unknown"
    # Replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, '_')
    # Remove leading/trailing dots and spaces
    text = text.strip('. ')
    return text or "unknown"


def get_location_name_from_coordinates(latitude: float, longitude: float, delay_seconds: float = 1.0, language: str = 'fr') -> str | None:
    """
    Retrieve the city/location name from latitude and longitude using OpenStreetMap Nominatim.
    
    Args:
        latitude: Latitude in decimal degrees (north is positive)
        longitude: Longitude in decimal degrees (east is positive, west is negative)
        delay_seconds: Delay between API requests to respect rate limits (default: 1.0)
        language: Language for location names (default: 'fr' for French)
    
    Returns:
        Location name (city name) as a string, or None if not found
    """
    if not HAS_GEOPY:
        return None
    
    time.sleep(delay_seconds)  # Respect rate limits - call before API request
    geolocator = Nominatim(user_agent="batem_pickle_converter")
    
    try:
        location = geolocator.reverse((latitude, longitude), language=language, exactly_one=True)
        if location:
            # Try to get city name, fallback to town, village, or address
            address = location.raw.get('address', {})
            city_name = (
                address.get('city') or
                address.get('town') or
                address.get('village') or
                address.get('municipality') or
                address.get('city_district') or
                address.get('county') or
                location.address.split(',')[0]  # Fallback to first part of address
            )
            return city_name
        return None
    except Exception as e:
        print(f"  Error during reverse geocoding for ({latitude}, {longitude}): {e}")
        return None


def main():
    """Convert all pickle files to JSON using correspondence file for location names."""
    data_folder = Path('data')
    correspondence_file = Path('pickle_drias_correspondence.json')
    
    if not data_folder.exists():
        print(f"Error: Data folder '{data_folder}' does not exist.")
        return
    
    if not correspondence_file.exists():
        print(f"Error: Correspondence file '{correspondence_file}' does not exist.")
        return
    
    # Load correspondence file
    print(f"Loading correspondence file: {correspondence_file}")
    with open(correspondence_file, 'r', encoding='utf-8') as f:
        correspondence = json.load(f)
    
    # Create a lookup: pickle filename -> entry
    pickle_lookup = {}
    for entry in correspondence['pickle_files']:
        filename = entry['filename']
        pickle_lookup[filename] = entry
    
    # Create a lookup: pickle filename -> matched DRIAS entry (for location fallback)
    match_lookup = {}
    for match in correspondence['matches']:
        pickle_filename = match['pickle_file']
        if pickle_filename not in match_lookup:
            match_lookup[pickle_filename] = match
    
    # Create a lookup: DRIAS filename -> DRIAS entry (for coordinates)
    drias_lookup = {}
    for drias_entry in correspondence['drias_files']:
        filename = drias_entry['filename']
        drias_lookup[filename] = drias_entry
    
    # Find all pickle files
    pickle_files = list(data_folder.glob('*.pickle')) + list(data_folder.glob('*.pkl'))
    
    if not pickle_files:
        print(f"No pickle files found in {data_folder}")
        return
    
    print(f"\nFound {len(pickle_files)} pickle files")
    print("="*70)
    
    converted = 0
    skipped = 0
    failed = 0
    no_location = 0
    
    for pickle_path in sorted(pickle_files):
        pickle_filename = pickle_path.name
        
        # Look up in correspondence
        entry = pickle_lookup.get(pickle_filename)
        
        # Get location
        location = None
        latitude = None
        longitude = None
        
        if entry:
            location = entry.get('location')
            # If location is null, try to get it from matched DRIAS file
            if not location:
                match = match_lookup.get(pickle_filename)
                if match:
                    location = match.get('location')
                    latitude = match.get('latitude')
                    longitude = match.get('longitude')
                    
                    # If still no location but we have coordinates, get location from DRIAS file
                    if not location and (latitude is None or longitude is None):
                        drias_filename = match.get('drias_file')
                        if drias_filename:
                            drias_entry = drias_lookup.get(drias_filename)
                            if drias_entry:
                                latitude = drias_entry.get('latitude')
                                longitude = drias_entry.get('longitude')
                                location = drias_entry.get('location')
        
        # If still no location, try to match by number pattern to DRIAS file
        if not location:
            import re
            # Extract number pattern from pickle filename (e.g., ' 10_', ' 12_', ' 48_')
            match_pattern = re.search(r'\s+(\d+)[_.]', pickle_filename)
            if match_pattern:
                number = match_pattern.group(1)
                # Try to find DRIAS file with this number
                for drias_entry in correspondence['drias_files']:
                    drias_name = drias_entry['filename']
                    # Check if the number appears in the DRIAS filename
                    if number in drias_name and (f' {number}.txt' in drias_name or f' {number}_' in drias_name):
                        location = drias_entry.get('location')
                        latitude = drias_entry.get('latitude')
                        longitude = drias_entry.get('longitude')
                        if location or (latitude is not None and longitude is not None):
                            break
            else:
                # No number pattern - try to match base DRIAS file (without location prefix)
                # Look for DRIAS file that has the same base pattern without location prefix
                base_pattern = 'tasmintasmaxtasprtotprsnhussrsdsrldssfcwindevspsblpot_France_CNRM-CERFACS-CNRM-CM5_CNRM-ALADIN63_rcp8.5_METEO-FRANCE_ADAMONT-France_SAFRAN_day_20060101-21001231.txt'
                for drias_entry in correspondence['drias_files']:
                    drias_name = drias_entry['filename']
                    # Check if it's the exact base file (matches base pattern exactly)
                    if drias_name == base_pattern:
                        location = drias_entry.get('location')
                        latitude = drias_entry.get('latitude')
                        longitude = drias_entry.get('longitude')
                        if location or (latitude is not None and longitude is not None):
                            break
        
        # Get processing/model
        processing = None
        if entry:
            processing = entry.get('model', 'unknown')
        
        # If no location but we have coordinates, use reverse geocoding
        if not location and latitude is not None and longitude is not None:
            print(f"  No location found, extracting from coordinates ({latitude}, {longitude})...")
            if HAS_GEOPY:
                location = get_location_name_from_coordinates(latitude, longitude, delay_seconds=1.0)
                if location:
                    print(f"  ✓ Found location: {location}")
                else:
                    print(f"  ✗ Could not retrieve location name from coordinates")
            else:
                print(f"  ✗ geopy not available, cannot reverse geocode")
        
        # Skip if no location found after all attempts
        if not location:
            print(f"Skipping {pickle_filename} (no location found in correspondence or from coordinates)")
            no_location += 1
            continue
        
        # Sanitize location and processing for filename
        location_sanitized = sanitize_filename_part(location)
        proc_sanitized = sanitize_filename_part(processing)
        
        # Create JSON filename: proc_location.json
        json_filename = f"{proc_sanitized}_{location_sanitized}.json"
        json_path = data_folder / json_filename
        
        # Check if JSON file already exists
        if json_path.exists():
            print(f"Skipping {pickle_filename} (JSON file already exists: {json_filename})")
            skipped += 1
            continue
        
        print(f"Converting {pickle_filename}...")
        print(f"  Location: {location}, Processing: {processing}")
        print(f"  -> {json_filename}")
        
        if convert_pickle_to_json(pickle_path, json_path):
            print("  ✓ Saved successfully")
            converted += 1
        else:
            failed += 1
    
    print("="*70)
    print("Conversion complete:")
    print(f"  - Converted: {converted} files")
    print(f"  - Skipped (already exist): {skipped} files")
    print(f"  - Failed: {failed} files")
    print(f"  - No location found: {no_location} files")
    print(f"  - Total pickle files: {len(pickle_files)}")


if __name__ == '__main__':
    main()

