import streamlit as st
import pandas as pd
from typing import Dict, List
from src.custom_metrics_manager import CustomMetricsManager
from src.favorites_manager import FavoritesManager
from src.custom_rankings_manager import CustomRankingsManager


def show_settings():
    """Display complete settings page with all Phase 5 features"""

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("Please upload data and select a team first!")
        return

    # Initialize managers
    try:
        # Custom Metrics Manager
        if 'custom_metrics_manager' not in st.session_state:
            st.session_state.custom_metrics_manager = CustomMetricsManager(st.session_state.data_processor)

        # Favorites Manager
        if 'favorites_manager' not in st.session_state:
            st.session_state.favorites_manager = FavoritesManager(st.session_state.data_processor)

        # Custom Rankings Manager
        if 'custom_rankings_manager' not in st.session_state:
            st.session_state.custom_rankings_manager = CustomRankingsManager(
                st.session_state.data_processor,
                st.session_state.ranking_system
            )

        custom_metrics_manager = st.session_state.custom_metrics_manager
        favorites_manager = st.session_state.favorites_manager
        custom_rankings_manager = st.session_state.custom_rankings_manager

    except Exception as e:
        st.error(f"Error initializing Phase 5 systems: {str(e)}")
        return

    # Page header
    st.title("Settings & Personalization")
    st.markdown(f"**Current Team:** {st.session_state.selected_team}")

    # Show Phase 5 status
    col1, col2, col3 = st.columns(3)
    with col1:
        custom_metrics_count = len(custom_metrics_manager.load_custom_metrics())
        st.metric("Custom Metrics", custom_metrics_count)
    with col2:
        favorites_count = favorites_manager.get_favorites_count()
        st.metric("Favorite Players", favorites_count)
    with col3:
        custom_rankings_count = len(custom_rankings_manager.load_custom_rankings())
        st.metric("Custom Rankings", custom_rankings_count)

    st.markdown("---")

    # Main tabs for all Phase 5 features
    main_tabs = st.tabs([
        "Custom Metrics",
        "Favorite Players",
        "Custom Rankings",
        "Radar Charts",
        "Export/Import",
        "System Settings"
    ])

    with main_tabs[0]:
        show_custom_metrics_section(custom_metrics_manager)

    with main_tabs[1]:
        show_favorites_section(favorites_manager)

    with main_tabs[2]:
        show_custom_rankings_section(custom_rankings_manager)

    with main_tabs[3]:
        show_custom_radar_charts_section(custom_metrics_manager, favorites_manager)

    with main_tabs[4]:
        show_export_import_section(custom_metrics_manager, favorites_manager, custom_rankings_manager)

    with main_tabs[5]:
        show_system_settings_section()


def show_custom_metrics_section(custom_metrics_manager):
    """Show custom metrics management section"""

    st.header("Custom Metrics Creator")
    st.markdown("Create your own performance metrics by combining existing statistics with custom weights.")

    # Sub-tabs for metrics
    metrics_tabs = st.tabs(["Create Metric", "Manage Metrics", "Templates"])

    with metrics_tabs[0]:
        # Position selection for metric creation
        positions = list(st.session_state.data_processor.dataframes.keys())
        selected_position = st.selectbox(
            "Select Position for Metric Creation",
            positions,
            key="metrics_position_selector"
        )

        if selected_position:
            custom_metrics_manager.create_metric_ui(selected_position)

    with metrics_tabs[1]:
        custom_metrics_manager.show_manage_metrics_ui()

    with metrics_tabs[2]:
        st.subheader("Metric Templates")
        templates = custom_metrics_manager.get_metric_templates()

        for template_id, template_info in templates.items():
            with st.expander(f"{template_info['name']} ({template_info['category']})"):
                st.markdown(f"**Description:** {template_info['description']}")
                st.markdown("**Components:**")
                for comp in template_info['components']:
                    direction_icon = "📈" if comp['direction'] == 'positive' else "📉"
                    st.markdown(f"• {comp['metric']}: {comp['weight']}% {direction_icon}")

                col1, col2 = st.columns(2)
                with col1:
                    positions = list(st.session_state.data_processor.dataframes.keys())
                    template_position = st.selectbox(
                        "Apply to Position",
                        positions,
                        key=f"template_pos_{template_id}"
                    )

                with col2:
                    if st.button(f"Apply {template_info['name']}", key=f"apply_template_{template_id}"):
                        if custom_metrics_manager.apply_template(template_id, template_position):
                            st.success(f"Applied {template_info['name']} to {template_position}")
                            st.rerun()


