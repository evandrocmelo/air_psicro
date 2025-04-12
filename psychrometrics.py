import numpy as np
import math

# Constants
R_a = 287.05  # Gas constant for dry air, J/(kg·K)
R_v = 461.5   # Gas constant for water vapor, J/(kg·K)
P_std = 101.325  # Standard atmospheric pressure, kPa
g = 9.81      # Gravitational acceleration, m/s²
T_0 = 273.15  # Zero Celsius in Kelvin

def calculate_atmospheric_pressure(altitude):
    """
    Calculate atmospheric pressure based on altitude using barometric formula
    
    Parameters:
        altitude (float): Altitude in meters
        
    Returns:
        float: Atmospheric pressure in kPa
    """
    # Ensure altitude is a valid numerical value
    try:
        altitude_value = float(altitude)
    except (ValueError, TypeError):
        # Return standard pressure if conversion fails
        return P_std
    
    # Barometric formula for altitude correction (ASHRAE)
    p_atm = P_std * (1 - 2.25577e-5 * altitude_value) ** 5.2559
    
    # Ensure we have a reasonable value (between 10% and 110% of standard pressure)
    p_atm = max(P_std * 0.1, min(p_atm, P_std * 1.1))
    
    return p_atm

def saturation_vapor_pressure(t):
    """
    Calculate saturation vapor pressure at given temperature
    
    Parameters:
        t (float): Temperature in °C
        
    Returns:
        float: Saturation vapor pressure in kPa
    """
    T = t + T_0  # Convert to Kelvin
    
    if t >= 0:
        # For temperatures above freezing
        log_p_ws = -5.8002206e3 / T + 1.3914993 - 4.8640239e-2 * T + \
                   4.1764768e-5 * T**2 - 1.4452093e-8 * T**3 + 6.5459673 * np.log(T)
    else:
        # For temperatures below freezing
        log_p_ws = -5.6745359e3 / T + 6.3925247 - 9.677843e-3 * T + \
                   6.2215701e-7 * T**2 + 2.0747825e-9 * T**3 - 9.484024e-13 * T**4 + \
                   4.1635019 * np.log(T)
    
    p_ws = np.exp(log_p_ws)  # In pascals
    return p_ws / 1000  # Convert to kPa

def humidity_ratio_from_vapor_pressure(p_v, p_atm):
    """
    Calculate humidity ratio from vapor pressure
    
    Parameters:
        p_v (float): Vapor pressure in kPa
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        float: Humidity ratio in kg water vapor / kg dry air
    """
    return 0.62198 * p_v / (p_atm - p_v)

def vapor_pressure_from_humidity_ratio(w, p_atm):
    """
    Calculate vapor pressure from humidity ratio
    
    Parameters:
        w (float): Humidity ratio in kg water vapor / kg dry air
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        float: Vapor pressure in kPa
    """
    return p_atm * w / (0.62198 + w)

def relative_humidity_from_vapor_pressure(p_v, p_ws):
    """
    Calculate relative humidity from vapor pressure
    
    Parameters:
        p_v (float): Vapor pressure in kPa
        p_ws (float): Saturation vapor pressure in kPa
        
    Returns:
        float: Relative humidity (0-100)
    """
    return 100 * p_v / p_ws

def dew_point_temperature(p_v):
    """
    Calculate dew point temperature from vapor pressure
    
    Parameters:
        p_v (float): Vapor pressure in kPa
        
    Returns:
        float: Dew point temperature in °C
    """
    # Handle edge case where p_v is very close to zero or zero
    if p_v < 0.001:
        return -20.0  # Return very low dew point for very dry air
    
    # Using more reliable empirical formulas
    a = 17.27
    b = 237.7
    
    # Convert kPa to Pa for calculation
    p_v_pa = p_v * 1000
    
    # Calculate dew point using simplified approach
    # These constants are based on Magnus-Tetens formula
    gamma = np.log(p_v_pa / 611.2)
    t_dp = (b * gamma) / (a - gamma)
    
    # Ensure value is in reasonable range
    t_dp = max(-50.0, min(t_dp, 60.0))
    
    return t_dp

