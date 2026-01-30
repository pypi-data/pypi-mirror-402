#!/usr/bin/env python3
"""
Convert pickle files from the data folder to JSON files.

This script finds all .pickle and .pkl files in the data folder and converts them
to JSON format while keeping the original pickle files intact.
"""

import pickle
import json
import re
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

    Handles:
    - dict, list, tuple -> converted appropriately
    - numpy arrays -> converted to lists
    - datetime objects -> converted to ISO format strings
    - complex objects -> converted to dict with __class__ and attributes
    - Other types -> converted to string representation
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


def extract_location_and_processing(filename: str) -> tuple[str, str]:
    """
    Extract location and processing information from pickle filename.

    Examples:
    - "Grenoble_ALADIN63_rcp8.5_1016445602454680974.pickle" -> ("Grenoble", "ALADIN63_rcp8.5")
    - "ALADIN63_rcp8.5_Lille_46797e06c39a2623.pickle" -> ("Lille", "ALADIN63_rcp8.5")
    - "ALLOUE_tasmintas..._6f5ca263e91bde02.pickle" -> ("ALLOUE", "ALADIN63_rcp8.5")
    - "Carcassonne_ALADIN63_rcp8.5_hash.pickle" -> ("Carcassonne", "ALADIN63_rcp8.5")

    Args:
        filename: The pickle filename (without path)

    Returns:
        Tuple of (location, processing) strings
    """
    # Remove extension
    name = filename.replace('.pickle', '').replace('.pkl', '')

    # Remove hash suffix (last part after underscore that looks like a hash)
    parts = name.split('_')
    if len(parts) > 1:
        last_part = parts[-1]
        # If last part looks like a hash (hex string, 8-16 chars), remove it
        if len(last_part) >= 8 and len(last_part) <= 20 and all(c in '0123456789abcdef' for c in last_part.lower()):
            name = '_'.join(parts[:-1])
            parts = name.split('_')

    # Known model/processing keywords to identify processing information
    model_keywords = ['ALADIN', 'RACMO', 'CM5', 'CNRM', 'CERFACS', 'rcp2.6', 'rcp4.5', 'rcp8.5']
    location_keywords = ['FRANCE', 'METEO', 'ADAMONT', 'SAFRAN', 'day']

    # Pattern 1: "Location_Model_rcp..." (e.g., "Grenoble_ALADIN63_rcp8.5")
    # Check if first part looks like a location (capitalized, reasonable length, not a model keyword)
    first_part = parts[0] if parts else ''
    first_is_model = any(kw in first_part for kw in model_keywords) if first_part else False
    if (first_part and first_part[0].isupper() and len(first_part) < 25 and
            not first_is_model and first_part not in location_keywords):
        # Check if second part is a model
        if len(parts) >= 2 and any(kw in parts[1] for kw in model_keywords):
            location = first_part
            # Extract processing: look for model and rcp pattern
            processing_parts = []
            for i, part in enumerate(parts[1:], 1):
                if any(kw in part for kw in model_keywords) or 'rcp' in part.lower():
                    # Take this part and potentially next parts that are related
                    processing_parts.append(part)
                    # If next part is rcpX.X, include it
                    if i + 1 < len(parts) and 'rcp' in parts[i + 1].lower():
                        processing_parts.append(parts[i + 1])
                        break
                    elif 'rcp' in part.lower():
                        break
            processing = '_'.join(processing_parts) if processing_parts else '_'.join(parts[1:3])
            return location, processing

    # Pattern 2: "Model_rcp..._Location" (e.g., "ALADIN63_rcp8.5_Lille")
    # Look for model at the start
    if parts and any(kw in parts[0] for kw in model_keywords):
        # Extract processing (model + rcp)
        processing_parts = []
        location_parts = []
        found_rcp = False

        for part in parts:
            # Check if this is part of processing (model or rcp)
            if not location_parts and (any(kw in part for kw in model_keywords) or 'rcp' in part.lower()):
                processing_parts.append(part)
                if 'rcp' in part.lower():
                    found_rcp = True
            elif found_rcp and part[0].isupper() and len(part) < 25 and part not in model_keywords and part not in location_keywords:
                # After we found rcp, the next capitalized short word is likely the location
                location_parts.append(part)
                break

        if location_parts and processing_parts:
            location = '_'.join(location_parts)
            processing = '_'.join(processing_parts)
            return location, processing

    # Pattern 3: "LOCATION_very_long_processing_string..." (e.g., "ALLOUE_tasmintas...ALADIN63_rcp8.5...")
    # Extract location (first part) and find model/rcp in the string
    if parts:
        location = parts[0]
        # Look for model and rcp in the remaining parts
        processing_parts = []
        for part in parts[1:]:
            if any(kw in part for kw in model_keywords) or 'rcp' in part.lower():
                processing_parts.append(part)
                # If we found rcp, we're done
                if 'rcp' in part.lower():
                    break

        if processing_parts:
            processing = '_'.join(processing_parts)
        else:
            # Fallback: use first two parts after location as processing
            processing = '_'.join(parts[1:3]) if len(parts) > 2 else (parts[1] if len(parts) > 1 else 'processed')

        return location, processing

    # Final fallback
    return 'unknown', 'processed'


