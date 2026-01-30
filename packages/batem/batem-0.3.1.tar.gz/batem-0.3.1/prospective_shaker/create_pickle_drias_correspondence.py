#!/usr/bin/env python3
"""
Create a correspondence/mapping between pickle files in batem_all/data
and DRIAS prospective weather files in the archive folder.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import json


def extract_location_from_filename(filename: str) -> str | None:
    """
    Extract location name from filename.
    
    Args:
        filename: The filename (pickle or DRIAS file)
    
    Returns:
        Location name or None if not found
    """
    # Remove extension
    name = filename.replace('.pickle', '').replace('.pkl', '').replace('.txt', '')
    parts = name.split('_')
    
    # Remove hash if present (for pickle files)
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


def extract_rcp_from_filename(filename: str) -> str | None:
    """Extract RCP scenario from filename."""
    rcp_match = re.search(r'rcp(\d\.\d)', filename, re.IGNORECASE)
    return rcp_match.group(1) if rcp_match else None


def extract_model_from_filename(filename: str) -> str | None:
    """Extract model name from filename."""
    model_keywords = ['RACMO22E', 'ALADIN63', 'CNRM-CM5', 'CNRM-CERFACS-CNRM-CM5']
    
    for model in model_keywords:
        if model in filename:
            return model
    
    # Try pattern matching
    if 'RACMO' in filename:
        return 'RACMO22E'
    if 'ALADIN63' in filename or 'ALADIN' in filename:
        return 'ALADIN63'
    if 'CNRM-CM5' in filename or 'CM5' in filename:
        return 'CNRM-CM5'
    
    return None


def parse_drias_filename(filename: str) -> Dict[str, str | None]:
    """
    Parse DRIAS filename to extract location, model, RCP, etc.
    
    DRIAS filenames typically have format like:
    LOCATION_tasmintas..._France_CNRM-CERFACS-CNRM-CM5_CNRM-ALADIN63_rcp8.5_...
    """
    result = {
        'location': extract_location_from_filename(filename),
        'rcp': extract_rcp_from_filename(filename),
        'model': extract_model_from_filename(filename),
        'filename': filename
    }
    return result


def create_correspondence(data_folder: Path, drias_folder: Path) -> Dict[str, List[Dict]]:
    """
    Create correspondence between pickle files and DRIAS files.
    
    Returns:
        Dictionary with 'pickle_files' and 'drias_files' keys, each containing
        parsed information and a 'matches' key with correspondences
    """
    # Get all pickle files
    pickle_files = list(data_folder.glob('*.pickle')) + list(data_folder.glob('*.pkl'))
    
    # Get all DRIAS files
    drias_files = list(drias_folder.glob('*.txt'))
    
    print(f"Found {len(pickle_files)} pickle files")
    print(f"Found {len(drias_files)} DRIAS files\n")
    
    # Parse pickle files
    pickle_data = []
    for pkl_file in pickle_files:
        parsed = parse_drias_filename(pkl_file.name)
        parsed['file_path'] = str(pkl_file)
        parsed['file_type'] = 'pickle'
        pickle_data.append(parsed)
    
    # Parse DRIAS files
    drias_data = []
    for drias_file in drias_files:
        parsed = parse_drias_filename(drias_file.name)
        parsed['file_path'] = str(drias_file)
        parsed['file_type'] = 'drias'
        drias_data.append(parsed)
    
    # Create matches based on location, RCP, and model
    matches = []
    for pkl_info in pickle_data:
        pkl_location = pkl_info['location']
        pkl_rcp = pkl_info['rcp']
        pkl_model = pkl_info['model']
        
        if not pkl_location:
            continue
        
        # Find matching DRIAS files
        for drias_info in drias_data:
            drias_location = drias_info['location']
            drias_rcp = drias_info['rcp']
            drias_model = drias_info['model']
            
            # Match if location matches (and optionally RCP and model)
            if drias_location and pkl_location.upper() == drias_location.upper():
                match_score = 0
                if pkl_rcp and drias_rcp and pkl_rcp == drias_rcp:
                    match_score += 2
                if pkl_model and drias_model and pkl_model in drias_model:
                    match_score += 1
                
                matches.append({
                    'pickle_file': pkl_info['filename'],
                    'pickle_path': pkl_info['file_path'],
                    'drias_file': drias_info['filename'],
                    'drias_path': drias_info['file_path'],
                    'location': pkl_location,
                    'rcp_pickle': pkl_rcp,
                    'rcp_drias': drias_rcp,
                    'model_pickle': pkl_model,
                    'model_drias': drias_model,
                    'match_score': match_score
                })
    
    # Sort matches by score (higher is better)
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return {
        'pickle_files': pickle_data,
        'drias_files': drias_data,
        'matches': matches
    }


def main():
    data_folder = Path('/Users/stephane/Documents/enseignements/BATEM/batem_all/data')
    drias_folder = Path.home() / 'Documents/recherche/chercheurs/khaled/work/70cities/Drias_1point_10parameters_2006_2100/arch'
    
    if not data_folder.exists():
        print(f"Error: Data folder '{data_folder}' does not exist.")
        return
    
    if not drias_folder.exists():
        print(f"Error: DRIAS folder '{drias_folder}' does not exist.")
        return
    
    print("Creating correspondence between pickle files and DRIAS files...")
    print("="*70)
    
    correspondence = create_correspondence(data_folder, drias_folder)
    
    print(f"\nFound {len(correspondence['matches'])} matches")
    print("\nTop matches (by location, RCP, and model):")
    print("="*70)
    
    # Group matches by pickle file
    matches_by_pickle = {}
    for match in correspondence['matches']:
        pkl_file = match['pickle_file']
        if pkl_file not in matches_by_pickle:
            matches_by_pickle[pkl_file] = []
        matches_by_pickle[pkl_file].append(match)
    
    # Display matches
    for pkl_file, match_list in list(matches_by_pickle.items())[:20]:
        print(f"\nPickle: {pkl_file}")
        for match in match_list[:3]:  # Show top 3 matches per pickle
            print(f"  -> DRIAS: {match['drias_file']}")
            print(f"     Location: {match['location']}, RCP: {match['rcp_pickle']}/{match['rcp_drias']}, Score: {match['match_score']}")
    
    # Save to JSON file
    output_file = Path('pickle_drias_correspondence.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correspondence, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"Correspondence saved to: {output_file}")
    print(f"Total pickle files: {len(correspondence['pickle_files'])}")
    print(f"Total DRIAS files: {len(correspondence['drias_files'])}")
    print(f"Total matches: {len(correspondence['matches'])}")


if __name__ == '__main__':
    main()


