import os
import time
import re
from pathlib import Path
from datetime import date, datetime
from batem.core.climate import ProspectiveClimateDRIAS, data_to_feature_names, HistoricalDatabase, ProspectiveClimateRefiner, MinMerger, AvgMerger, MaxMerger, SumMerger, Merger, stringdate_to_date, date_to_stringdate
from batem.core.weather import SWDbuilder

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    Nominatim = None


def load_drias_files_from_folder(folder_path: str, file_extensions: tuple[str] = ('.txt',), starting_stringdate: str = None, ending_stringdate: str = None):
    """
    Load all non-empty files from the specified folder.

    Args:
        folder_path: Path to the folder containing DRIAS files
        file_extensions: Tuple of file extensions to include (default: ('.txt',))
        starting_stringdate: Optional starting date string (e.g., '1/1/2006')
        ending_stringdate: Optional ending date string (e.g., '31/12/2100')

    Returns:
        List of ProspectiveClimateDRIAS objects, one for each loaded file
    """
    folder = Path(os.path.expanduser(folder_path))
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")

    loaded_climates = []

    # Get all files in the folder
    all_files = [f for f in folder.iterdir() if f.is_file()]

    # Filter for non-empty files with specified extensions
    relevant_files = [
        f for f in all_files
        if f.suffix.lower() in [ext.lower() for ext in file_extensions]
        and f.stat().st_size > 0
        and not f.name.startswith('.')  # Exclude hidden files like .DS_Store
    ]

    print(f"Found {len(relevant_files)} non-empty files in {folder_path}")

    # Load each file
    for file_path in relevant_files:
        try:
            print(f"\nLoading file: {file_path.name}")
            climate = load_drias_file_with_custom_path(
                str(file_path),
                data_to_feature_names,
                starting_stringdate,
                ending_stringdate
            )
            # Add location name from coordinates if available
            if climate.gps:
                latitude, longitude = climate.gps
                location_name = get_location_name_from_coordinates(latitude, longitude)
                climate.location_name = location_name
                if location_name:
                    print(f"  Location: {location_name}")
            loaded_climates.append(climate)
            print(f"Successfully loaded: {file_path.name}")
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")
            continue

    return loaded_climates


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
    geolocator = Nominatim(user_agent="batem_drias_reverse_geocoder")

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
        print(f"Error during reverse geocoding for ({latitude}, {longitude}): {e}")
        return None


