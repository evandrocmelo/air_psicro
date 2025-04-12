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

# Set page config
st.set_page_config(
    page_title="Humid Air Calculator",
    page_icon="💧",
    layout="wide"
)

# Application title and description
st.title("Humid Air Thermodynamic Calculator")
st.markdown("""
**English**: This application calculates thermodynamic properties of humid air based on different input methods.  
**Português**: Esta aplicação calcula as propriedades termodinâmicas do ar úmido com base em diferentes métodos de entrada.
""")

# Main content - Location and altitude input
st.header("Location / Localização")

# Initialize session state for location data
if 'location_info' not in st.session_state:
    st.session_state.location_info = None
if 'altitude' not in st.session_state:
    st.session_state.altitude = 0.0
if 'using_geolocation' not in st.session_state:
    st.session_state.using_geolocation = False
if 'manual_location' not in st.session_state:
    st.session_state.manual_location = False
if 'p_atm' not in st.session_state:
    st.session_state.p_atm = 101.325  # Default atmospheric pressure (kPa at sea level)

# Geolocation option
use_geolocation = st.checkbox(
    "Use geolocation for automatic pressure calculation / Usar geolocalização para cálculo automático de pressão",
    value=st.session_state.using_geolocation
)

# Update the using_geolocation flag in session_state
if use_geolocation != st.session_state.using_geolocation:
    st.session_state.using_geolocation = use_geolocation
    if use_geolocation and st.session_state.location_info is None:
        # Only fetch location if the checkbox is checked and we don't have location info yet
        with st.spinner("Obtaining location data... / Obtendo dados de localização..."):
            st.session_state.location_info = get_location_info()