def get_location_name_from_coordinates(latitude: float, longitude: float, delay_seconds: float = 1.0, language: str = 'fr') -> str:
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
        raise ImportError("geopy is required for reverse geocoding. Please install it with: pip install geopy")

    time.sleep(delay_seconds)  # Respect rate limits - call before API request
    geolocator = Nominatim(user_agent="batem_pickle_json_converter")

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


def extract_processing_and_rcp_from_filename(filename: str) -> tuple[str, str]:
    """
    Extract processing (model) and RCP scenario from filename.

    Args:
        filename: The pickle or JSON filename

    Returns:
        Tuple of (processing, rcp) strings, e.g., ("RACMO22E", "8.5") or ("CNRM-CERFACS-CNRM-CM5_CNRM-ALADIN63", "8.5")
    """
    # Extract RCP
    rcp_match = re.search(r'rcp(\d\.\d)', filename)
    rcp = rcp_match.group(1) if rcp_match else None

    # Remove extension and hash
    name = filename.replace('.pickle', '').replace('.pkl', '').replace('.json', '')
    parts = name.split('_')

    # Remove hash if present
    if len(parts) > 1:
        last_part = parts[-1]
        if len(last_part) >= 8 and len(last_part) <= 20 and all(c in '0123456789abcdef' for c in last_part.lower()):
            parts = parts[:-1]

    # Extract processing parts (model keywords before RCP)
    model_keywords = ['ALADIN', 'RACMO', 'CM5', 'CNRM', 'CERFACS']
    processing_parts = []
    location_keywords = ['FRANCE', 'METEO', 'ADAMONT', 'SAFRAN', 'day']

    found_rcp = False
    for part in parts:
        if 'rcp' in part.lower():
            found_rcp = True
            break
        if any(kw in part for kw in model_keywords) and part not in location_keywords:
            processing_parts.append(part)

    processing = '_'.join(processing_parts) if processing_parts else 'unknown'
    rcp_str = rcp if rcp else 'unknown'

    return processing, rcp_str