def save_climate_to_excel(climate: ProspectiveClimateDRIAS, output_folder: str, city_name: str = None):
    """
    Save climate data to an Excel file with date and features.

    Args:
        climate: ProspectiveClimateDRIAS object containing the data
        output_folder: Folder where the Excel file will be saved
        city_name: City name for the filename (if None, uses location_name or model_name)
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for saving to Excel. Please install it with: pip install pandas")

    # Determine city name for filename
    if city_name is None:
        if hasattr(climate, 'location_name') and climate.location_name:
            city_name = climate.location_name
        else:
            city_name = climate.model_name

    # Clean city name for filename (remove special characters, spaces)
    city_name_clean = re.sub(r'[^\w\s-]', '', city_name).strip()
    city_name_clean = re.sub(r'[-\s]+', '_', city_name_clean)

    # Create filename
    filename = f"{city_name_clean}_2006-2100_daily.xlsx"
    output_path = Path(os.path.expanduser(output_folder)) / filename

    # Check if file already exists
    if output_path.exists():
        print(f"File already exists, skipping: {output_path}")
        return

    # Filter dates from 2006-01-01 to 2100-12-31
    start_date = date(2006, 1, 1)
    end_date = date(2100, 12, 31)

    # Extract data for the date range
    filtered_dates = sorted([d for d in climate.dates if start_date <= d <= end_date])

    if not filtered_dates:
        print(f"Warning: No data found in the date range 2006-01-01 to 2100-12-31 for {city_name}")
        return

    # Prepare data for DataFrame
    data_dict = {'Date': []}

    # Initialize feature columns
    for feature_name in climate.feature_names:
        data_dict[feature_name] = []

    # Fill data
    for d in filtered_dates:
        data_dict['Date'].append(datetime.combine(d, datetime.min.time()))
        feature_values = climate.date_name_features[d]
        for feature_name in climate.feature_names:
            # Get the feature value directly (it's a float, not a list)
            value = feature_values.get(feature_name)
            data_dict[feature_name].append(value)

    # Create DataFrame
    df = pd.DataFrame(data_dict)

    # Ensure Date is the first column
    columns = ['Date'] + [col for col in df.columns if col != 'Date']
    df = df[columns]

    # Create output folder if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to Excel (pandas will automatically format dates as Excel dates)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')

    print(f"Saved data to: {output_path}")
    print(f"  Date range: {filtered_dates[0]} to {filtered_dates[-1]}")
    print(f"  Number of days: {len(filtered_dates)}")
    print(f"  Features: {', '.join(climate.feature_names)}")


def save_hourly_climate_to_excel(climate: ProspectiveClimateDRIAS, output_folder: str, city_name: str = None, reference_period_start: str = '1/1/1980', reference_period_end: str = '31/12/2024', prospective_period_start: str = '1/1/2025', prospective_period_end: str = '31/12/2100'):
    """
    Generate and save hourly climate data combining historical (from 1980-01-01 until 2024-12-31) and prospective (2025-01-01 to 2100-12-31) data.

    Args:
        climate: ProspectiveClimateDRIAS object containing the prospective data
        output_folder: Folder where the Excel file will be saved
        city_name: City name for the filename (if None, uses location_name or model_name)
        reference_period_start: Start date for historical data (default: '1/1/1980')
        reference_period_end: End date for historical data (default: '31/12/2024')
        prospective_period_start: Start date for prospective data (default: '1/1/2025')
        prospective_period_end: End date for prospective data (default: '31/12/2100')
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for saving to Excel. Please install it with: pip install pandas")

    # Determine city name for filename
    if city_name is None:
        if hasattr(climate, 'location_name') and climate.location_name:
            city_name = climate.location_name
        else:
            city_name = climate.model_name

    # Clean city name for filename (remove special characters, spaces)
    city_name_clean = re.sub(r'[^\w\s-]', '', city_name).strip()
    city_name_clean = re.sub(r'[-\s]+', '_', city_name_clean)

    # Create filenames for historical and prospective data
    historical_filename = f"{city_name_clean}_hourly_1980-2024.xlsx"
    prospective_filename = f"{city_name_clean}_hourly_2025-2100.xlsx"
    historical_output_path = Path(os.path.expanduser(output_folder)) / historical_filename
    prospective_output_path = Path(os.path.expanduser(output_folder)) / prospective_filename

    # Check if files already exist
    if historical_output_path.exists() and prospective_output_path.exists():
        print("Files already exist, skipping:")
        print(f"  - {historical_output_path}")
        print(f"  - {prospective_output_path}")
        return

    # Get GPS coordinates
    if not climate.gps:
        raise ValueError(f"No GPS coordinates available for {city_name}")
    latitude, longitude = climate.gps

    print(f"Generating hourly data for {city_name}...")

    # Define feature merger weights (same as in try_climate_hourly.py)
    feature_merger_weights: dict[Merger, float] = {
        MinMerger('temperature'): 1,
        MaxMerger('temperature'): 1,
        AvgMerger('temperature'): 1,
        SumMerger('precipitation_mass'): 1,
        AvgMerger('absolute_humidity'): 1,
        AvgMerger('OM_ghi'): 1,
        AvgMerger('wind_speed_m_s'): 1,
        SumMerger('snowfall_mass'): 1
    }

    # Filter the existing climate object to get only the prospective period
    prospective_period_start_date = stringdate_to_date(prospective_period_start)
    prospective_period_end_date = stringdate_to_date(prospective_period_end)

    # Filter dates for the prospective period
    filtered_dates = sorted([d for d in climate.dates if prospective_period_start_date <= d <= prospective_period_end_date])

    if not filtered_dates:
        raise ValueError(f"No data found in the prospective period {prospective_period_start} to {prospective_period_end}")

    # Create a filtered climate object by copying and filtering
    # Since we can't easily subclass, we'll create a simple object with the needed attributes
    class FilteredProspectiveClimate:
        def __init__(self, original_climate, start_date, end_date):
            self.model_name = original_climate.model_name
            self.gps = original_climate.gps
            self.feature_names = original_climate.feature_names
            self.feature_units = original_climate.feature_units
            self.feature_descriptions = original_climate.feature_descriptions
            self.starting_date = start_date
            self.ending_date = end_date
            self.data_to_feature_names = original_climate.data_to_feature_names
            # Filter date_name_features
            self.date_name_features = {
                d: original_climate.date_name_features[d]
                for d in filtered_dates
            }
            self.dates = tuple(filtered_dates)

        @property
        def starting_stringdate(self):
            return date_to_stringdate(self.starting_date)

        @property
        def ending_stringdate(self):
            return date_to_stringdate(self.ending_date)

        def __call__(self, a_date, feature_name=None):
            if feature_name is not None:
                return self.date_name_features[a_date][feature_name]
            else:
                return self.date_name_features[a_date]

    prospective_climate = FilteredProspectiveClimate(climate, filtered_dates[0], filtered_dates[-1])

    # Load historical weather data
    print(f"Loading historical weather data from {reference_period_start} to {reference_period_end}...")
    # Extract end year from date string to set end_year for SWDbuilder
    reference_end_year = int(reference_period_end.split('/')[-1])
    # Use 1980 as initial_year to download from 1980, and ensure end_year covers the requested period (including 2024)
    swd_builder = SWDbuilder(location=city_name, latitude_north_deg=latitude, longitude_east_deg=longitude, initial_year=1980, end_year=reference_end_year)

    # Check what data is actually available and adjust dates if necessary
    from batem.core.timemg import epochtimems_to_stringdate, REGULAR_DATE_FORMAT, local_timezone
    available_start_date_str = epochtimems_to_stringdate(swd_builder.first_epochtimems, date_format=REGULAR_DATE_FORMAT, timezone_str=local_timezone())
    available_end_date_str = epochtimems_to_stringdate(swd_builder.last_epochtimems, date_format=REGULAR_DATE_FORMAT, timezone_str=local_timezone())

    # Parse the dates to compare them as date objects
    requested_start_date_obj = stringdate_to_date(reference_period_start)
    requested_end_date_obj = stringdate_to_date(reference_period_end)
    available_start_date_obj = stringdate_to_date(available_start_date_str)
    available_end_date_obj = stringdate_to_date(available_end_date_str)

    # Use the later of the requested start date or available start date
    if available_start_date_obj > requested_start_date_obj:
        print(f"Warning: Requested start date {reference_period_start} is before available data. Using available start date: {available_start_date_str}")
        actual_reference_period_start = available_start_date_str
    else:
        actual_reference_period_start = reference_period_start

    # Use the earlier of the requested end date or available end date
    if available_end_date_obj < requested_end_date_obj:
        print(f"Warning: Requested end date {reference_period_end} is beyond available data. Using available end date: {available_end_date_str}")
        actual_reference_period_end = available_end_date_str
    else:
        actual_reference_period_end = reference_period_end

    historical_weather_data = swd_builder(from_stringdate=actual_reference_period_start, to_stringdate=actual_reference_period_end)

    # Filter feature_merger_weights to only include variables that exist in the historical weather data
    available_variable_names = set(historical_weather_data.variable_names)
    filtered_feature_merger_weights = {
        merger: weight
        for merger, weight in feature_merger_weights.items()
        if merger.variable_name in available_variable_names
    }

    # Check if we have any valid mergers
    if not filtered_feature_merger_weights:
        raise ValueError(f"No matching variables found between feature_merger_weights and available historical weather data variables: {available_variable_names}")

    # Warn about missing variables
    missing_variables = {
        merger.variable_name
        for merger in feature_merger_weights.keys()
        if merger.variable_name not in available_variable_names
    }
    if missing_variables:
        print(f"Warning: The following variables are not available in historical weather data and will be skipped: {missing_variables}")

    # Create historical database
    historical_database = HistoricalDatabase(historical_weather_data, filtered_feature_merger_weights)

    # Create ProspectiveClimateRefiner to generate hourly prospective data
    print(f"Generating hourly prospective data from {prospective_period_start} to {prospective_period_end}...")
    pcr = ProspectiveClimateRefiner(prospective_climate=prospective_climate, historical_database=historical_database)
    prospective_hourly_data = pcr.make_prospective_site_weather_data(city_name)

    # Concatenate historical and prospective data
    print("Concatenating historical and prospective data...")

    # Get all datetimes and variable values
    all_datetimes = historical_weather_data.datetimes + prospective_hourly_data.datetimes

    # Get all variable names (union of both)
    all_variable_names = list(set(historical_weather_data.variable_names) | set(prospective_hourly_data.variable_names))
    # Remove metadata variables
    all_variable_names = [v for v in all_variable_names if v not in ('datetime', 'epochtimems', 'stringdate')]

    # Prepare data dictionary
    data_dict = {'DateTime': all_datetimes}

    # Fill data for each variable
    for var_name in all_variable_names:
        historical_values = historical_weather_data.get(var_name) if var_name in historical_weather_data.variable_names else [None] * len(historical_weather_data.datetimes)
        prospective_values = prospective_hourly_data.get(var_name) if var_name in prospective_hourly_data.variable_names else [None] * len(prospective_hourly_data.datetimes)
        data_dict[var_name] = list(historical_values) + list(prospective_values)

    # Create DataFrame
    df = pd.DataFrame(data_dict)

    # Filter to ensure we only include data up to 2100-12-31 23:00:00
    # Get timezone from historical_weather_data to make cutoff_datetime timezone-aware
    import pytz
    naive_cutoff = datetime(2100, 12, 31, 23, 0, 0)

    # Get timezone string from historical_weather_data (which is the source of truth)
    timezone_str = getattr(historical_weather_data, 'timezone_str', None)
    if not timezone_str and hasattr(prospective_hourly_data, 'timezone_str'):
        timezone_str = prospective_hourly_data.timezone_str

    if timezone_str:
        cutoff_timezone = pytz.timezone(timezone_str)
        cutoff_datetime = cutoff_timezone.localize(naive_cutoff)
    elif all_datetimes and len(all_datetimes) > 0:
        # Fallback: extract timezone from the first datetime's tzinfo
        first_dt = all_datetimes[0]
        if hasattr(first_dt, 'tzinfo') and first_dt.tzinfo is not None:
            # Get timezone name from tzinfo (for pytz timezones, use .zone attribute)
            if hasattr(first_dt.tzinfo, 'zone'):
                timezone_str = first_dt.tzinfo.zone
                cutoff_timezone = pytz.timezone(timezone_str)
                cutoff_datetime = cutoff_timezone.localize(naive_cutoff)
            else:
                # If tzinfo doesn't have zone attribute, try to use it directly (not recommended but fallback)
                # This shouldn't happen with pytz timezones
                cutoff_datetime = naive_cutoff
        else:
            # Datetimes are naive, use naive cutoff
            cutoff_datetime = naive_cutoff
    else:
        # No timezone info available, use naive datetime
        cutoff_datetime = naive_cutoff

    df = df[df['DateTime'] <= cutoff_datetime]

    # Remove timezone information from DateTime column for Excel compatibility
    # Excel does not support timezone-aware datetimes
    if pd.api.types.is_datetime64_any_dtype(df['DateTime']):
        # If it's a datetime64 type, check if it's timezone-aware
        if df['DateTime'].dt.tz is not None:
            # Convert to naive datetime (remove timezone info)
            # For timezone-aware datetime Series, convert to UTC then remove timezone
            df['DateTime'] = df['DateTime'].dt.tz_convert('UTC').dt.tz_localize(None)
    else:
        # If it's object dtype with datetime objects, convert each one
        # For Python datetime objects, use replace(tzinfo=None)
        df['DateTime'] = df['DateTime'].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo is not None else x)

    # Ensure DateTime is the first column
    columns = ['DateTime'] + [col for col in df.columns if col != 'DateTime']
    df = df[columns]

    # Create output folder if it doesn't exist
    historical_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Split DataFrame into historical (1980-2024) and prospective (2025-2100) portions
    cutoff_date = datetime(2024, 12, 31, 23, 59, 59)  # End of 2024
    
    # Split data - datetimes should already be naive at this point
    df_historical = df[df['DateTime'] <= cutoff_date].copy()
    df_prospective = df[df['DateTime'] > cutoff_date].copy()
    
    print("Splitting data into historical (1980-2024) and prospective (2025-2100) files...")
    print(f"  Historical data: {len(df_historical)} rows ({df_historical['DateTime'].min()} to {df_historical['DateTime'].max()})")
    print(f"  Prospective data: {len(df_prospective)} rows ({df_prospective['DateTime'].min()} to {df_prospective['DateTime'].max()})")

    # Save historical data file
    if not historical_output_path.exists():
        save_dataframe_to_excel(df_historical, historical_output_path, all_variable_names, "historical")
    else:
        print(f"Historical file already exists, skipping: {historical_output_path}")
    
    # Save prospective data file
    if not prospective_output_path.exists():
        save_dataframe_to_excel(df_prospective, prospective_output_path, all_variable_names, "prospective")
    else:
        print(f"Prospective file already exists, skipping: {prospective_output_path}")


