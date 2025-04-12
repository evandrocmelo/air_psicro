import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time
from psychrometrics import (
    calculate_atmospheric_pressure, 
    calculate_properties_tbs_tbm, 
    calculate_properties_tbs_ur, 
    calculate_properties_tbs_tpo
)
from utils import display_results, input_with_units
from psychrometric_chart import plot_psychrometric_chart
from geo_location import get_location_info
from user_preferences import init_preferences, render_preferences_ui, get_current_profile_name

# Set page config
st.set_page_config(
    page_title="Humid Air Calculator",
    page_icon="💧",
    layout="wide"
)

# Initialize user preferences
init_preferences()

# Application title and description
st.title("Humid Air Thermodynamic Calculator")

# Show current profile if one is active
current_profile = get_current_profile_name()
if current_profile:
    st.success(f"Perfil ativo / Active profile: **{current_profile}**")

st.markdown("""
**English**: This application calculates thermodynamic properties of humid air based on different input methods.  
**Português**: Esta aplicação calcula as propriedades termodinâmicas do ar úmido com base em diferentes métodos de entrada.
""")

# Main content - Location and altitude input
st.header("Altitude & Pressão Atmosférica / Altitude & Atmospheric Pressure")

# Initialize session states
if 'altitude' not in st.session_state:
    st.session_state.altitude = 0.0  # Default altitude (sea level)
if 'know_altitude' not in st.session_state:
    st.session_state.know_altitude = None
if 'p_atm' not in st.session_state:
    st.session_state.p_atm = 101.325  # Default atmospheric pressure (kPa at sea level)
if 'manual_location_data' not in st.session_state:
    st.session_state.manual_location_data = {
        'city': 'Viçosa',
        'region': 'Minas Gerais',
        'country': 'Brazil',
        'latitude': -20.7546,
        'longitude': -42.8825,
        'elevation': 648.0  # Approximate elevation for Viçosa in meters
    }

# First question: Do you know the local altitude?
know_altitude = st.radio(
    "Você sabe a altitude local? / Do you know the local altitude?",
    options=["Sim / Yes", "Não / No"],
    index=0 if st.session_state.know_altitude else 1
)

# Update session state
st.session_state.know_altitude = (know_altitude == "Sim / Yes")

if st.session_state.know_altitude:
    # If the user knows the altitude, show direct input
    altitude = st.number_input(
        "Altitude (m)", 
        min_value=0.0, 
        max_value=5000.0, 
        value=st.session_state.altitude, 
        step=10.0,
        help="Enter altitude in meters to calculate atmospheric pressure / Insira a altitude em metros para calcular a pressão atmosférica",
        key="altitude_input_direct"
    )
    # Update session state
    st.session_state.altitude = altitude
    
    # Calculate atmospheric pressure using the altitude value
    p_atm = calculate_atmospheric_pressure(altitude)
    st.session_state.p_atm = p_atm
    
else:
    # If the user doesn't know the altitude, show location input
    st.subheader("Inserir Localização Manualmente / Enter Location Manually")
    st.info("Insira sua localização para estimar a altitude / Enter your location to estimate altitude")
    
    # City, Region, Country in a single row
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.text_input("Cidade / City", 
                            value=st.session_state.manual_location_data.get('city', 'Viçosa'),
                            key="city_input")
    with col2:
        region = st.text_input("Estado / State",
                             value=st.session_state.manual_location_data.get('region', 'Minas Gerais'),
                             key="region_input")
    with col3:
        country = st.text_input("País / Country",
                              value=st.session_state.manual_location_data.get('country', 'Brazil'),
                              key="country_input")
    
    # Latitude, Longitude in a single row
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude",
                                value=st.session_state.manual_location_data.get('latitude', -20.7546),
                                format="%.6f",
                                key="latitude_input")
    with col2:
        longitude = st.number_input("Longitude",
                                 value=st.session_state.manual_location_data.get('longitude', -42.8825),
                                 format="%.6f",
                                 key="longitude_input")
    
    # Custom elevation input
    elevation = st.number_input("Altitude (m) / Elevation (m)",
                              value=st.session_state.manual_location_data.get('elevation', 648.0),
                              min_value=0.0,
                              max_value=5000.0,
                              step=1.0,
                              key="elevation_input")
    
    # Update button
    if st.button("Usar esta localização / Use this location"):
        # Update the manual location data
        st.session_state.manual_location_data = {
            'city': city,
            'region': region,
            'country': country,
            'latitude': latitude,
            'longitude': longitude,
            'elevation': elevation
        }
        
        # Set altitude directly from manual entry
        st.session_state.altitude = elevation
        
        # Calculate atmospheric pressure
        p_atm = calculate_atmospheric_pressure(elevation)
        st.session_state.p_atm = p_atm
        
        st.success(f"Localização atualizada: {city}, {region}, {country} / Location updated")
        st.rerun()
    
    # Show the current manual location on a map
    try:
        map_data = {
            'latitude': [st.session_state.manual_location_data['latitude']],
            'longitude': [st.session_state.manual_location_data['longitude']]
        }
        st.map(map_data, zoom=10)
    except Exception as e:
        st.warning(f"Não foi possível exibir o mapa: {str(e)} / Could not display map")
    
    # Use the elevation from manual location data
    altitude = st.session_state.manual_location_data['elevation']
    st.session_state.altitude = altitude
    
    # Calculate atmospheric pressure
    p_atm = calculate_atmospheric_pressure(altitude)
    st.session_state.p_atm = p_atm

# Display the atmospheric pressure and its change from standard pressure
p_std = 101.325  # Standard pressure in kPa
pressure_diff = p_atm - p_std
pressure_diff_percent = (pressure_diff / p_std) * 100