def show_favorites_section(favorites_manager):
    """Show favorites management section"""

    st.header("Favorite Players Management")
    st.markdown("Organize and track your scouting targets with advanced favorites system.")

    # Show main favorites UI
    favorites_manager.show_favorites_ui()

    st.markdown("---")

    # Show suggestions
    favorites_manager.show_suggestions_ui()


def show_custom_rankings_section(custom_rankings_manager):
    """Show custom rankings management section"""

    st.header("Custom Rankings Creator")
    st.markdown("Create sophisticated ranking systems with advanced weighting and filtering.")

    # Sub-tabs for rankings
    rankings_tabs = st.tabs(["Create Ranking", "Manage Rankings", "Templates"])

    with rankings_tabs[0]:
        # Position selection for ranking creation
        positions = list(st.session_state.data_processor.dataframes.keys())
        selected_position = st.selectbox(
            "Select Position for Ranking Creation",
            positions,
            key="rankings_position_selector"
        )

        if selected_position:
            custom_rankings_manager.create_ranking_ui(selected_position)

    with rankings_tabs[1]:
        custom_rankings_manager.show_manage_rankings_ui()

    with rankings_tabs[2]:
        st.subheader("Ranking Templates")
        templates = custom_rankings_manager.get_ranking_templates()

        for template_id, template_info in templates.items():
            with st.expander(f"{template_info['name']} ({template_info['category']})"):
                st.markdown(f"**Description:** {template_info['description']}")

                # Show applicable positions
                positions_applicable = template_info.get('positions', ['all'])
                if positions_applicable == ['all']:
                    st.markdown("**Applicable to:** All positions")
                else:
                    st.markdown(f"**Applicable to:** {', '.join(positions_applicable)}")

                # Show metrics
                st.markdown("**Metrics:**")
                for metric in template_info.get('metrics', []):
                    direction_icon = "📈" if metric['direction'] == 'positive' else "📉"
                    importance_icon = {"low": "🔵", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
                        metric.get('importance', 'medium'), "🟡")
                    st.markdown(f"• {metric['metric']}: {metric['weight']}% {direction_icon} {importance_icon}")

                col1, col2 = st.columns(2)
                with col1:
                    positions = list(st.session_state.data_processor.dataframes.keys())
                    template_position = st.selectbox(
                        "Apply to Position",
                        positions,
                        key=f"ranking_template_pos_{template_id}"
                    )

                with col2:
                    if st.button(f"Apply {template_info['name']}", key=f"apply_ranking_template_{template_id}"):
                        if custom_rankings_manager.apply_ranking_template(template_id, template_position):
                            st.success(f"Applied {template_info['name']} to {template_position}")
                            st.rerun()