def save_dataframe_to_excel(df: pd.DataFrame, output_path: Path, variable_names: list[str], data_type: str):
    """
    Save a DataFrame to Excel, handling Excel's row limit by splitting into multiple sheets if needed.
    
    Args:
        df: DataFrame to save
        output_path: Path where the Excel file will be saved
        variable_names: List of variable names for logging
        data_type: Type of data ('historical' or 'prospective') for logging
    """
    MAX_EXCEL_ROWS = 1048576
    total_rows = len(df)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        if total_rows <= MAX_EXCEL_ROWS:
            # Data fits in one sheet
            df.to_excel(writer, index=False, sheet_name='Data')
            print(f"Saved {data_type} hourly data to: {output_path}")
            print(f"  Date range: {df['DateTime'].min()} to {df['DateTime'].max()}")
            print(f"  Number of hours: {len(df)}")
            print(f"  Variables: {', '.join(variable_names)}")
        else:
            # Split data into multiple sheets
            num_sheets = (total_rows // MAX_EXCEL_ROWS) + 1
            print(f"{data_type.capitalize()} data exceeds Excel row limit ({total_rows} > {MAX_EXCEL_ROWS}). Splitting into {num_sheets} sheets...")
            
            for sheet_num in range(num_sheets):
                start_idx = sheet_num * MAX_EXCEL_ROWS
                end_idx = min((sheet_num + 1) * MAX_EXCEL_ROWS, total_rows)
                df_sheet = df.iloc[start_idx:end_idx].copy()
                
                # Create sheet name with date range
                start_date = df_sheet['DateTime'].min()
                end_date = df_sheet['DateTime'].max()
                sheet_name = f"Data_{start_date.year}-{end_date.year}"
                if len(sheet_name) > 31:  # Excel sheet name limit is 31 characters
                    sheet_name = f"Sheet{sheet_num + 1}"
                
                df_sheet.to_excel(writer, index=False, sheet_name=sheet_name)
                print(f"  Sheet {sheet_num + 1}/{num_sheets}: {sheet_name} ({len(df_sheet)} rows, {start_date} to {end_date})")
            
            print(f"Saved {data_type} hourly data to: {output_path}")
            print(f"  Total date range: {df['DateTime'].min()} to {df['DateTime'].max()}")
            print(f"  Total number of hours: {len(df)}")
            print(f"  Number of sheets: {num_sheets}")
            print(f"  Variables: {', '.join(variable_names)}")


def load_drias_file_with_custom_path(file_path: str, data_to_feature_names: dict[str, str], starting_stringdate: str = None, ending_stringdate: str = None):
    """
    Load a DRIAS file from a custom path by temporarily patching the data folder path.
    This is a workaround since ProspectiveClimateDRIAS expects files in the data folder.
    """
    import batem.core.climate as climate_module

    # Store original path
    original_data_folder = climate_module._DATA_FOLDER_PATH
    full_path = Path(file_path)

    # Temporarily set the data folder to the file's parent directory
    # and use just the filename
    climate_module._DATA_FOLDER_PATH = full_path.parent
    filename = full_path.name

    try:
        # Now create the ProspectiveClimateDRIAS instance with the patched path
        climate = ProspectiveClimateDRIAS(
            filename=filename,
            data_to_feature_names=data_to_feature_names,
            starting_stringdate=starting_stringdate,
            ending_stringdate=ending_stringdate
        )
        return climate
    finally:
        # Restore original path
        climate_module._DATA_FOLDER_PATH = original_data_folder


def process_location(file_path: Path, output_folder: str, data_to_feature_names: dict[str, str]):
    """
    Process a single location: load DRIAS data, generate daily Excel file,
    then generate hourly Excel file with historical and prospective data.

    Args:
        file_path: Path to the DRIAS file for this location
        output_folder: Folder where Excel files will be saved
        data_to_feature_names: Mapping dictionary for feature names

    Returns:
        tuple: (success: bool, location_name: str, error_message: str or None)
    """
    try:
        # Load DRIAS data for this location
        print(f"\n{'='*60}")
        print(f"Processing location: {file_path.name}")
        print(f"{'='*60}")
        
        climate = load_drias_file_with_custom_path(
            str(file_path),
            data_to_feature_names,
            starting_stringdate=None,
            ending_stringdate=None
        )
        
        # Get location name from coordinates if available
        city_name = None
        if climate.gps:
            latitude, longitude = climate.gps
            location_name = get_location_name_from_coordinates(latitude, longitude)
            if location_name:
                climate.location_name = location_name
                city_name = location_name
                print(f"Location: {city_name}")
        
        if not city_name:
            city_name = climate.model_name
        
        # Step 1: Generate daily Excel file
        print(f"\nStep 1: Generating daily Excel file for {city_name}...")
        save_climate_to_excel(climate, output_folder, city_name)
        print("Daily file generated successfully")
        
        # Step 2: Generate hourly Excel file with historical and prospective data
        print(f"\nStep 2: Generating hourly Excel file for {city_name}...")
        save_hourly_climate_to_excel(climate, output_folder, city_name)
        print("Hourly file generated successfully")
        
        print(f"\n{'='*60}")
        print(f"Successfully processed {city_name}")
        print(f"{'='*60}\n")
        
        return True, city_name, None
        
    except Exception as e:
        city_name = getattr(climate, 'location_name', file_path.stem) if 'climate' in locals() else file_path.stem
        error_msg = str(e)
        print(f"\n{'!'*60}")
        print(f"ERROR processing {city_name}: {error_msg}")
        print(f"{'!'*60}")
        import traceback
        traceback.print_exc()
        return False, city_name, error_msg


def main():
    folder_path = "~/Documents/recherche/chercheurs/khaled/work/70cities/Drias_1point_10parameters_2006_2100"
    output_folder = "."  # Save Excel files in current directory, change as needed

    folder = Path(os.path.expanduser(folder_path))
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")

    # Get all non-empty .txt files from the folder
    all_files = [f for f in folder.iterdir() if f.is_file()]
    relevant_files = [
        f for f in all_files
        if f.suffix.lower() == '.txt'
        and f.stat().st_size > 0
        and not f.name.startswith('.')  # Exclude hidden files
    ]

    print(f"Found {len(relevant_files)} non-empty DRIAS files to process")
    print(f"Output folder: {os.path.abspath(output_folder)}")

    # Process each location sequentially
    success_count = 0
    failed_locations = []
    
    for idx, file_path in enumerate(relevant_files, 1):
        print(f"\n{'#'*60}")
        print(f"Processing file {idx}/{len(relevant_files)}: {file_path.name}")
        print(f"{'#'*60}")
        
        success, location_name, error_msg = process_location(file_path, output_folder, data_to_feature_names)
        
        if success:
            success_count += 1
        else:
            failed_locations.append((location_name, error_msg))
            print(f"\n{'!'*60}")
            print(f"Stopping processing due to error with {location_name}")
            print(f"Error: {error_msg}")
            print(f"{'!'*60}")
            break  # Stop processing on first error
    
    # Summary
    print(f"\n{'='*60}")
    print("Processing Summary:")
    print(f"  - Successfully processed: {success_count} locations")
    if failed_locations:
        print(f"  - Failed: {len(failed_locations)} location(s)")
        for loc_name, err_msg in failed_locations:
            print(f"    * {loc_name}: {err_msg}")
    print(f"  - Total files found: {len(relevant_files)}")
    print(f"{'='*60}")
    
    if success_count == 0 and failed_locations:
        print("\nNo files were generated. Processing stopped due to errors.")
    
    return success_count, failed_locations


if __name__ == '__main__':
    main()
