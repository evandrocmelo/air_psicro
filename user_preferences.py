"""
User preferences storage for the Psychrometric Calculator
"""
import streamlit as st
import json
import base64
import datetime

def init_preferences():
    """
    Initialize user preferences in session state if not already present
    """
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'saved_profiles': {},  # Dictionary to store named profiles
            'current_profile': None,  # Name of the currently active profile
            'last_saved': None,  # Timestamp of last save
        }

def save_current_settings(profile_name):
    """
    Save current app settings to a named profile
    
    Parameters:
        profile_name (str): Name to identify the saved profile
    """
    # Make sure preferences are initialized
    init_preferences()
    
    # Collect current settings from session state
    current_settings = {
        # Location/altitude settings
        'altitude': st.session_state.altitude,
        'know_altitude': st.session_state.know_altitude,
        'manual_location_data': st.session_state.manual_location_data,
        
        # Input method preferences (latest values used)
        'tbs1': st.session_state.get('tbs1', 25.0),
        'tbm': st.session_state.get('tbm', 18.0),
        'tbs2': st.session_state.get('tbs2', 25.0),
        'ur': st.session_state.get('ur', 50.0),
        'tbs3': st.session_state.get('tbs3', 25.0),
        'tpo': st.session_state.get('tpo', 15.0),
        
        # Metadata
        'created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': f"Saved profile: {profile_name}"
    }
    
    # Save to user_preferences
    st.session_state.user_preferences['saved_profiles'][profile_name] = current_settings
    st.session_state.user_preferences['current_profile'] = profile_name
    st.session_state.user_preferences['last_saved'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return True

def load_profile(profile_name):
    """
    Load a previously saved profile and apply its settings
    
    Parameters:
        profile_name (str): Name of the profile to load
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Make sure preferences are initialized
    init_preferences()
    
    # Check if profile exists
    if profile_name not in st.session_state.user_preferences['saved_profiles']:
        return False
    
    # Get profile settings
    profile = st.session_state.user_preferences['saved_profiles'][profile_name]
    
    # Apply settings to session state
    if 'altitude' in profile:
        st.session_state.altitude = profile['altitude']
    if 'know_altitude' in profile:
        st.session_state.know_altitude = profile['know_altitude']
    if 'manual_location_data' in profile:
        st.session_state.manual_location_data = profile['manual_location_data']
    
    # Apply input method values if they exist
    for key in ['tbs1', 'tbm', 'tbs2', 'ur', 'tbs3', 'tpo']:
        if key in profile:
            st.session_state[key] = profile[key]
    
    # Update current profile
    st.session_state.user_preferences['current_profile'] = profile_name
    
    # Calculate atmospheric pressure based on altitude
    from psychrometrics import calculate_atmospheric_pressure
    st.session_state.p_atm = calculate_atmospheric_pressure(st.session_state.altitude)
    
    return True

def delete_profile(profile_name):
    """
    Delete a saved profile
    
    Parameters:
        profile_name (str): Name of the profile to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Make sure preferences are initialized
    init_preferences()
    
    # Check if profile exists
    if profile_name not in st.session_state.user_preferences['saved_profiles']:
        return False
    
    # Delete profile
    del st.session_state.user_preferences['saved_profiles'][profile_name]
    
    # If current profile was deleted, set current profile to None
    if st.session_state.user_preferences['current_profile'] == profile_name:
        st.session_state.user_preferences['current_profile'] = None
    
    return True

def export_all_profiles():
    """
    Export all saved profiles as a JSON string
    
    Returns:
        str: Base64-encoded JSON string of all profiles
    """
    # Make sure preferences are initialized
    init_preferences()
    
    # Get all profiles
    profiles = st.session_state.user_preferences['saved_profiles']
    
    # Convert to JSON string
    json_str = json.dumps(profiles, indent=2)
    
    # Encode to base64 for easier copy-paste
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    return encoded

def import_profiles(encoded_data):
    """
    Import profiles from a base64-encoded JSON string
    
    Parameters:
        encoded_data (str): Base64-encoded JSON string of profiles
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Decode base64
        json_str = base64.b64decode(encoded_data).decode('utf-8')
        
        # Parse JSON
        profiles = json.loads(json_str)
        
        # Make sure preferences are initialized
        init_preferences()
        
        # Update saved profiles
        for profile_name, profile_data in profiles.items():
            st.session_state.user_preferences['saved_profiles'][profile_name] = profile_data
        
        return True
    except Exception as e:
        st.error(f"Error importing profiles: {str(e)}")
        return False

def get_profile_names():
    """
    Get list of all saved profile names
    
    Returns:
        list: List of profile names
    """
    # Make sure preferences are initialized
    init_preferences()
    
    # Return list of profile names
    return list(st.session_state.user_preferences['saved_profiles'].keys())

def get_current_profile_name():
    """
    Get name of currently active profile
    
    Returns:
        str: Name of current profile, or None if no profile is active
    """
    # Make sure preferences are initialized
    init_preferences()
    
    return st.session_state.user_preferences['current_profile']

def render_preferences_ui():
    """
    Render the user preferences UI
    
    Returns:
        None
    """
    # Make sure preferences are initialized
    init_preferences()
    
    st.subheader("Preferências do Usuário / User Preferences")
    
    # Create tabs for different preference actions
    pref_tab1, pref_tab2, pref_tab3 = st.tabs([
        "Salvar / Save", 
        "Carregar / Load", 
        "Exportar/Importar / Export/Import"
    ])
    
    # Tab 1: Save current settings
    with pref_tab1:
        st.write("Salve as configurações atuais como um perfil / Save current settings as a profile")
        
        # Profile name input
        profile_name = st.text_input(
            "Nome do perfil / Profile name",
            key="save_profile_name",
            placeholder="Meu Perfil / My Profile"
        )
        
        # Optional description
        profile_desc = st.text_area(
            "Descrição (opcional) / Description (optional)",
            key="save_profile_desc",
            placeholder="Descreva este perfil... / Describe this profile..."
        )
        
        # Save button
        if st.button("Salvar Configurações / Save Settings"):
            if not profile_name:
                st.error("Por favor, insira um nome para o perfil / Please enter a profile name")
            else:
                success = save_current_settings(profile_name)
                if success:
                    st.success(f"Perfil '{profile_name}' salvo com sucesso! / Profile saved successfully!")
                else:
                    st.error("Erro ao salvar perfil / Error saving profile")
    
    # Tab 2: Load saved settings
    with pref_tab2:
        st.write("Carregue um perfil salvo / Load a saved profile")
        
        # Get list of saved profiles
        profile_names = get_profile_names()
        
        if not profile_names:
            st.info("Nenhum perfil salvo ainda. Salve suas configurações primeiro. / No saved profiles yet. Save your settings first.")
        else:
            # Dropdown to select profile
            selected_profile = st.selectbox(
                "Selecione um perfil / Select a profile",
                options=profile_names,
                index=0,
                key="load_profile_select"
            )
            
            # Show profile details if available
            if selected_profile:
                profile = st.session_state.user_preferences['saved_profiles'][selected_profile]
                st.write(f"**Criado em / Created on:** {profile.get('created', 'N/A')}")
                
                # Display location info
                if 'manual_location_data' in profile:
                    loc = profile['manual_location_data']
                    st.write(f"**Localização / Location:** {loc.get('city', '')}, {loc.get('region', '')}, {loc.get('country', '')}")
                
                # Display altitude
                if 'altitude' in profile:
                    st.write(f"**Altitude:** {profile['altitude']} m")
                
                # Load and delete buttons in columns
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Carregar Perfil / Load Profile"):
                        success = load_profile(selected_profile)
                        if success:
                            st.success(f"Perfil '{selected_profile}' carregado com sucesso! / Profile loaded successfully!")
                            st.rerun()
                        else:
                            st.error("Erro ao carregar perfil / Error loading profile")
                
                with col2:
                    if st.button("Excluir Perfil / Delete Profile"):
                        success = delete_profile(selected_profile)
                        if success:
                            st.success(f"Perfil '{selected_profile}' excluído com sucesso! / Profile deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir perfil / Error deleting profile")
    
    # Tab 3: Export/Import
    with pref_tab3:
        # Create subtabs for export and import
        export_tab, import_tab = st.tabs(["Exportar / Export", "Importar / Import"])
        
        # Export tab
        with export_tab:
            st.write("Exporte todos os seus perfis salvos / Export all your saved profiles")
            
            # Check if we have any profiles to export
            if not get_profile_names():
                st.info("Nenhum perfil salvo para exportar / No saved profiles to export")
            else:
                if st.button("Gerar Código de Exportação / Generate Export Code"):
                    export_code = export_all_profiles()
                    st.code(export_code, language=None)
                    st.info("Copie o código acima para transferir seus perfis para outro dispositivo / Copy the code above to transfer your profiles to another device")
        
        # Import tab
        with import_tab:
            st.write("Importe perfis de outro dispositivo / Import profiles from another device")
            
            import_code = st.text_area(
                "Cole o código de exportação aqui / Paste export code here",
                key="import_code_area",
                height=150
            )
            
            if st.button("Importar Perfis / Import Profiles"):
                if not import_code:
                    st.error("Por favor, insira um código de exportação / Please enter an export code")
                else:
                    success = import_profiles(import_code)
                    if success:
                        st.success("Perfis importados com sucesso! / Profiles imported successfully!")
                        st.rerun()
                    else:
                        st.error("Erro ao importar perfis. Verifique o código e tente novamente. / Error importing profiles. Check the code and try again.")