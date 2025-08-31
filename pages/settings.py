import streamlit as st
import pandas as pd
from typing import Dict, List
from ..src.custom_metrics_manager import CustomMetricsManager
from ..src.favorites_manager import FavoritesManager
from ..src.custom_rankings_manager import CustomRankingsManager


def show_settings():
    """Display settings page with customization features"""

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
        st.error(f"Error initializing systems: {str(e)}")
        return

    # Page header
    st.title("⚙️ Customize & Personalize Metrics")
    st.markdown(f"**Current Team:** {st.session_state.selected_team}")

    # Show status
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

    # Main tabs (removed System Settings as requested)
    main_tabs = st.tabs([
        "Custom Metrics",
        "Favorite Players",
        "Custom Rankings",
        "Export/Import"
    ])

    with main_tabs[0]:
        show_custom_metrics_section(custom_metrics_manager)

    with main_tabs[1]:
        show_favorites_section(favorites_manager)

    with main_tabs[2]:
        show_custom_rankings_section(custom_rankings_manager)

    with main_tabs[3]:
        show_export_import_section(custom_metrics_manager, favorites_manager, custom_rankings_manager)


def show_custom_metrics_section(custom_metrics_manager):
    """Show custom metrics management section"""

    st.header("🎨 Custom Metrics Creator")
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
        custom_metrics_manager.show_manage_metrics_ui_updated()  # Updated version without Test/Copy

    with metrics_tabs[2]:
        st.subheader("📋 Metric Templates")
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
    """Show favorites management section (removed suggestions tab)"""

    st.header("⭐ Favorite Players Management")
    st.markdown("Organize and track your scouting targets with advanced favorites system.")

    # Show main favorites UI (without suggestions)
    favorites_manager.show_favorites_ui_updated()


def show_custom_rankings_section(custom_rankings_manager):
    """Show custom rankings management section (with requested changes)"""

    st.header("🏆 Custom Rankings Creator")
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
            custom_rankings_manager.create_ranking_ui_updated(selected_position)  # Updated version

    with rankings_tabs[1]:
        custom_rankings_manager.show_manage_rankings_ui()

    with rankings_tabs[2]:
        st.subheader("🏆 Ranking Templates")
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
                    importance_icon = {"low": "🔵", "medium": "🟡", "high": "🟠"}.get(
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


def show_export_import_section(custom_metrics_manager, favorites_manager, custom_rankings_manager):
    """Show export/import functionality"""

    st.header("📥 Export & Import Configurations")
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
                "text/json"
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