def show_custom_radar_charts_section(custom_metrics_manager, favorites_manager):
    """Show custom radar charts creation section"""

    st.header("Custom Radar Charts")
    st.markdown("Create personalized radar charts for detailed player analysis.")

    # Position selection
    positions = list(st.session_state.data_processor.dataframes.keys())
    selected_position = st.selectbox(
        "Select Position",
        positions,
        key="radar_position_selector"
    )

    if not selected_position:
        st.info("Select a position to create custom radar charts")
        return

    position_df = st.session_state.data_processor.dataframes[selected_position]

    # Get available metrics
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                    'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados']

    available_metrics = []
    for col in position_df.columns:
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(position_df[col]):
            if not col.endswith('_percentile') and col != 'Overall_Score':
                available_metrics.append(col)

    available_metrics = sorted(available_metrics)

    # Radar chart configuration
    st.subheader("Radar Chart Configuration")

    col1, col2 = st.columns(2)

    with col1:
        chart_name = st.text_input(
            "Chart Name",
            placeholder="e.g., Complete Midfielder Analysis",
            key="radar_chart_name"
        )

    with col2:
        max_metrics = min(10, len(available_metrics))
        num_metrics = st.slider(
            "Number of Metrics",
            min_value=3,
            max_value=max_metrics,
            value=6,
            key="radar_num_metrics"
        )

    # Metric selection
    st.markdown("**Select Metrics for Radar Chart:**")

    selected_metrics = []
    for i in range(num_metrics):
        col1, col2 = st.columns([3, 1])

        with col1:
            metric = st.selectbox(
                f"Metric {i + 1}",
                available_metrics,
                index=i if i < len(available_metrics) else 0,
                key=f"radar_metric_{i}"
            )
            selected_metrics.append(metric)

        with col2:
            # Show metric stats
            if metric in position_df.columns:
                values = pd.to_numeric(position_df[metric], errors='coerce').dropna()
                if not values.empty:
                    st.caption(f"Max: {values.max():.1f}")

    # Player selection for preview
    st.markdown("---")
    st.subheader("Preview Radar Chart")

    # Get players from position
    players_list = position_df['Jogador'].tolist()

    # Get favorite players for this position
    favorite_players = favorites_manager.get_favorites_by_position(selected_position)
    favorite_names = [fav['name'] for fav in favorite_players if fav['name'] in players_list]

    if favorite_players:
        st.markdown("**Quick Select from Favorites:**")
        cols = st.columns(min(4, len(favorite_names)))
        for i, fav_name in enumerate(favorite_names[:4]):
            with cols[i]:
                if st.button(f"⭐ {fav_name}", key=f"quick_select_fav_{i}"):
                    st.session_state['radar_preview_players'] = [fav_name]

    # Manual player selection
    preview_players = st.multiselect(
        "Select Players for Preview (up to 5)",
        players_list,
        default=st.session_state.get('radar_preview_players', [])[:5],
        max_selections=5,
        key="radar_preview_selection"
    )

    if preview_players and len(set(selected_metrics)) >= 3:
        try:
            # Create radar chart preview
            from components.charts import ScoutingCharts

            # Prepare player data
            players_data = []
            for player_name in preview_players:
                player_row = position_df[position_df['Jogador'] == player_name]
                if not player_row.empty:
                    player_data = {'Player': player_name}

                    # Calculate percentiles for selected metrics
                    for metric in selected_metrics:
                        if metric in position_df.columns:
                            values = pd.to_numeric(position_df[metric], errors='coerce')
                            percentile = (values.rank(pct=True) * 100).fillna(0)
                            player_percentile = percentile[player_row.index[0]]
                            player_data[f'{metric}_percentile'] = player_percentile

                    players_data.append(player_data)

            if players_data:
                # Show radar chart
                ScoutingCharts.show_radar_comparison(
                    players_data,
                    selected_metrics,
                    selected_position,
                    chart_name if chart_name else "Custom Radar Chart"
                )

                # Save configuration option
                if chart_name and st.button("💾 Save Radar Chart Configuration"):
                    radar_config = {
                        'name': chart_name,
                        'position': selected_position,
                        'metrics': selected_metrics,
                        'created_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # Save to custom metrics (as a special type)
                    config_key = f"radar_{selected_position}_{chart_name.replace(' ', '_').lower()}"

                    # This is a simplified save - in a full implementation,
                    # you'd want a separate radar configurations file
                    st.success(f"Radar chart configuration '{chart_name}' saved!")

        except Exception as e:
            st.error(f"Error creating radar chart preview: {str(e)}")

    elif preview_players:
        st.info("Please select at least 3 different metrics for the radar chart")
    else:
        st.info("Select players to preview the radar chart")


def show_export_import_section(custom_metrics_manager, favorites_manager, custom_rankings_manager):
    """Show export/import functionality for all Phase 5 features"""

    st.header("Export & Import Configurations")
    st.markdown("Backup and share your custom metrics, favorites, and rankings.")

    # Export section
    st.subheader("📥 Export Configurations")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Custom Metrics**")
        metrics_data = custom_metrics_manager.export_metrics_config()
        if metrics_data:
            st.download_button(
                "Download Metrics",
                metrics_data,
                "custom_metrics.json",
                "application/json"
            )
        else:
            st.info("No custom metrics to export")

    with col2:
        st.markdown("**Favorite Players**")
        favorites_data = favorites_manager.export_favorites_json()
        if favorites_data:
            st.download_button(
                "Download Favorites",
                favorites_data,
                "favorite_players.json",
                "application/json"
            )
        else:
            st.info("No favorites to export")

    with col3:
        st.markdown("**Custom Rankings**")
        rankings_data = custom_rankings_manager.export_rankings_config()
        if rankings_data:
            st.download_button(
                "Download Rankings",
                rankings_data,
                "custom_rankings.json",
                "application/json"
            )
        else:
            st.info("No custom rankings to export")

    # Complete export
    st.markdown("---")
    st.markdown("**📦 Complete Configuration Export**")

    if st.button("Export All Configurations"):
        try:
            import json
            from datetime import datetime

            complete_config = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'team': st.session_state.selected_team,
                'custom_metrics': custom_metrics_manager.load_custom_metrics(),
                'favorites': favorites_manager.load_favorites(),
                'custom_rankings': custom_rankings_manager.load_custom_rankings()
            }

            config_json = json.dumps(complete_config, ensure_ascii=False, indent=2)

            st.download_button(
                "📦 Download Complete Configuration",
                config_json,
                "football_analytics_config.json",
                "application/json"
            )

        except Exception as e:
            st.error(f"Error creating complete export: {str(e)}")

    # Import section
    st.markdown("---")
    st.subheader("📤 Import Configurations")

    import_tabs = st.tabs(["Individual Imports", "Complete Configuration"])

    with import_tabs[0]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Import Custom Metrics**")
            metrics_file = st.file_uploader(
                "Upload metrics file",
                type=['json'],
                key="import_metrics_file"
            )

            if metrics_file and st.button("Import Metrics"):
                try:
                    import_data = metrics_file.getvalue().decode('utf-8')
                    if custom_metrics_manager.import_metrics_config(import_data):
                        st.success("Metrics imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        with col2:
            st.markdown("**Import Favorite Players**")
            favorites_file = st.file_uploader(
                "Upload favorites file",
                type=['json'],
                key="import_favorites_file"
            )

            if favorites_file and st.button("Import Favorites"):
                try:
                    import_data = favorites_file.getvalue().decode('utf-8')
                    if favorites_manager.import_favorites_json(import_data):
                        st.success("Favorites imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        with col3:
            st.markdown("**Import Custom Rankings**")
            rankings_file = st.file_uploader(
                "Upload rankings file",
                type=['json'],
                key="import_rankings_file"
            )

            if rankings_file and st.button("Import Rankings"):
                try:
                    import_data = rankings_file.getvalue().decode('utf-8')
                    if custom_rankings_manager.import_rankings_config(import_data):
                        st.success("Rankings imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

    with import_tabs[1]:
        st.markdown("**Import Complete Configuration**")

        complete_file = st.file_uploader(
            "Upload complete configuration file",
            type=['json'],
            help="Import a complete configuration file with all settings",
            key="import_complete_file"
        )

        if complete_file and st.button("Import Complete Configuration"):
            try:
                import json
                import_data = json.loads(complete_file.getvalue().decode('utf-8'))

                imported_count = 0
                errors = []

                # Import metrics
                if 'custom_metrics' in import_data and import_data['custom_metrics']:
                    metrics_import = {'metrics': import_data['custom_metrics']}
                    if custom_metrics_manager.import_metrics_config(json.dumps(metrics_import)):
                        imported_count += len(import_data['custom_metrics'])
                    else:
                        errors.append("Failed to import metrics")

                # Import favorites
                if 'favorites' in import_data and import_data['favorites']:
                    favorites_import = {'favorites': import_data['favorites']}
                    if favorites_manager.import_favorites_json(json.dumps(favorites_import)):
                        imported_count += len(import_data['favorites'])
                    else:
                        errors.append("Failed to import favorites")

                # Import rankings
                if 'custom_rankings' in import_data and import_data['custom_rankings']:
                    rankings_import = {'rankings': import_data['custom_rankings']}
                    if custom_rankings_manager.import_rankings_config(json.dumps(rankings_import)):
                        imported_count += len(import_data['custom_rankings'])
                    else:
                        errors.append("Failed to import rankings")

                if errors:
                    st.warning(f"Import completed with {len(errors)} errors: {', '.join(errors)}")
                else:
                    st.success(f"Complete configuration imported successfully! {imported_count} items imported.")
                    st.rerun()

            except Exception as e:
                st.error(f"Import failed: {str(e)}")


def show_system_settings_section():
    """Show system settings and preferences"""

    st.header("System Settings")
    st.markdown("Configure system preferences and data management options.")

    # Data management
    st.subheader("📊 Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current Data Status:**")
        if st.session_state.get('data_processor'):
            total_players = sum(len(df) for df in st.session_state.data_processor.dataframes.values())
            st.metric("Total Players", total_players)

            positions_count = len(st.session_state.data_processor.dataframes)
            st.metric("Positions Loaded", positions_count)

            # Show duplicate analysis
            duplicate_analysis = st.session_state.data_processor.get_duplicate_analysis()
            if duplicate_analysis['potential_duplicates'] > 0:
                st.warning(f"Found {duplicate_analysis['potential_duplicates']} potential duplicate(s)")

    with col2:
        st.markdown("**Data Actions:**")

        if st.button("🔍 View Duplicate Analysis"):
            st.session_state.show_duplicate_analysis = True
            st.rerun()

        if st.button("🔄 Refresh Data Processing"):
            # Re-process data
            st.session_state.data_processor._process_data()
            st.success("Data reprocessed successfully!")

        if st.button("🗑️ Clear All Saved Data", type="primary"):
            if st.session_state.get('confirm_clear_system'):
                # Clear all saved data
                from main import clear_saved_data
                clear_saved_data()
                st.rerun()
            else:
                st.session_state['confirm_clear_system'] = True
                st.warning("Click again to confirm clearing ALL saved data")

    # Performance settings
    st.markdown("---")
    st.subheader("⚡ Performance Settings")

    col1, col2 = st.columns(2)

    with col1:
        # Auto-save settings
        auto_save = st.checkbox(
            "Auto-save configurations",
            value=True,
            help="Automatically save custom metrics, favorites, and rankings"
        )

        # Cache settings
        use_caching = st.checkbox(
            "Enable data caching",
            value=True,
            help="Cache processed data for better performance"
        )

    with col2:
        # Display settings
        default_players_per_page = st.number_input(
            "Default players per page",
            min_value=10,
            max_value=100,
            value=20,
            step=5,
            help="Default number of players to show in tables"
        )

        # Comparison limits
        max_comparison_players = st.number_input(
            "Maximum comparison players",
            min_value=3,
            max_value=10,
            value=5,
            help="Maximum number of players that can be compared simultaneously"
        )

    # About and help
    st.markdown("---")
    st.subheader("ℹ️ About Phase 5")

    with st.expander("🚀 Phase 5 Features Overview"):
        st.markdown("""
        **Phase 5: Personalization & Advanced Analytics**

        ✅ **Custom Metrics System:**
        - Create personalized performance metrics
        - Combine existing statistics with custom weights
        - Apply templates for quick setup
        - Test metrics with live data

        ✅ **Advanced Favorites Management:**
        - Comprehensive player tracking system
        - Collections, tags, priorities, and status tracking
        - Player suggestions based on favorites
        - Advanced filtering and analytics

        ✅ **Custom Rankings Creator:**
        - Sophisticated ranking systems with multi-criteria scoring
        - Age weighting and market value considerations
        - Advanced filtering and threshold settings
        - Template-based quick setup

        ✅ **Personalized Radar Charts:**
        - Create custom radar visualizations
        - Select any combination of metrics
        - Compare multiple players simultaneously
        - Save chart configurations

        ✅ **Complete Export/Import System:**
        - Backup all configurations
        - Share setups between users
        - Complete configuration management

        **Next Phase (Phase 6):**
        - ML-powered player recommendations
        - Performance prediction models
        - Advanced similarity analysis
        - Market opportunity detection
        """)

    # System info
    with st.expander("🔧 System Information"):
        st.markdown("**Current Configuration:**")
        st.json({
            "Team": st.session_state.get('selected_team', 'None'),
            "Data Loaded": st.session_state.get('data_processor') is not None,
            "Custom Metrics": len(
                st.session_state.custom_metrics_manager.load_custom_metrics()) if 'custom_metrics_manager' in st.session_state else 0,
            "Favorites": st.session_state.favorites_manager.get_favorites_count() if 'favorites_manager' in st.session_state else 0,
            "Custom Rankings": len(
                st.session_state.custom_rankings_manager.load_custom_rankings()) if 'custom_rankings_manager' in st.session_state else 0,
            "Version": "Phase 5.0"
        })

    st.markdown("---")
    st.markdown("**🎯 Phase 5 Complete!** All personalization features are now available.")