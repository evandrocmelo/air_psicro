import streamlit as st
import numpy as np
import pandas as pd
from psychrometric_chart import plot_psychrometric_chart

def input_with_units(label, unit, min_value=None, max_value=None, value=None, step=None, key=None):
    """
    Create an input field with units displayed
    
    Parameters:
        label (str): Label for the input field
        unit (str): Unit to display
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        value: Default value
        step: Step size for the input
        key: Unique key for the input field
        
    Returns:
        Value from the input field
    """
    col1, col2 = st.columns([4, 1])
    with col1:
        val = st.number_input(
            label, 
            min_value=min_value, 
            max_value=max_value, 
            value=value, 
            step=step,
            key=key,
            label_visibility="visible"
        )
    with col2:
        st.markdown(f"<div style='padding-top: 30px'>{unit}</div>", unsafe_allow_html=True)
    return val

def display_results(properties):
    """
    Display the calculated properties in a formatted way
    
    Parameters:
        properties (dict): Dictionary of calculated properties
    """
    st.subheader("Results / Resultados")
    
    # Highlight atmospheric pressure in a prominent box
    st.info(f"**Atmospheric Pressure / Pressão Atmosférica**: {properties['p_atm']:.2f} kPa")
    
    # Create three columns for displaying results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Dry-bulb Temperature / Temperatura de Bulbo Seco", f"{properties['tbs']:.2f} °C")
        st.metric("Wet-bulb Temperature / Temperatura de Bulbo Molhado", f"{properties['tbm']:.2f} °C")
        st.metric("Dew Point Temperature / Temperatura de Ponto de Orvalho", f"{properties['tpo']:.2f} °C")
    
    with col2:
        st.metric("Relative Humidity / Umidade Relativa", f"{properties['ur']:.2f} %")
        st.metric("Humidity Ratio / Razão de Mistura", f"{properties['w']*1000:.2f} g/kg")
        st.metric("Specific Volume / Volume Específico", f"{properties['v']:.4f} m³/kg")
    
    with col3:
        st.metric("Enthalpy / Entalpia", f"{properties['h']:.2f} kJ/kg")
        st.metric("Vapor Pressure / Pressão de Vapor", f"{properties['p_v']:.4f} kPa")
        st.metric("Saturation Pressure / Pressão de Saturação", f"{properties['p_ws']:.4f} kPa")
    
    # Create a DataFrame for detailed results
    data = {
        "Property / Propriedade": [
            "Dry-bulb Temperature / Temperatura de Bulbo Seco",
            "Wet-bulb Temperature / Temperatura de Bulbo Molhado",
            "Dew Point Temperature / Temperatura de Ponto de Orvalho",
            "Relative Humidity / Umidade Relativa",
            "Humidity Ratio / Razão de Mistura",
            "Specific Volume / Volume Específico",
            "Enthalpy / Entalpia",
            "Vapor Pressure / Pressão de Vapor",
            "Saturation Pressure / Pressão de Saturação",
            "Atmospheric Pressure / Pressão Atmosférica"
        ],
        "Value / Valor": [
            f"{properties['tbs']:.2f} °C",
            f"{properties['tbm']:.2f} °C",
            f"{properties['tpo']:.2f} °C",
            f"{properties['ur']:.2f} %",
            f"{properties['w']*1000:.2f} g/kg",
            f"{properties['v']:.4f} m³/kg",
            f"{properties['h']:.2f} kJ/kg",
            f"{properties['p_v']:.4f} kPa",
            f"{properties['p_ws']:.4f} kPa",
            f"{properties['p_atm']:.2f} kPa"
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Generate psychrometric chart with the current state point
    st.subheader("Psychrometric Chart / Carta Psicrométrica")
    
    # Set temperature range based on current point
    tbs = properties['tbs']
    min_temp = max(-10, tbs - 20)
    max_temp = min(50, tbs + 20)
    
    try:
        # Wrap chart generation in try-except to catch any errors
        fig = plot_psychrometric_chart(properties['p_atm'], properties, min_temp=min_temp, max_temp=max_temp)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating psychrometric chart: {str(e)}")
        st.info("The calculation results are still valid, but the chart could not be displayed.")
    
    # Display detailed results in an expander
    with st.expander("Detailed Results / Resultados Detalhados"):
        st.dataframe(df, hide_index=True)
        
        # Explanation of properties
        st.markdown("""
        ### Property Explanations / Explicações das Propriedades:
        
        **English**:
        - **Dry-bulb Temperature**: The temperature of air measured by a thermometer freely exposed to the air but shielded from radiation and moisture.
        - **Wet-bulb Temperature**: The temperature a parcel of air would have if cooled to saturation by evaporation of water into it.
        - **Dew Point Temperature**: The temperature at which air becomes saturated with water vapor when cooled.
        - **Relative Humidity**: The ratio of the partial pressure of water vapor to the saturation vapor pressure at a given temperature.
        - **Humidity Ratio**: The mass of water vapor per unit mass of dry air.
        - **Specific Volume**: The volume occupied by a unit mass of dry air.
        - **Enthalpy**: The total energy of the air, including sensible and latent components.
        - **Vapor Pressure**: The partial pressure of water vapor in the air.
        - **Saturation Pressure**: The maximum water vapor pressure possible at a given temperature.
        
        **Português**:
        - **Temperatura de Bulbo Seco**: A temperatura do ar medida por um termômetro exposto livremente ao ar, mas protegido da radiação e umidade.
        - **Temperatura de Bulbo Molhado**: A temperatura que uma parcela de ar teria se fosse resfriada até a saturação pela evaporação de água.
        - **Temperatura de Ponto de Orvalho**: A temperatura na qual o ar se torna saturado com vapor de água quando resfriado.
        - **Umidade Relativa**: A razão entre a pressão parcial de vapor de água e a pressão de saturação do vapor a uma dada temperatura.
        - **Razão de Mistura**: A massa de vapor de água por unidade de massa de ar seco.
        - **Volume Específico**: O volume ocupado por uma unidade de massa de ar seco.
        - **Entalpia**: A energia total do ar, incluindo componentes sensíveis e latentes.
        - **Pressão de Vapor**: A pressão parcial do vapor de água no ar.
        - **Pressão de Saturação**: A pressão máxima de vapor de água possível a uma dada temperatura.
        """)
