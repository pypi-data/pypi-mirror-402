# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from batem.core.weather import SWDbuilder
from batem.core.climate import ProspectiveClimateDRIAS, HistoricalDatabase, MinMerger, AvgMerger, MaxMerger, SumMerger, Merger, ProspectiveClimateRefiner, data_to_feature_names
from batem.core.weather import SiteWeatherData
from batem.core.solar import SolarModel


################################################################

location = 'prapoutel'
latitude_north_deg = 45.2571092981119
longitude_east_deg = 5.9952649331806755
historical_year = 2024
prospective_year = 2100
drias_filename = 'prapoutel_ALADIN63_rcp8.5.txt'

prospective_period: tuple[str, str] = ('1/1/2027', '31/12/2050')
reference_period: tuple[str, str] = ('1/1/2006', '31/12/2024')

# location = 'Grenoble'
# latitude_north_deg = 45.19154994547585
# longitude_east_deg = 5.722065312331381
# historical_year = 2023
# prospective_year = 2100
# drias_filename = 'Grenoble_ALADIN63_rcp8.5.txt'

# prospective_period: tuple[str, str] = ('1/1/2050', '31/12/2050')
# reference_period: tuple[str, str] = ('1/1/2006', '31/12/2023')

feature_merger_weights: dict[Merger, float] = {
    MinMerger('temperature'): 1,
    MaxMerger('temperature'): 1,
    AvgMerger('temperature'): 1,
    SumMerger('precipitation_mass'): 1,
    AvgMerger('absolute_humidity'): 1,
    AvgMerger('OM_ghi'): 1,
    AvgMerger('wind_speed_m_per_s'): 1,
    SumMerger('snowfall_mass'): 1
    }
################################################################

prospective_climate = ProspectiveClimateDRIAS(
    filename=drias_filename,
    data_to_feature_names=data_to_feature_names,
    starting_stringdate=prospective_period[0],
    ending_stringdate=prospective_period[1],
)
print('Climate prospective:', prospective_climate)

prospective_climate = ProspectiveClimateDRIAS(
    filename=drias_filename,
    data_to_feature_names=data_to_feature_names,
    starting_stringdate=prospective_period[0],
    ending_stringdate=prospective_period[1],
)

weather_builder = SWDbuilder(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg)
historical_site_weather_data = weather_builder(from_stringdate=reference_period[0], to_stringdate=reference_period[1])
historical_database = HistoricalDatabase(historical_site_weather_data, feature_merger_weights)
pcr = ProspectiveClimateRefiner(prospective_climate=prospective_climate, historical_database=historical_database)
prospective_site_weather_data: SiteWeatherData = pcr.make_prospective_site_weather_data(location)

solar_model = SolarModel(prospective_site_weather_data)
print(f'Exporting solar model to {location}_{prospective_year}.try')
solar_model.try_export()