# Display with change indicators
st.write(f"Atmospheric Pressure / Pressão Atmosférica: **{p_atm:.2f} kPa**")
if abs(pressure_diff) > 0.01:  # Only show difference if it's significant
    change_color = "red" if pressure_diff < 0 else "green"
    change_arrow = "↓" if pressure_diff < 0 else "↑"
    st.write(f"<span style='color:{change_color};'>({change_arrow} {abs(pressure_diff):.2f} kPa ou {abs(pressure_diff_percent):.1f}% em relação ao nível do mar)</span>", unsafe_allow_html=True)
    
# Show a small example of how altitude affects pressure
with st.expander("Altitude & Pressure Relation / Relação Altitude & Pressão"):
    st.markdown("""
    | Altitude (m) | Pressão Aprox. (kPa) |
    |-------------|-------------------|
    | 0 (nível do mar) | 101.33 |
    | 500 | 95.46 |
    | 1000 | 89.88 |
    | 2000 | 79.50 |
    | 3000 | 70.12 |
    | 4000 | 61.66 |
    | 5000 | 54.05 |
    """)
    st.markdown("A pressão atmosférica diminui com o aumento da altitude. / Atmospheric pressure decreases as altitude increases.")

# Input methods section
st.header("Input Method / Método de Entrada")

# Create tabs for different input methods
tab1, tab2, tab3 = st.tabs([
    "Dry-bulb & Wet-bulb / Bulbo Seco & Bulbo Molhado", 
    "Dry-bulb & Relative Humidity / Bulbo Seco & Umidade Relativa", 
    "Dry-bulb & Dew Point / Bulbo Seco & Ponto de Orvalho"
])

# Tab 1: Dry-bulb and Wet-bulb temperatures
with tab1:
    st.subheader("Dry-bulb and Wet-bulb Temperatures / Temperaturas de Bulbo Seco e Bulbo Molhado")
    
    col1, col2 = st.columns(2)
    with col1:
        tbs1 = input_with_units("Dry-bulb Temperature / Temperatura de Bulbo Seco", "°C", 
                               min_value=-20.0, max_value=60.0, value=25.0, step=0.1, key="tbs1")
    with col2:
        tbm = input_with_units("Wet-bulb Temperature / Temperatura de Bulbo Molhado", "°C", 
                              min_value=-20.0, max_value=60.0, value=18.0, step=0.1, key="tbm")
    
    # Check valid input range
    if tbm > tbs1:
        st.error("Wet-bulb temperature cannot be higher than dry-bulb temperature / A temperatura de bulbo molhado não pode ser maior que a temperatura de bulbo seco")
    else:
        if st.button("Calculate / Calcular", key="calc_tbm"):
            try:
                properties = calculate_properties_tbs_tbm(tbs1, tbm, p_atm)
                display_results(properties)
            except Exception as e:
                st.error(f"Calculation error: {str(e)}")

# Tab 2: Dry-bulb and Relative Humidity
with tab2:
    st.subheader("Dry-bulb Temperature and Relative Humidity / Temperatura de Bulbo Seco e Umidade Relativa")
    
    col1, col2 = st.columns(2)
    with col1:
        tbs2 = input_with_units("Dry-bulb Temperature / Temperatura de Bulbo Seco", "°C", 
                               min_value=-20.0, max_value=60.0, value=25.0, step=0.1, key="tbs2")
    with col2:
        ur = input_with_units("Relative Humidity / Umidade Relativa", "%", 
                             min_value=0.0, max_value=100.0, value=50.0, step=1.0, key="ur")
    
    if st.button("Calculate / Calcular", key="calc_ur"):
        try:
            properties = calculate_properties_tbs_ur(tbs2, ur, p_atm)
            display_results(properties)
        except Exception as e:
            st.error(f"Calculation error: {str(e)}")

# Tab 3: Dry-bulb and Dew Point temperatures
with tab3:
    st.subheader("Dry-bulb and Dew Point Temperatures / Temperaturas de Bulbo Seco e Ponto de Orvalho")
    
    col1, col2 = st.columns(2)
    with col1:
        tbs3 = input_with_units("Dry-bulb Temperature / Temperatura de Bulbo Seco", "°C", 
                               min_value=-20.0, max_value=60.0, value=25.0, step=0.1, key="tbs3")
    with col2:
        tpo = input_with_units("Dew Point Temperature / Temperatura de Ponto de Orvalho", "°C", 
                              min_value=-20.0, max_value=60.0, value=15.0, step=0.1, key="tpo")
    
    # Check valid input range
    if tpo > tbs3:
        st.error("Dew point temperature cannot be higher than dry-bulb temperature / A temperatura de ponto de orvalho não pode ser maior que a temperatura de bulbo seco")
    else:
        if st.button("Calculate / Calcular", key="calc_tpo"):
            try:
                properties = calculate_properties_tbs_tpo(tbs3, tpo, p_atm)
                display_results(properties)
            except Exception as e:
                st.error(f"Calculation error: {str(e)}")

# User preferences section
st.markdown("---")
st.header("🔧 Preferências do Usuário / User Preferences")

# Show the user preferences UI in an expander for cleaner interface
with st.expander("Abrir Gerenciador de Perfis / Open Profile Manager"):
    render_preferences_ui()

# Footer with information
st.markdown("---")
st.markdown("""
### References / Referências:
- ASHRAE Handbook - Fundamentals
- Engineering Thermodynamics - Moran & Shapiro
- Psychrometric Analysis - Stoecker & Jones

### About:
This calculator uses standard psychrometric equations to determine the thermodynamic properties of humid air.  
Este calculador utiliza equações psicrométricas padrão para determinar as propriedades termodinâmicas do ar úmido.
""")