def get_coordinates_from_location_name(location_name: str) -> tuple[float, float] | None:
    """
    Get coordinates from a location name using forward geocoding.

    Args:
        location_name: Name of the location (city name)

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    if not HAS_GEOPY:
        return None

    time.sleep(1.0)  # Respect rate limits
    geolocator = Nominatim(user_agent="batem_pickle_json_converter")

    try:
        location = geolocator.geocode(location_name + ", France", exactly_one=True)
        if location:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        print(f"  Error during geocoding for {location_name}: {e}")
        return None


def cleanup_incorrectly_named_json_files(data_folder: Path, expected_json_filenames: set[str]) -> int:
    """
    Remove JSON files that don't match the expected location_processing.json pattern.

    Args:
        data_folder: Path to the data folder
        expected_json_filenames: Set of expected JSON filenames (location_processing.json format)

    Returns:
        Number of files deleted
    """
    deleted_count = 0
    json_files = list(data_folder.glob('*.json'))

    # Keywords that indicate incorrect location part (model names, long variable strings, etc.)
    incorrect_location_indicators = ['ALADIN63', 'RACMO', 'tasmintasmaxtasprtotprsnhussrsdsrldssfcwindevspsblpot']

    for json_path in json_files:
        json_filename = json_path.name

        # Skip if this is an expected filename
        if json_filename in expected_json_filenames:
            continue

        # Check if filename starts with incorrect location indicators
        should_delete = False
        for indicator in incorrect_location_indicators:
            if json_filename.startswith(f"{indicator}_"):
                should_delete = True
                break

        # Also check for very long location names (likely variable names concatenated)
        # Location names are typically short (under 25 chars), but variable name strings are much longer
        if not should_delete and '_' in json_filename:
            location_part = json_filename.split('_')[0]
            # If location part is very long (likely a variable names string), delete it
            if len(location_part) > 40:
                should_delete = True

        # Also check if filename contains the long variable names string anywhere
        # (even if it starts with a valid location, files with the variable names string are incorrect)
        if not should_delete and 'tasmintasmaxtasprtotprsnhussrsdsrldssfcwindevspsblpot' in json_filename:
            should_delete = True

        if should_delete:
            print(f"Deleting incorrectly named file: {json_filename}")
            try:
                json_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"  Error deleting {json_filename}: {e}")

    return deleted_count


def main():
    pickle_filename = 'prapoutel_ALADIN63_rcp8.5.pickle'  # None

    """Main function to convert all pickle files in the data folder."""
    data_folder = Path('data')

    if not data_folder.exists():
        print(f"Error: Data folder '{data_folder}' does not exist.")
        return

    # Find all pickle files
    pickle_files = list(data_folder.glob('*.pickle')) + list(data_folder.glob('*.pkl'))
    pickle_files = (Path(data_folder, 'prapoutel_ALADIN63_rcp8.5_7aebc7d0db75a82d.pickle'),)    # comment for all# None

    if not pickle_files:
        print(f"No pickle files found in {data_folder}")
        return

    # Build set of expected JSON filenames
    expected_json_filenames = set()
    for pickle_path in pickle_files:
        location, processing = extract_location_and_processing(pickle_path.name)
        json_filename = f"{location}_{processing}.json"
        expected_json_filenames.add(json_filename)

    # Clean up incorrectly named JSON files
    print(f"Found {len(pickle_files)} pickle files to convert")
    print("Cleaning up incorrectly named JSON files...")
    deleted_count = cleanup_incorrectly_named_json_files(data_folder, expected_json_filenames)
    if deleted_count > 0:
        print(f"Deleted {deleted_count} incorrectly named JSON file(s)")
    print(f"{'='*60}")

    converted = 0
    skipped = 0
    failed = 0

    for pickle_path in sorted(pickle_files):
        # Extract location and processing from filename
        location, processing = extract_location_and_processing(pickle_path.name)

        # Skip files where location is the variable names string (these don't have proper location names)
        if location == 'tasmintasmaxtasprtotprsnhussrsdsrldssfcwindevspsblpot' or len(location) > 40:
            print(f"Skipping {pickle_path.name} (no location name in filename)")
            skipped += 1
            continue

        # Create JSON filename: location_processing.json
        json_filename = f"{location}_{processing}.json"
        json_path = data_folder / json_filename

        # Check if JSON file already exists with the correct name
        if json_path.exists():
            print(f"Skipping {pickle_path.name} (JSON file already exists: {json_filename})")
            skipped += 1
            continue

        print(f"Converting {pickle_path.name}...")
        print(f"  -> {json_filename}")
        if convert_pickle_to_json(pickle_path, json_path):
            print("  ✓ Saved successfully")
            converted += 1
        else:
            failed += 1

    print(f"{'='*60}")
    print("Conversion complete:")
    print(f"  - Converted: {converted} files")
    print(f"  - Skipped (already exist): {skipped} files")
    print(f"  - Failed: {failed} files")
    print(f"  - Deleted (incorrectly named): {deleted_count} files")
    print(f"  - Original pickle files: {len(pickle_files)} (all preserved)")


if __name__ == '__main__':
    main()
