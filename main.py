import streamlit as st
import sys
import os
import pickle
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_processor import DataProcessor
from src.config import PAGE_CONFIG


def create_data_dir():
    """Create data directory if it doesn't exist"""
    data_dir = Path("data/temp")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def save_data_processor(data_processor):
    """Save data processor to disk"""
    if data_processor:
        data_dir = create_data_dir()
        with open(data_dir / "data_processor.pkl", "wb") as f:
            pickle.dump(data_processor, f)


def load_data_processor():
    """Load data processor from disk"""
    data_dir = create_data_dir()
    pkl_file = data_dir / "data_processor.pkl"

    if pkl_file.exists():
        try:
            with open(pkl_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
    return None


def save_session_config():
    """Save current session configuration"""
    if st.session_state.get('selected_team'):
        data_dir = create_data_dir()
        config = {
            'selected_team': st.session_state.selected_team,
            'has_data': st.session_state.data_processor is not None,
            'current_page': st.session_state.get('current_page', 'dashboard')
        }
        with open(data_dir / "session_config.json", "w") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


def load_session_config():
    """Load session configuration"""
    data_dir = create_data_dir()
    config_file = data_dir / "session_config.json"

    if config_file.exists():
        try:
            with open(config_file, "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}


def initialize_session_state():
    """Initialize session state with persistence"""
    # Initialize basic state
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = None
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    if 'show_player_profile' not in st.session_state:
        st.session_state.show_player_profile = False
    if 'selected_player' not in st.session_state:
        st.session_state.selected_player = None

    # Try to load saved data
    if st.session_state.data_processor is None:
        saved_data = load_data_processor()
        if saved_data:
            st.session_state.data_processor = saved_data

    # Load saved config
    saved_config = load_session_config()
    if saved_config.get('selected_team') and not st.session_state.selected_team:
        st.session_state.selected_team = saved_config['selected_team']
    if saved_config.get('current_page'):
        st.session_state.current_page = saved_config['current_page']


def main():
    st.set_page_config(**PAGE_CONFIG)
    initialize_session_state()

    st.sidebar.title("⚽ Football Analytics")

    # Show status if data is loaded
    if st.session_state.data_processor:
        st.sidebar.success("📊 Data loaded from previous session")

        # Clear data option
        if st.sidebar.button("🗑️ Clear Saved Data"):
            clear_saved_data()
            st.rerun()

    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload Wyscout CSVs",
        type="csv",
        accept_multiple_files=True,
        help="Select all CSV files by position"
    )

    # Process uploaded files
    if uploaded_files:
        if st.session_state.data_processor is None:
            with st.spinner("Processing data..."):
                try:
                    st.session_state.data_processor = DataProcessor(uploaded_files)
                    save_data_processor(st.session_state.data_processor)
                    st.sidebar.success(f"✅ {len(uploaded_files)} files loaded & saved")
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
                    return

    # Team selection (only if data is loaded)
    if st.session_state.data_processor:
        teams = st.session_state.data_processor.get_teams()
        selected_team = st.sidebar.selectbox(
            "Select Team",
            teams,
            index=teams.index(st.session_state.selected_team) if st.session_state.selected_team in teams else 0
        )

        if selected_team != st.session_state.selected_team:
            st.session_state.selected_team = selected_team
            save_session_config()

        # Navigation menu
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🧭 Navigation")

        page_options = {
            'dashboard': '🏠 Team Dashboard',
            'player_profile': '👤 Player Profile',
            'scouting': '🔍 Scouting',
            'rankings': '📊 Rankings',
            'settings': '⚙️ Settings'
        }

        # Handle player profile navigation
        if st.session_state.show_player_profile and st.session_state.selected_player:
            st.session_state.current_page = 'player_profile'
            st.session_state.show_player_profile = False

        current_page = st.sidebar.radio(
            "Select Page",
            list(page_options.keys()),
            format_func=lambda x: page_options[x],
            index=list(page_options.keys()).index(st.session_state.current_page)
        )

        if current_page != st.session_state.current_page:
            st.session_state.current_page = current_page
            save_session_config()

        # Show selected page
        if current_page == 'dashboard':
            show_team_dashboard_page()
        elif current_page == 'player_profile':
            show_player_profile_page()
        elif current_page == 'scouting':
            show_scouting_page()
        elif current_page == 'rankings':
            show_rankings_page()
        elif current_page == 'settings':
            show_settings_page()

    else:
        show_welcome_screen()


def clear_saved_data():
    """Clear all saved data"""
    data_dir = create_data_dir()

    # Remove saved files
    for file_path in data_dir.glob("*"):
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

    # Clear session state
    st.session_state.data_processor = None
    st.session_state.selected_team = None
    st.session_state.current_page = 'dashboard'
    st.session_state.show_player_profile = False
    st.session_state.selected_player = None

    st.success("🗑️ All saved data cleared!")


def show_welcome_screen():
    st.title("⚽ Football Analytics Platform")
    st.markdown("""
    ### 🚀 Welcome to your football analytics platform!

    **To get started:**
    1. 📤 Upload Wyscout CSV files in the sidebar
    2. 🏆 Select your team
    3. 📊 Explore the available features

    **💾 Auto-Save Feature:**
    - Your data is automatically saved after upload
    - Team selection is remembered
    - No need to re-upload after refresh!

    **🔧 Available Features:**
    - 🏠 **Team Dashboard**: Squad overview with starters/subs
    - 👤 **Player Profiles**: Detailed individual analysis
    - 🔍 **Scouting**: Advanced player search and comparison
    - 📊 **Rankings**: Custom rankings by position
    - ⚙️ **Settings**: Personalization and configuration
    """)


def show_team_dashboard_page():
    """Show team dashboard page"""
    # Import the function directly
    import importlib.util
    import os

    # Get the path to the team_dashboard file
    dashboard_path = os.path.join(os.path.dirname(__file__), 'pages', 'team_dashboard.py')

    try:
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("team_dashboard", dashboard_path)
        team_dashboard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(team_dashboard)

        # Call the function
        team_dashboard.show_team_dashboard()
    except Exception as e:
        st.error(f"Error loading team dashboard: {e}")

        # Fallback - show basic team info
        show_basic_dashboard()


def show_player_profile_page():
    """Show player profile page"""
    st.title("👤 Player Profile")

    if st.session_state.selected_player:
        player_name = st.session_state.selected_player['name']
        position = st.session_state.selected_player['position']

        st.subheader(f"Profile: {player_name} ({position})")

        # Get player data
        player_data = st.session_state.data_processor.get_player_data(player_name, position)

        if player_data is not None:
            # Basic info
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Age", player_data.get('Idade', 'N/A'))
            with col2:
                st.metric("Height", player_data.get('Altura', 'N/A'))
            with col3:
                st.metric("Nationality", player_data.get('Nacionalidade', 'N/A'))
            with col4:
                st.metric("Foot", player_data.get('Pé', 'N/A'))

            # Performance metrics
            st.subheader("📊 Performance Metrics")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Minutes Played", int(player_data.get('Minutos jogados', 0)))
            with col2:
                st.metric("Goals", int(player_data.get('Gols', 0)))
            with col3:
                st.metric("Assists", int(player_data.get('Assistências', 0)))
            with col4:
                st.metric("Market Value", player_data.get('Valor de mercado', 'N/A'))

            # Show all available metrics
            st.subheader("🔍 All Metrics")

            # Filter out non-numeric and basic info columns
            exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado']
            numeric_cols = [col for col in player_data.index if
                            col not in exclude_cols and pd.api.types.is_numeric_dtype(type(player_data[col]))]

            # Display metrics in columns
            metrics_per_row = 4
            for i in range(0, len(numeric_cols), metrics_per_row):
                cols = st.columns(metrics_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(numeric_cols):
                        metric_name = numeric_cols[i + j]
                        metric_value = player_data[metric_name]

                        # Format value
                        if isinstance(metric_value, float):
                            formatted_value = f"{metric_value:.2f}"
                        else:
                            formatted_value = str(metric_value)

                        with col:
                            st.metric(metric_name, formatted_value)

        else:
            st.error(f"Player {player_name} not found in {position} data!")
    else:
        st.info("👆 Select a player from the Team Dashboard to view their profile!")

        # Back button
        if st.button("🏠 Back to Team Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()


def show_scouting_page():
    """Show scouting page (placeholder)"""
    st.title("🔍 Scouting System")
    st.info("🚧 Scouting system will be implemented in Fase 4!")

    st.markdown("""
    **Coming Soon:**
    - 🔎 Advanced player search
    - 📊 Performance filters
    - ⚖️ Player comparisons
    - 🏆 Rankings by position
    """)


def show_rankings_page():
    """Show rankings page (placeholder)"""
    st.title("📊 Rankings System")
    st.info("🚧 Rankings system will be implemented in Fase 4!")

    st.markdown("""
    **Coming Soon:**
    - 🏆 Pre-defined rankings by position
    - 🎯 Custom ranking creation
    - 📈 Percentile analysis
    - ⚖️ Weighted scoring systems
    """)


def show_settings_page():
    """Show settings page (placeholder)"""
    st.title("⚙️ Settings & Configuration")
    st.info("🚧 Settings will be implemented in Fase 5!")

    st.markdown("""
    **Coming Soon:**
    - 🎨 Custom metrics creation
    - 📊 Personalized radar charts
    - 💾 Export/Import configurations
    - ⭐ Favorites management
    """)


# Import pandas for player profile
import pandas as pd

if __name__ == "__main__":
    main()