# Add option for manual location input when geolocation is enabled
if use_geolocation:
    # Add tabs for auto vs manual location
    geo_tab1, geo_tab2 = st.tabs(["Automatic Detection / Detecção Automática", "Manual Location / Localização Manual"])
    
    with geo_tab1:
        # Add a refresh button for location data
        if st.button("Refresh Location Data / Atualizar Dados de Localização"):
            with st.spinner("Refreshing location data... / Atualizando dados de localização..."):
                st.session_state.location_info = get_location_info()
                st.session_state.manual_location = False
                st.rerun()
        
        # Display automatic location info if available
        if st.session_state.location_info and not st.session_state.get('manual_location', False):
            location = st.session_state.location_info
            
            # Display location information
            st.success(f"Location detected / Localização detectada: {location.get('city', 'Unknown')}, {location.get('region', '')}, {location.get('country', '')}")
            
            # Display a map with the detected location if we have coordinates
            if 'latitude' in location and 'longitude' in location:
                try:
                    # Create a single-element map with the detected location
                    map_data = {
                        'latitude': [float(location['latitude'])],
                        'longitude': [float(location['longitude'])]
                    }
                    st.map(map_data, zoom=10)
                except Exception as e:
                    st.warning(f"Could not display location map: {str(e)}")
            
            # If we have elevation data, use it for altitude
            if 'elevation' in location:
                altitude = location['elevation']
                st.info(f"Estimated elevation / Altitude estimada: {altitude:.1f} meters")
                st.session_state.altitude = altitude
                
                # If we have atmospheric pressure directly, use it
                if 'atmospheric_pressure' in location:
                    p_atm = location['atmospheric_pressure']
                    st.session_state.p_atm = p_atm
                else:
                    # Calculate atmospheric pressure from elevation
                    p_atm = calculate_atmospheric_pressure(altitude)
                    st.session_state.p_atm = p_atm
            else:
                # If no elevation data, show warning
                st.warning("Elevation data not available. / Dados de elevação não disponíveis.")
                st.info("Try using manual location input instead. / Tente usar a entrada manual de localização.")
        else:
            # If geolocation failed, show message
            st.error("Could not automatically detect location. Please try manual input. / Não foi possível detectar a localização automaticamente. Por favor, tente a entrada manual.")
    
    with geo_tab2:
        # Manual location input
        st.subheader("Enter Location Manually / Inserir Localização Manualmente")
        
        # Initialize session state for manual location if not already present
        if 'manual_location_data' not in st.session_state:
            st.session_state.manual_location_data = {
                'city': 'Viçosa',
                'region': 'Minas Gerais',
                'country': 'Brazil',
                'latitude': -20.7546,
                'longitude': -42.8825,
                'elevation': 648.0  # Approximate elevation for Viçosa in meters
            }
        
        # City, Region, Country in a single row
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input("City / Cidade", 
                                value=st.session_state.manual_location_data.get('city', 'Viçosa'),
                                key="city_input")
        with col2:
            region = st.text_input("State / Estado",
                                 value=st.session_state.manual_location_data.get('region', 'Minas Gerais'),
                                 key="region_input")
        with col3:
            country = st.text_input("Country / País",
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
        
        # Elevation (can be overridden)
        elevation = st.number_input("Elevation (m) / Altitude (m)",
                                  value=st.session_state.manual_location_data.get('elevation', 648.0),
                                  min_value=0.0,
                                  max_value=5000.0,
                                  step=1.0,
                                  key="elevation_input")
        
        # Update button
        if st.button("Use this location / Usar esta localização"):
            # Update the manual location data
            st.session_state.manual_location_data = {
                'city': city,
                'region': region,
                'country': country,
                'latitude': latitude,
                'longitude': longitude,
                'elevation': elevation
            }
            
            # Get location info with the manual data
            with st.spinner("Processing location... / Processando localização..."):
                st.session_state.location_info = get_location_info(st.session_state.manual_location_data)
                st.session_state.manual_location = True
                st.rerun()
        
        # Show the current manual location on a map
        try:
            map_data = {
                'latitude': [st.session_state.manual_location_data['latitude']],
                'longitude': [st.session_state.manual_location_data['longitude']]
            }
            st.map(map_data, zoom=10)
        except Exception as e:
            st.warning(f"Could not display map: {str(e)}")
        
        # Display the manually entered location if it's being used
        if st.session_state.get('manual_location', False) and st.session_state.location_info:
            location = st.session_state.location_info
            
            # If we have elevation data, display it and use it for altitude
            if 'elevation' in location:
                altitude = location['elevation']
                st.info(f"Using elevation: {altitude:.1f} meters")
                st.session_state.altitude = altitude
                
                # Calculate atmospheric pressure from elevation
                p_atm = calculate_atmospheric_pressure(altitude)
                st.session_state.p_atm = p_atm
            else:
                st.warning("Could not determine elevation. Using manual input.")
                
                # Use manually entered elevation
                altitude = elevation
                st.session_state.altitude = altitude
                
                # Calculate atmospheric pressure from elevation
                p_atm = calculate_atmospheric_pressure(altitude)
                st.session_state.p_atm = p_atm
    
    # If we have valid location info from either method, use it
    if st.session_state.location_info:
        location = st.session_state.location_info
        
        # If location has elevation, use it for altitude
        if 'elevation' in location:
            altitude = location['elevation']
            # Use atmospheric pressure from location if available, otherwise calculate
            if 'atmospheric_pressure' in location:
                p_atm = location['atmospheric_pressure']
            else:
                p_atm = calculate_atmospheric_pressure(altitude)
        else:
            # No elevation, fall back to manual input
            st.warning("No elevation data available, using manual input for atmospheric pressure calculation.")
            altitude = st.number_input(
                "Altitude (m)", 
                min_value=0.0, 
                max_value=5000.0, 
                value=st.session_state.altitude, 
                step=10.0,
                help="Enter altitude in meters to calculate atmospheric pressure / Insira a altitude em metros para calcular a pressão atmosférica",
                key="altitude_input_geo_fallback"
            )
            p_atm = calculate_atmospheric_pressure(altitude)
            
        # Store in session state
        st.session_state.altitude = altitude
        st.session_state.p_atm = p_atm
    else:
        # No location info at all, allow manual entry of altitude directly
        st.error("No location information available. Please enter altitude manually. / Nenhuma informação de localização disponível. Por favor, insira a altitude manualmente.")
        altitude = st.number_input(
            "Altitude (m)", 
            min_value=0.0, 
            max_value=5000.0, 
            value=st.session_state.altitude, 
            step=10.0,
            help="Enter altitude in meters to calculate atmospheric pressure / Insira a altitude em metros para calcular a pressão atmosférica",
            key="altitude_input_geo_failed"
        )
        # Calculate atmospheric pressure using the altitude value
        p_atm = calculate_atmospheric_pressure(altitude)
        st.session_state.p_atm = p_atm
else:
    # Manual altitude input if geolocation is not used
    altitude = st.number_input(
        "Altitude (m)", 
        min_value=0.0, 
        max_value=5000.0, 
        value=st.session_state.altitude, 
        step=10.0,
        help="Enter altitude in meters to calculate atmospheric pressure / Insira a altitude em metros para calcular a pressão atmosférica",
        key="altitude_input"
    )
    # Update session state
    st.session_state.altitude = altitude
    
    # Calculate atmospheric pressure using the altitude value
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