def wet_bulb_temperature(tbs, w, p_atm):
    """
    Calculate wet bulb temperature using iteration
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        w (float): Humidity ratio in kg water vapor / kg dry air
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        float: Wet bulb temperature in °C
    """
    # Handle edge cases
    if w <= 0.0001:  # Very dry air
        return max(-20.0, tbs - 15.0)  # Significant depression for very dry air
        
    # Starting guess for wet bulb temperature - more conservative approach
    tbm = tbs - 2.0  # Start closer to dry bulb for stability
    
    # Precision goal
    epsilon = 0.01
    max_iterations = 50
    
    # Guard against invalid inputs
    if not (isinstance(tbs, (int, float)) and isinstance(w, (int, float)) and isinstance(p_atm, (int, float))):
        return tbs - 5.0  # Return reasonable estimate if inputs are problematic
    
    # Use try-except to handle numerical issues
    try:
        for i in range(max_iterations):
            # Saturation vapor pressure at wet bulb temperature
            p_ws_tbm = saturation_vapor_pressure(tbm)
            
            # Humidity ratio at wet bulb temperature (saturated)
            w_s_tbm = humidity_ratio_from_vapor_pressure(p_ws_tbm, p_atm)
            
            # Humidity ratio from psychrometric relation
            h_fg = 2501 - 2.326 * tbm  # Latent heat of vaporization, kJ/kg
            c_pa = 1.006  # Specific heat of dry air, kJ/(kg·K)
            factor = h_fg - 4.186 * (tbs - tbm)
            
            # Avoid division by zero or very small values
            if abs(factor) < 0.001:
                factor = 0.001 if factor >= 0 else -0.001
                
            w_calc = ((factor) * w_s_tbm - c_pa * (tbs - tbm)) / factor
            
            # Check convergence
            if abs(w_calc - w) < epsilon:
                return tbm
            
            # Adjust wet bulb temperature with smaller steps for better convergence
            if w_calc > w:
                tbm -= 0.05
            else:
                tbm += 0.05
            
            # Ensure tbm stays in reasonable range
            tbm = max(-20.0, min(tbm, tbs))
    except Exception:
        # If any calculation errors occur, return a reasonable estimate
        return tbs - 5.0 if tbs > 10 else tbs * 0.9
    
    # If no convergence, return the best estimate with bounds checking
    return max(-20.0, min(tbm, tbs))

def specific_volume(tbs, w, p_atm):
    """
    Calculate specific volume of humid air
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        w (float): Humidity ratio in kg water vapor / kg dry air
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        float: Specific volume in m³/kg dry air
    """
    T = tbs + T_0  # Convert to Kelvin
    return (R_a * T / (p_atm * 1000)) * (1 + 1.6078 * w)

def enthalpy(tbs, w):
    """
    Calculate specific enthalpy of humid air
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        w (float): Humidity ratio in kg water vapor / kg dry air
        
    Returns:
        float: Specific enthalpy in kJ/kg dry air
    """
    return 1.006 * tbs + w * (2501 + 1.86 * tbs)

def calculate_properties_tbs_tbm(tbs, tbm, p_atm):
    """
    Calculate all properties from dry-bulb and wet-bulb temperatures
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        tbm (float): Wet bulb temperature in °C
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        dict: Dictionary containing all calculated properties
    """
    # Special case: if dry bulb equals wet bulb, we have 100% relative humidity
    if abs(tbs - tbm) < 0.01:
        # At saturation (UR = 100%), tbs = tbm = tpo
        p_ws_tbs = saturation_vapor_pressure(tbs)
        p_v = p_ws_tbs  # Vapor pressure equals saturation pressure at 100% UR
        ur = 100.0
        w = humidity_ratio_from_vapor_pressure(p_v, p_atm)
        tpo = tbs  # Dew point equals dry bulb at saturation
    else:
        # Saturation vapor pressure at wet bulb temperature
        p_ws_tbm = saturation_vapor_pressure(tbm)
        
        # Saturation vapor pressure at dry bulb temperature
        p_ws_tbs = saturation_vapor_pressure(tbs)
        
        # Humidity ratio calculation from psychrometric wet bulb equation
        h_fg = 2501 - 2.326 * tbm  # Latent heat of vaporization, kJ/kg
        w_s_tbm = humidity_ratio_from_vapor_pressure(p_ws_tbm, p_atm)
        w = ((h_fg - 4.186 * (tbs - tbm)) * w_s_tbm - 1.006 * (tbs - tbm)) / (h_fg - 4.186 * (tbs - tbm))
        
        # Vapor pressure from humidity ratio
        p_v = vapor_pressure_from_humidity_ratio(w, p_atm)
        
        # Relative humidity
        ur = relative_humidity_from_vapor_pressure(p_v, p_ws_tbs)
        
        # Dew point temperature
        tpo = dew_point_temperature(p_v)
    
    # Specific volume
    v = specific_volume(tbs, w, p_atm)
    
    # Enthalpy
    h = enthalpy(tbs, w)
    
    return {
        'tbs': tbs,
        'tbm': tbm,
        'ur': ur,
        'w': w,
        'tpo': tpo,
        'h': h,
        'v': v,
        'p_v': p_v,
        'p_ws': p_ws_tbs,
        'p_atm': p_atm
    }

