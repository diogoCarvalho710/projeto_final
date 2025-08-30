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
            'has_data': st.session_state.data_processor is not None
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
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = None
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = None

    # Try to load saved data
    if st.session_state.data_processor is None:
        saved_data = load_data_processor()
        if saved_data:
            st.session_state.data_processor = saved_data

    # Load saved config
    saved_config = load_session_config()
    if saved_config.get('selected_team') and not st.session_state.selected_team:
        st.session_state.selected_team = saved_config['selected_team']


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

    if uploaded_files:
        # Process data
        if st.session_state.data_processor is None:
            with st.spinner("Processing data..."):
                try:
                    st.session_state.data_processor = DataProcessor(uploaded_files)
                    save_data_processor(st.session_state.data_processor)  # Save immediately
                    st.sidebar.success(f"✅ {len(uploaded_files)} files loaded & saved")
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
                    return

        # Team selection
        if st.session_state.data_processor:
            teams = st.session_state.data_processor.get_teams()
            selected_team = st.sidebar.selectbox(
                "Select Team",
                teams,
                index=teams.index(st.session_state.selected_team) if st.session_state.selected_team in teams else 0
            )

            if selected_team != st.session_state.selected_team:
                st.session_state.selected_team = selected_team
                save_session_config()  # Save team selection

            # Show basic info
            show_basic_dashboard()

    elif st.session_state.data_processor:
        # Show dashboard even without new upload if data exists
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

            show_basic_dashboard()
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
    """)


def show_basic_dashboard():
    st.title(f"🏠 Dashboard - {st.session_state.selected_team}")

    if not st.session_state.data_processor:
        st.warning("Load data first!")
        return

    team_players = st.session_state.data_processor.get_team_players(st.session_state.selected_team)

    if not team_players:
        st.warning(f"No players found for {st.session_state.selected_team}")
        return

    # Team statistics
    total_players = sum(len(df) for df in team_players.values())
    ages = []

    for df in team_players.values():
        if 'Idade' in df.columns:
            ages.extend(df['Idade'].dropna().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Players", total_players)
    with col2:
        if ages:
            st.metric("📊 Average Age", f"{sum(ages) / len(ages):.1f}")
    with col3:
        st.metric("🏆 Positions", len(team_players))

    # Show players by position
    for pos, df in team_players.items():
        with st.expander(f"⚽ {pos} ({len(df)} players)"):
            # Display player names and basic info
            for _, player in df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{player['Jogador']}**")
                with col2:
                    st.write(f"Age: {player.get('Idade', 'N/A')}")
                with col3:
                    st.write(f"Minutes: {player.get('Minutos jogados', 0)}")



if __name__ == "__main__":
    main()