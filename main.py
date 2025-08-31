import streamlit as st
import sys
import os
import pickle
import json
import pandas as pd
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_processor import DataProcessor
from src.team_manager import TeamManager
from src.comparison_manager import ComparisonManager
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
            'current_page': st.session_state.get('current_page', 'dashboard'),
            'comparison_players': st.session_state.get('comparison_players', [])
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
    if 'show_duplicate_analysis' not in st.session_state:
        st.session_state.show_duplicate_analysis = False
    if 'ranking_system' not in st.session_state:
        st.session_state.ranking_system = None
    if 'comparison_manager' not in st.session_state:
        st.session_state.comparison_manager = None
    if 'comparison_players' not in st.session_state:
        st.session_state.comparison_players = []

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
    if saved_config.get('comparison_players'):
        st.session_state.comparison_players = saved_config['comparison_players']


def main():
    st.set_page_config(**PAGE_CONFIG)
    initialize_session_state()

    st.sidebar.title("⚽ Football Analytics")

    # Show status if data is loaded
    if st.session_state.data_processor:
        st.sidebar.success("📊 Data loaded from previous session")

        # Show comparison status
        comparison_count = len(st.session_state.get('comparison_players', []))
        if comparison_count > 0:
            st.sidebar.info(f"⚖️ {comparison_count}/5 players in comparison")

        # Show deduplication info
        duplicate_analysis = st.session_state.data_processor.get_duplicate_analysis()
        if duplicate_analysis['potential_duplicates'] > 0:
            st.sidebar.warning(f"🔍 Found {duplicate_analysis['potential_duplicates']} potential duplicate(s)")

        # Debug button for duplicates
        if st.sidebar.button("🔍 View Duplicate Analysis"):
            st.session_state.show_duplicate_analysis = True

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

                    # Clear ranking system and comparison manager to force recreation with new data
                    st.session_state.ranking_system = None
                    st.session_state.comparison_manager = None
                    st.session_state.comparison_players = []

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
            'scouting': '🔍 Scouting & Comparison',
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

    # Show duplicate analysis if requested
    if st.session_state.get('show_duplicate_analysis') and st.session_state.data_processor:
        show_duplicate_analysis()
        st.session_state.show_duplicate_analysis = False


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
    st.session_state.ranking_system = None
    st.session_state.comparison_manager = None
    st.session_state.comparison_players = []

    st.success("🗑️ All saved data cleared!")


def show_duplicate_analysis():
    """Show duplicate analysis in a modal-like container"""

    analysis = st.session_state.data_processor.get_duplicate_analysis()

    st.markdown("---")
    st.subheader("🔍 Duplicate Player Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Players", analysis['total_players'])
    with col2:
        st.metric("Unique Names", analysis['unique_names'])
    with col3:
        st.metric("Potential Duplicates", analysis['potential_duplicates'])

    if analysis['duplicates']:
        st.markdown("### 👥 Players with Multiple Records")

        for duplicate in analysis['duplicates']:
            # Use different styling for likely duplicates
            if duplicate.get('likely_duplicate', False):
                icon = "🚨"
                status = "LIKELY DUPLICATE"
                color = "red"
            else:
                icon = "🔄"
                status = "DIFFERENT PLAYERS"
                color = "orange"

            with st.expander(f"{icon} {duplicate['name']} ({duplicate['count']} records) - {status}"):

                # Create a table of the duplicate records
                records_data = []
                for record in duplicate['records']:
                    records_data.append({
                        'Position': record['position'],
                        'Minutes': record['minutes'],
                        'Age': record['age'],
                        'Nationality': record['nationality'],
                        'Team': record['team'],
                        'Birth Date': record['birth_date']
                    })

                df_records = pd.DataFrame(records_data)
                st.dataframe(df_records, use_container_width=True)

                # Show analysis
                if duplicate.get('likely_duplicate', False):
                    # Show which one was kept (highest minutes)
                    max_minutes = duplicate['max_minutes']
                    kept_position = next(
                        r['position'] for r in duplicate['records']
                        if r['minutes'] == max_minutes
                    )

                    st.error(f"⚠️ **This appears to be the same player!** "
                             f"Should be kept in **{kept_position}** position with **{max_minutes}** minutes")
                else:
                    st.info(f"ℹ️ These appear to be different players with the same name")
    else:
        st.success("✅ No duplicate players found across different positions!")

    st.markdown("---")