def calculate_properties_tbs_ur(tbs, ur, p_atm):
    """
    Calculate all properties from dry-bulb temperature and relative humidity
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        ur (float): Relative humidity (0-100)
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        dict: Dictionary containing all calculated properties
    """
    # Saturation vapor pressure at dry bulb temperature
    p_ws_tbs = saturation_vapor_pressure(tbs)
    
    # Vapor pressure from relative humidity
    p_v = (ur / 100) * p_ws_tbs
    
    # Humidity ratio
    w = humidity_ratio_from_vapor_pressure(p_v, p_atm)
    
    # Dew point temperature
    tpo = dew_point_temperature(p_v)
    
    # Special case: if UR is 100% (or very close), tbs = tbm
    if abs(ur - 100.0) < 0.1:
        tbm = tbs  # At saturation, wet bulb equals dry bulb
    else:
        # Normal calculation for non-saturated air
        tbm = wet_bulb_temperature(tbs, w, p_atm)
    
    # Specific volume
    v = specific_volume(tbs, w, p_atm)
    
    # Enthalpy
    h = enthalpy(tbs, w)
    
    return {
        'tbs': tbs,
        'tbm': tbm,
        'ur': ur,
        'w': w,
        'tpo': tpo,
        'h': h,
        'v': v,
        'p_v': p_v,
        'p_ws': p_ws_tbs,
        'p_atm': p_atm
    }

def calculate_properties_tbs_tpo(tbs, tpo, p_atm):
    """
    Calculate all properties from dry-bulb and dew point temperatures
    
    Parameters:
        tbs (float): Dry bulb temperature in °C
        tpo (float): Dew point temperature in °C
        p_atm (float): Atmospheric pressure in kPa
        
    Returns:
        dict: Dictionary containing all calculated properties
    """
    # Saturation vapor pressure at dry bulb temperature
    p_ws_tbs = saturation_vapor_pressure(tbs)
    
    # Vapor pressure equals saturation vapor pressure at dew point
    p_v = saturation_vapor_pressure(tpo)
    
    # Relative humidity
    ur = relative_humidity_from_vapor_pressure(p_v, p_ws_tbs)
    
    # Humidity ratio
    w = humidity_ratio_from_vapor_pressure(p_v, p_atm)
    
    # Special case: if UR is 100% (or very close), tbs = tbm
    # This happens when dry bulb is equal to dew point
    if abs(ur - 100.0) < 0.1:
        tbm = tbs  # At saturation, wet bulb equals dry bulb
    else:
        # Normal calculation for non-saturated air
        tbm = wet_bulb_temperature(tbs, w, p_atm)
    
    # Specific volume
    v = specific_volume(tbs, w, p_atm)
    
    # Enthalpy
    h = enthalpy(tbs, w)
    
    return {
        'tbs': tbs,
        'tbm': tbm,
        'ur': ur,
        'w': w,
        'tpo': tpo,
        'h': h,
        'v': v,
        'p_v': p_v,
        'p_ws': p_ws_tbs,
        'p_atm': p_atm
    }
