import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import ConnectionPatch
from psychrometrics import (
    saturation_vapor_pressure,
    humidity_ratio_from_vapor_pressure,
    vapor_pressure_from_humidity_ratio,
    relative_humidity_from_vapor_pressure,
    enthalpy
)

def plot_psychrometric_chart(p_atm, properties=None, min_temp=-10, max_temp=50, fig_size=(10, 8)):
    """
    Plot a psychrometric chart with optional point marking for the current state.
    
    Parameters:
        p_atm (float): Atmospheric pressure in kPa
        properties (dict, optional): Properties of the state point to mark
        min_temp (float): Minimum temperature for chart (°C)
        max_temp (float): Maximum temperature for chart (°C)
        fig_size (tuple): Figure size as (width, height)
    
    Returns:
        matplotlib.figure.Figure: The figure object
    """
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=fig_size)
    ax2 = ax1.twinx()  # Create second y-axis that shares the same x-axis
    
    # Temperature range for plotting
    t_range = np.linspace(min_temp, max_temp, 200)
    
    # Humidity ratio range (0-30 g/kg) for a comfortable range
    max_w = 0.030  # 30 g/kg
    
    # 1. Plot saturation curve (100% RH)
    p_ws_values = np.array([saturation_vapor_pressure(t) for t in t_range])
    w_s_values = np.array([humidity_ratio_from_vapor_pressure(p_ws, p_atm) for p_ws in p_ws_values])
    
    # Limit to chart range
    w_s_values = np.clip(w_s_values, 0, max_w)
    
    # Plot saturation curve with thicker line - now plot pressure on primary axis
    line_sat, = ax1.plot(t_range, p_ws_values, 'k-', linewidth=2, label='Saturação (UR = 100%)')
    
    # 2. Plot RH curves (20%, 40%, 60%, 80%)
    rh_values = [20, 40, 60, 80]
    for rh in rh_values:
        p_v_values = np.array([(rh / 100) * saturation_vapor_pressure(t) for t in t_range])
        
        # Plot RH curve - now plot pressure on primary axis
        line_rh = None
        if rh == rh_values[0]:
            line_rh, = ax1.plot(t_range, p_v_values, 'b--', linewidth=0.7, alpha=0.7, label=f'UR = {rh}%')
        else:
            ax1.plot(t_range, p_v_values, 'b--', linewidth=0.7, alpha=0.7)
        
        # Label the RH curve at a reasonable position
        # Find index where the curve is in the middle of the chart
        label_idx = np.abs(t_range - (min_temp + 0.7 * (max_temp - min_temp))).argmin()
        ax1.text(t_range[label_idx], p_v_values[label_idx], f'{rh}%', 
                color='blue', fontsize=8, ha='center', va='bottom')
    
    # 3. Plot constant dry-bulb temperature lines (vertical)
    temp_lines = np.arange(min_temp, max_temp + 1, 5)
    for t in temp_lines:
        # Plot vertical line only - no labels (we'll use axis ticks instead)
        ax1.axvline(x=t, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    # Removido: Plot constant wet-bulb temperature lines (diagonal)
    
    # 5. Plot constant enthalpy lines
    h_lines = np.arange(0, 100 + 1, 10)
    
    line_enth = None
    for h_val in h_lines:
        # For each enthalpy, we need to find combinations of t and w that give this value
        # w = (h - 1.006 * t) / (2501 + 1.86 * t)
        w_enthalpy = np.array([(h_val - 1.006 * t) / (2501 + 1.86 * t) for t in t_range])
        
        # Filter valid values within range
        valid_idx = (w_enthalpy >= 0) & (w_enthalpy <= max_w)
        
        if np.any(valid_idx):
            t_valid = t_range[valid_idx]
            w_valid = w_enthalpy[valid_idx]
            
            # Convert to vapor pressure for the primary axis
            p_v_valid = np.array([vapor_pressure_from_humidity_ratio(w, p_atm) for w in w_valid])
            
            # Plot enthalpy line
            if h_val == 40:  # Use one value for the legend
                line_enth, = ax1.plot(t_valid, p_v_valid, 'r--', linewidth=0.7, alpha=0.5, 
                                     label='Entalpia (kJ/kg)')
            else:
                ax1.plot(t_valid, p_v_valid, 'r--', linewidth=0.7, alpha=0.5)
            
            # Label the enthalpy line at a reasonable position
            mid_idx = len(t_valid) // 2
            if mid_idx < len(t_valid):
                ax1.text(t_valid[mid_idx], p_v_valid[mid_idx], 
                        f'{h_val} kJ/kg', color='red', fontsize=8, ha='left', va='bottom', rotation=-15)
    
    # 6. Mark the point if properties are provided
    line_point = None
    if properties is not None:
        tbs = properties['tbs']
        w = properties['w']
        p_v = properties['p_v']  # Use pressure of vapor directly
        
        # Plot point
        ax1.plot(tbs, p_v, 'ko', markersize=8)
        line_point, = ax1.plot(tbs, p_v, 'ro', markersize=6, label='Ponto de Estado')
        
        # Add horizontal and vertical lines to axes for the point
        ax1.axhline(y=p_v, color='red', linestyle='--', linewidth=0.7, alpha=0.7)
        ax1.axvline(x=tbs, color='red', linestyle='--', linewidth=0.7, alpha=0.7)
        
        # Add labels for the state point
        # Format with 2 decimal places
        ax1.text(tbs + 1, p_v, 
                f"Estado do Ar:\nTbs = {tbs:.1f}°C\nUR = {properties['ur']:.1f}%\nw = {w*1000:.2f} g/kg\nh = {properties['h']:.1f} kJ/kg\nPv = {p_v:.4f} kPa", 
                fontsize=9, bbox=dict(facecolor='white', alpha=0.8))
        
        # Show wet bulb temperature and dew point as lines
        if 'tbm' in properties and 'tpo' in properties:
            tbm = properties['tbm']
            tpo = properties['tpo']
            
            # Encontrar o ponto na curva de saturação (UR=100%) onde Tbs = Tbm
            p_ws_tbm = saturation_vapor_pressure(tbm)  # Pressão de vapor na saturação para Tbm
            
            # Desenhar linha verde que vai da curva de saturação em Tbm até o ponto de estado
            ax1.plot([tbm, tbs], [p_ws_tbm, p_v], 'g-', linewidth=1.5, alpha=0.8)
            
            # Adicionar rótulo para a temperatura de bulbo molhado
            ax1.text(tbm, p_ws_tbm, f"Tbm = {tbm:.1f}°C", 
                     color='green', fontsize=9, ha='right', va='bottom')
            
            # Add dew point line (horizontal to saturation curve)
            p_ws_tpo = saturation_vapor_pressure(tpo)
            
            ax1.plot([tpo, tpo], [p_v, p_ws_tpo], 'b--', linewidth=0.7, alpha=0.7)
            ax1.text(tpo, p_ws_tpo, f"Tpo = {tpo:.1f}°C", 
                     color='blue', fontsize=9, ha='center', va='bottom')
    
    # Configure the primary y-axis (Vapor Pressure)
    ax1.set_xlabel('Temperatura de Bulbo Seco (°C)')
    ax1.set_ylabel('Pressão de Vapor (kPa)')
    ax1.set_xlim(min_temp - 2, max_temp + 2)
    
    # Calculate vapor pressure range based on humidity ratio and atmospheric pressure
    max_pv = vapor_pressure_from_humidity_ratio(max_w, p_atm)
    ax1.set_ylim(-0.2, max_pv + 0.5)
    
    # Configure x-axis ticks to match our temperature lines
    ax1.set_xticks(temp_lines)
    ax1.set_xticklabels([f"{t}°C" for t in temp_lines])
    
    # Rotate labels for better visibility
    plt.setp(ax1.get_xticklabels(), fontsize=8)
    
    # Configure the secondary y-axis (Humidity Ratio)
    ax2.set_ylabel('Razão de Mistura (g/kg)')
    ax2.set_ylim(-1, max_w * 1000 + 1)
    
    # Set tick locations and labels for secondary y-axis (razão de mistura)
    # We need to convert from vapor pressure (primary axis) to humidity ratio
    w_ticks = np.linspace(0, max_w * 1000, 7)  # g/kg values
    ax2.set_yticks(w_ticks)
    ax2.set_yticklabels([f"{w:.1f}" for w in w_ticks])
    
    # Chart title
    plt.title(f'Carta Psicrométrica (Pressão: {p_atm:.2f} kPa)')
    
    # Add grid
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # Create a proper legend with all the different elements
    legend_elements = []
    if line_sat:
        legend_elements.append(line_sat)
    if line_rh:
        legend_elements.append(line_rh)
    if line_enth:
        legend_elements.append(line_enth)
    if line_point:
        legend_elements.append(line_point)
    
    if legend_elements:
        ax1.legend(handles=legend_elements, loc='upper left', fontsize=8)
    
    plt.tight_layout()
    return fig