def show_welcome_screen():
    st.title("⚽ Football Analytics Platform")
    st.markdown("""
    ### 🚀 Welcome to your advanced football analytics platform!

    **To get started:**
    1. 📤 Upload Wyscout CSV files in the sidebar
    2. 🏆 Select your team
    3. 📊 Explore the available features

    **💾 Auto-Save Feature:**
    - Your data is automatically saved after upload
    - Team selection and comparisons are remembered
    - No need to re-upload after refresh!

    **🔧 Available Features:**
    - 🏠 **Team Dashboard**: Squad overview with starters/subs
    - 👤 **Player Profiles**: Detailed individual analysis with radar charts
    - 🔍 **Advanced Scouting**: Player search, rankings, and comparison system ✨ **ENHANCED!**
    - 📊 **Rankings**: Performance rankings by position  
    - ⚙️ **Settings**: Personalization and configuration

    **🆕 Phase 4 - Scouting System:**
    - ✅ **Advanced filtering** by age, nationality, performance metrics
    - ✅ **Dynamic rankings** with percentiles and weighted scoring
    - ✅ **Multi-player comparison** with radar charts and statistics
    - ✅ **Export functionality** to CSV
    - ✅ **Similar player suggestions** and batch adding
    - ✅ **Interactive charts** with highlighted comparison players
    """)


def show_team_dashboard_page():
    """Show team dashboard page"""
    from pages.team_dashboard import show_team_dashboard
    show_team_dashboard()


def show_player_profile_page():
    """Show player profile page"""
    from pages.player_profile import show_player_profile
    show_player_profile()


def show_scouting_page():
    """Show enhanced scouting page"""
    try:
        from pages.scouting import show_scouting
        show_scouting()
    except Exception as e:
        st.error(f"Error loading scouting page: {str(e)}")
        st.markdown("""
        **Possible causes:**
        - Missing files: `src/ranking_system.py`, `src/comparison_manager.py`, `components/filters.py`, `components/charts.py`
        - Data not loaded properly
        - Import errors

        **Try:**
        1. Check if all files exist
        2. Clear saved data and re-upload CSVs
        3. Restart the application
        """)

        # Debug info
        with st.expander("🔍 Debug Info"):
            st.write("Session State Keys:", list(st.session_state.keys()))
            st.write("Data Processor:", st.session_state.get('data_processor') is not None)
            st.write("Selected Team:", st.session_state.get('selected_team'))
            if st.session_state.get('data_processor'):
                st.write("Available Positions:", list(st.session_state.data_processor.dataframes.keys()))


def show_rankings_page():
    """Show rankings page (placeholder)"""
    st.title("📊 Advanced Rankings System")
    st.info("🚧 Phase 5: Custom rankings creator will be implemented next!")

    st.markdown("""
    **✅ Currently Available (Phase 4):**
    - 🔍 **Pre-defined rankings** in the Scouting page
    - 🏆 **Position-specific scoring** with percentiles
    - ⚖️ **Weighted metrics** by position
    - 📊 **Real-time filtering and comparison**

    **Coming in Phase 5:**
    - 🎯 Custom ranking creation tool
    - 📈 Adjustable weights and scoring systems
    - ⚖️ Save/load custom ranking templates
    - 💾 Export custom rankings
    - 🎨 Advanced visualization options
    """)


def show_settings_page():
    """Show complete Phase 5 settings page"""
    try:
        from pages.settings import show_settings
        show_settings()
    except Exception as e:
        st.error(f"Settings page error: {str(e)}")

        # Fallback to debug version
        st.warning("🔧 Falling back to debug mode...")
        try:
            from pages.settings_debug import show_settings as show_settings_debug
            show_settings_debug()
        except Exception as debug_error:
            st.error(f"Even debug failed: {str(debug_error)}")

        # Show detailed error for debugging
        with st.expander("🔍 Error Details"):
            import traceback
            st.code(traceback.format_exc())


