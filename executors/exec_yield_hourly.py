import numpy as np
import pandas as pd
import pvlib
from pvlib.location import Location
import streamlit as st

@st.cache_data(ttl=86400)
def generate_hourly_yield(tmy_subset, surface_tilt=15, surface_azimuth=180, viable_area_m2=1000):
    latitude = 55.024984
    longitude = -1.468343
    tz = 'Europe/London'
    location = Location(latitude, longitude, tz=tz)
    
    # try to use the canadian solar panels, otherwise just grab a random generic one
    cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')
    try:
        module_params = cec_modules['Canadian_Solar_Inc__CS3W_440MS']
    except KeyError:
        fallback_name = cec_modules.columns[100] 
        module_params = cec_modules[fallback_name]
        
    solar_position = location.get_solarposition(tmy_subset.index)
    
    # figure out where the sun is relative to where the panels are pointing (angle of incidence)
    aoi = pvlib.irradiance.aoi(
        surface_tilt, surface_azimuth,
        solar_position['apparent_zenith'], solar_position['azimuth']
    )
    
    # calculate how much direct and fuzzy sunlight actually hits the tilted plane of the array
    poa_irrad = pvlib.irradiance.get_total_irradiance(
        surface_tilt, surface_azimuth,
        solar_position['apparent_zenith'], solar_position['azimuth'],
        tmy_subset['dni'], tmy_subset['ghi'], tmy_subset['dhi']
    )
    
    # penalize for reflection - sunlight bouncing off the glass when it comes in at a sharp angle
    iam_penalty = pvlib.iam.martin_ruiz(aoi, a_r=0.16)
    
    effective_irradiance = poa_irrad['poa_direct'] * iam_penalty + \
                           poa_irrad['poa_sky_diffuse'] + \
                           poa_irrad['poa_ground_diffuse']
                           
    effective_irradiance = np.maximum(effective_irradiance, 0)
    
    # simulate how hot the actual silicon cells get, since hot panels are less efficient
    cell_temperature = pvlib.temperature.faiman(
        effective_irradiance, 
        tmy_subset['temp_air'], 
        tmy_subset['wind_speed']
    )
    
    # throw all that physics math into the main Desoto single-diode equations 
    IL, I0, Rs, Rsh, nNsVth = pvlib.pvsystem.calcparams_desoto(
        effective_irradiance, cell_temperature,
        module_params['alpha_sc'], module_params['a_ref'],
        module_params['I_L_ref'], module_params['I_o_ref'],
        module_params['R_sh_ref'], module_params['R_s'],
        module_params.get('EgRef', 1.121), module_params.get('dEgdT', -0.0002677),
        irrad_ref=1000, temp_ref=25
    )
    
    diode_outputs = pvlib.pvsystem.singlediode(
        photocurrent=IL, saturation_current=I0,
        resistance_series=Rs, resistance_shunt=Rsh,
        nNsVth=nNsVth, method='lambertw'
    )
    
    # figure out how many actual rectangular panels we can fit in that viable area we calculated
    module_area = module_params.get('A_c', 2.2) 
    num_modules = viable_area_m2 / module_area
    hourly_dc_watts = diode_outputs['p_mp'] * num_modules
    
    # flat panels get way dirtier than steep panels, so penalize them harder
    soiling_factor = 0.95 if surface_tilt < 15 else 0.98
    hourly_dc_watts_soiled = hourly_dc_watts * soiling_factor
    
    return (hourly_dc_watts_soiled.fillna(0) / 1000.0)

