"""
Geolocation-based atmospheric pressure calculation
"""
import ipinfo
import requests
import streamlit as st
from psychrometrics import calculate_atmospheric_pressure

def get_location_info(manual_location=None):
    """
    Get the location information for the user
    
    Parameters:
        manual_location (dict, optional): Dictionary with manually entered location data
        
    Returns:
        dict: Dictionary containing location information
    """
    # If manual location is provided, use it
    if manual_location:
        try:
            # Extract coordinates
            lat = manual_location.get('latitude')
            lon = manual_location.get('longitude')
            
            # Validate coordinates
            if lat is None or lon is None:
                st.warning("Latitude e longitude são necessárias para localização manual.")
                return None
                
            # Create location dictionary
            location = {
                'city': manual_location.get('city', 'Unknown'),
                'region': manual_location.get('region', ''),
                'country': manual_location.get('country', 'Brazil'),
                'latitude': lat,
                'longitude': lon,
                'manual': True
            }
            
            # Try to get elevation if not provided
            if 'elevation' in manual_location and manual_location['elevation'] is not None:
                location['elevation'] = manual_location['elevation']
                location['atmospheric_pressure'] = calculate_atmospheric_pressure(location['elevation'])
            else:
                # Try to get elevation data from coordinates
                elevation = get_elevation(float(lat), float(lon))
                if elevation is not None:
                    location['elevation'] = elevation
                    # Calculate atmospheric pressure based on elevation
                    location['atmospheric_pressure'] = calculate_atmospheric_pressure(elevation)
            
            return location
        except Exception as e:
            st.warning(f"Erro ao processar localização manual: {str(e)}")
            return None
    
    # Otherwise try automatic geolocation
    try:
        # Get IP Info using ipinfo.io service
        handler = ipinfo.getHandler()
        details = handler.getDetails()
        
        # Extract relevant information
        location = {
            'city': details.city,
            'region': details.region,
            'country': details.country_name,
            'latitude': details.latitude,
            'longitude': details.longitude,
            'manual': False
        }
        
        # Try to get elevation data
        elevation = get_elevation(float(details.latitude), float(details.longitude))
        if elevation is not None:
            location['elevation'] = elevation
            # Calculate atmospheric pressure based on elevation
            location['atmospheric_pressure'] = calculate_atmospheric_pressure(elevation)
        
        return location
    except Exception as e:
        st.warning(f"Não foi possível obter localização automática: {str(e)}")
        return None

def get_elevation(lat, lon):
    """
    Get the elevation for a given latitude and longitude
    
    Parameters:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        float: Elevation in meters, None if request failed
    """
    try:
        # Use the Open-Elevation API to get altitude
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Extract elevation data from response
            elevation = data['results'][0]['elevation']
            return elevation
        else:
            # Try backup service
            return get_elevation_backup(lat, lon)
    except Exception:
        # If the primary service fails, try the backup
        return get_elevation_backup(lat, lon)

def get_elevation_backup(lat, lon):
    """
    Backup method to get elevation using alternative API
    
    Parameters:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        float: Elevation in meters, None if request failed
    """
    try:
        # Alternative elevation API
        url = f"https://elevation-api.io/api/elevation?points=({lat},{lon})"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Extract elevation data from response
            elevation = data['elevations'][0]['elevation']
            return elevation
    except Exception:
        # If all services fail, return None
        return None
    
    return None