def show_rankings_page():
    """Show enhanced rankings page with Phase 5 features"""
    st.title("📊 Advanced Rankings System")

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    # Initialize Phase 5 managers if needed
    try:
        if 'custom_rankings_manager' not in st.session_state:
            from src.custom_rankings_manager import CustomRankingsManager
            st.session_state.custom_rankings_manager = CustomRankingsManager(
                st.session_state.data_processor,
                st.session_state.ranking_system
            )

        custom_rankings_manager = st.session_state.custom_rankings_manager
        custom_rankings = custom_rankings_manager.load_custom_rankings()

        if custom_rankings:
            st.success(f"✅ {len(custom_rankings)} custom rankings available!")

            # Show custom rankings
            for ranking_id, ranking_config in custom_rankings.items():
                with st.expander(f"🏆 {ranking_config['name']} ({ranking_config['position']})", expanded=False):
                    st.markdown(f"**Description:** {ranking_config.get('description', 'No description')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"▶️ Run Ranking", key=f"run_{ranking_id}"):
                            # Calculate and display ranking
                            position = ranking_config['position']
                            if position in st.session_state.data_processor.dataframes:
                                df = st.session_state.data_processor.dataframes[position]
                                ranked_df = custom_rankings_manager.calculate_custom_ranking(df, ranking_config)

                                if not ranked_df.empty:
                                    st.subheader(f"🏆 {ranking_config['name']} Results")

                                    # Show top 20
                                    display_df = ranked_df.head(20)[
                                        ['Jogador', 'Time', 'Idade', 'Minutos jogados', 'Custom_Ranking_Score']].copy()
                                    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
                                    display_df.columns = ['Rank', 'Player', 'Team', 'Age', 'Minutes', 'Score']

                                    st.dataframe(display_df, use_container_width=True)

                                    # Export option
                                    csv_data = display_df.to_csv(index=False)
                                    st.download_button(
                                        "📥 Export Results",
                                        csv_data,
                                        f"{ranking_config['name']}_results.csv",
                                        "text/csv"
                                    )

                    with col2:
                        st.metric("Metrics Used", len(ranking_config.get('metrics', [])))
        else:
            st.info("🚧 No custom rankings yet. Create them in the Settings page!")

    except Exception as e:
        st.error(f"Custom rankings error: {str(e)}")

    # Show standard rankings (Phase 4)
    st.markdown("---")
    st.markdown("### 📊 Standard Position Rankings")
    st.info("These are available in the Scouting page. Create custom rankings in Settings for more advanced features!")

    # Quick access to scouting
    if st.button("🔍 Go to Advanced Scouting"):
        st.session_state.current_page = 'scouting'
        st.rerun()


# Update the main function to ensure Phase 5 compatibility
def main():
    st.set_page_config(**PAGE_CONFIG)
    initialize_session_state()

    st.sidebar.title("⚽ Football Analytics")

    # Show enhanced status if data is loaded
    if st.session_state.data_processor:
        st.sidebar.success("📊 Data loaded from previous session")

        # Show comparison status
        comparison_count = len(st.session_state.get('comparison_players', []))
        if comparison_count > 0:
            st.sidebar.info(f"⚖️ {comparison_count}/5 players in comparison")

        # Show Phase 5 status
        phase5_status = []

        # Check custom metrics
        try:
            from src.custom_metrics_manager import CustomMetricsManager
            if 'custom_metrics_manager' not in st.session_state:
                st.session_state.custom_metrics_manager = CustomMetricsManager(st.session_state.data_processor)
            custom_metrics = st.session_state.custom_metrics_manager.load_custom_metrics()
            if custom_metrics:
                phase5_status.append(f"🎨 {len(custom_metrics)} custom metrics")
        except:
            pass

        # Check favorites
        try:
            from src.favorites_manager import FavoritesManager
            if 'favorites_manager' not in st.session_state:
                st.session_state.favorites_manager = FavoritesManager(st.session_state.data_processor)
            favorites_count = st.session_state.favorites_manager.get_favorites_count()
            if favorites_count > 0:
                phase5_status.append(f"⭐ {favorites_count} favorites")
        except:
            pass

        # Check custom rankings
        try:
            from src.custom_rankings_manager import CustomRankingsManager
            if 'custom_rankings_manager' not in st.session_state:
                st.session_state.custom_rankings_manager = CustomRankingsManager(
                    st.session_state.data_processor,
                    st.session_state.ranking_system
                )
            custom_rankings = st.session_state.custom_rankings_manager.load_custom_rankings()
            if custom_rankings:
                phase5_status.append(f"🏆 {len(custom_rankings)} custom rankings")
        except:
            pass

        if phase5_status:
            st.sidebar.success("🚀 Phase 5 Active: " + " | ".join(phase5_status))

        # Show deduplication info
        duplicate_analysis = st.session_state.data_processor.get_duplicate_analysis()
        if duplicate_analysis['potential_duplicates'] > 0:
            st.sidebar.warning(f"🔍 Found {duplicate_analysis['potential_duplicates']} potential duplicate(s)")

        # Debug button for duplicates
        if st.sidebar.button("🔍 View Duplicate Analysis"):
            st.session_state.show_duplicate_analysis = True

        # Clear data option
        if st.sidebar.button("🗑️ Clear Saved Data"):
            clear_saved_data()
            st.rerun()

    # File upload (same as before)
    uploaded_files = st.sidebar.file_uploader(
        "Upload Wyscout CSVs",
        type="csv",
        accept_multiple_files=True,
        help="Select all CSV files by position"
    )

    # Process uploaded files (same as before)
    if uploaded_files:
        if st.session_state.data_processor is None:
            with st.spinner("Processing data..."):
                try:
                    st.session_state.data_processor = DataProcessor(uploaded_files)
                    save_data_processor(st.session_state.data_processor)
                    st.sidebar.success(f"✅ {len(uploaded_files)} files loaded & saved")

                    # Clear systems to force recreation with new data
                    for key in ['ranking_system', 'comparison_manager', 'comparison_players',
                                'custom_metrics_manager', 'favorites_manager', 'custom_rankings_manager']:
                        if key in st.session_state:
                            del st.session_state[key]

                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
                    return

    # Team selection and navigation (same as before, but updated page options)
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
            'scouting': '🔍 Scouting & Comparison',
            'rankings': '📊 Rankings & Custom Rankings',  # Updated
            'settings': '⚙️ Settings & Personalization'  # Updated
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
            show_rankings_page()  # Now enhanced!
        elif current_page == 'settings':
            show_settings_page()  # Now full Phase 5!

    else:
        # Enhanced welcome screen
        show_enhanced_welcome_screen()

    # Show duplicate analysis if requested
    if st.session_state.get('show_duplicate_analysis') and st.session_state.data_processor:
        show_duplicate_analysis()
        st.session_state.show_duplicate_analysis = False


def show_enhanced_welcome_screen():
    """Enhanced welcome screen with Phase 5 info"""
    st.title("⚽ Football Analytics Platform")
    st.markdown("""
    ### 🚀 Welcome to your advanced football analytics platform!

    **To get started:**
    1. 📤 Upload Wyscout CSV files in the sidebar
    2. 🏆 Select your team
    3. 📊 Explore the available features

    **💾 Auto-Save Feature:**
    - Your data is automatically saved after upload
    - Team selection and comparisons are remembered
    - Custom metrics, favorites, and rankings persist
    - No need to re-upload after refresh!
    """)

    # Phase overview with current status
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🔧 Available Features:**
        - 🏠 **Team Dashboard**: Squad overview with starters/subs
        - 👤 **Player Profiles**: Detailed individual analysis with radar charts
        - 🔍 **Advanced Scouting**: Player search, rankings, and comparison system
        - 📊 **Rankings**: Performance rankings by position + **Custom Rankings!** ✨
        - ⚙️ **Settings**: Complete personalization system ✨
        """)

    with col2:
        st.success("🎉 **PHASE 5 COMPLETE!**")
        st.markdown("""
        **✨ NEW Phase 5 Features:**
        - 🎨 **Custom Metrics**: Create personalized performance indicators
        - ⭐ **Advanced Favorites**: Comprehensive player tracking system  
        - 🏆 **Custom Rankings**: Sophisticated ranking systems
        - 📊 **Personalized Radar Charts**: Your own metric combinations
        - 💾 **Export/Import**: Complete configuration management
        """)

    st.markdown("---")
    st.info(
        "🚀 **Ready for Phase 6**: ML-powered recommendations, performance prediction, and advanced similarity analysis coming next!")


if __name__ == "__main__":
    main()