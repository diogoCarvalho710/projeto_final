import streamlit as st
import pandas as pd
from typing import List, Dict
from src.ranking_system import RankingSystem
from components.filters import ScoutingFilters, FilterValidator
from components.charts import ScoutingCharts


def show_scouting():
    """Display scouting system page"""

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    # Initialize systems safely
    try:
        if 'ranking_system' not in st.session_state or st.session_state.ranking_system is None:
            st.session_state.ranking_system = RankingSystem(st.session_state.data_processor)

        ranking_system = st.session_state.ranking_system
        current_team = st.session_state.selected_team

    except Exception as e:
        st.error(f"Error initializing scouting systems: {str(e)}")
        return

    # Page header
    st.title("🔍 Advanced Scouting System")
    st.markdown(f"**Current Team:** {current_team} | Find and analyze players across Liga 2")

    # Main layout - 2 columns (removed comparison column)
    filter_col, results_col = st.columns([1, 3])

    with filter_col:
        show_filters_panel_updated(ranking_system, current_team)

    with results_col:
        show_results_panel_updated(ranking_system, current_team)


def show_filters_panel_updated(ranking_system: RankingSystem, current_team: str):
    """Show filters panel with support for custom metrics"""

    st.subheader("🎯 Search Filters")

    # Get available data safely
    try:
        positions = list(st.session_state.data_processor.dataframes.keys())
        nationalities = ranking_system.get_available_nationalities()
        teams = st.session_state.data_processor.get_teams()
    except Exception as e:
        st.error(f"Error loading filter data: {str(e)}")
        return

    # Position filter
    selected_position = ScoutingFilters.show_position_filter(positions, "scout_position")

    st.divider()

    # Age filter
    min_age, max_age = ScoutingFilters.show_age_filter("scout_age")

    st.divider()

    # Minutes filter
    min_minutes = ScoutingFilters.show_minutes_filter("scout_minutes")

    st.divider()

    # Nationality filter
    selected_nationality = ScoutingFilters.show_nationality_filter(nationalities, "scout_nationality")

    st.divider()

    # Team filters
    team_filters = ScoutingFilters.show_team_filter(teams, current_team, "scout_team")

    st.divider()

    # Search filter
    search_query = ScoutingFilters.show_search_filter("scout_search")

    st.divider()

    # Performance filters (if position selected) - UPDATED to include custom metrics
    performance_filters = {}
    if selected_position:
        with st.expander("📊 Advanced Performance Filters"):
            performance_filters = show_enhanced_performance_filters(
                selected_position, st.session_state.data_processor, current_team, "scout_perf"
            )

    st.divider()

    # Quick actions
    st.markdown("**🚀 Quick Actions:**")
    if st.button("🗑️ Clear Filters", key="clear_scout_filters", use_container_width=True):
        ScoutingFilters.clear_filters()

    # Store filters in session state
    st.session_state.scout_filters = {
        'position': selected_position,
        'min_age': min_age,
        'max_age': max_age,
        'min_minutes': min_minutes,
        'nationality': selected_nationality,
        'exclude_own_team': team_filters['exclude_own'],
        'exclude_teams': team_filters['exclude_teams'],
        'search': search_query,
        'performance': performance_filters
    }


def show_enhanced_performance_filters(position: str, data_processor, current_team: str, key: str = "performance") -> \
Dict[str, float]:
    """Show enhanced performance filters including custom metrics"""

    st.markdown("📊 **Performance Filters**")

    # Get available numeric metrics for the position
    if position not in data_processor.dataframes:
        st.info("Select a position first")
        return {}

    position_df = data_processor.dataframes[position]

    # Get basic numeric columns
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Posição', 'Temporada', 'Idade', 'Partidas jogadas',
                    'Minutos jogados', 'Position_File', 'Index', 'Contrato expira em']

    numeric_cols = []
    for col in position_df.columns:
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(position_df[col]):
            numeric_cols.append(col)

    # Add custom metrics if available
    try:
        if 'custom_metrics_manager' in st.session_state:
            custom_metrics_manager = st.session_state.custom_metrics_manager
            custom_metrics = custom_metrics_manager.get_custom_metrics_for_position(position)

            # Apply custom metrics to dataframe (temporarily for filtering)
            if custom_metrics:
                temp_df = custom_metrics_manager.apply_custom_metrics_to_df(position_df, position)

                # Add custom metric columns to available metrics
                for col in temp_df.columns:
                    if col.startswith('Custom_') and col not in numeric_cols:
                        numeric_cols.append(col)

        # Also check for custom rankings metrics
        if 'custom_rankings_manager' in st.session_state:
            custom_rankings_manager = st.session_state.custom_rankings_manager
            custom_ranking = custom_rankings_manager.get_custom_ranking_for_position(position)

            if custom_ranking:
                # Add custom ranking metrics
                for metric_info in custom_ranking['metrics']:
                    metric_name = metric_info['metric']
                    if metric_name not in numeric_cols and metric_name in position_df.columns:
                        numeric_cols.append(metric_name)
    except Exception as e:
        st.warning(f"Could not load custom metrics: {str(e)}")

    if not numeric_cols:
        st.info("No performance metrics available for this position")
        return {}

    # Sort metrics alphabetically for better UX
    numeric_cols = sorted(numeric_cols)

    # Metric selection
    st.markdown("**Select Metrics to Filter:**")
    selected_metrics = st.multiselect(
        "Choose metrics",
        numeric_cols,
        key=f"{key}_metrics_select",
        help="Select which metrics you want to filter by (includes custom metrics if available)"
    )

    if not selected_metrics:
        st.info("👆 Select metrics above to set filters")
        return {}

    filters = {}

    # For each selected metric, show threshold options
    for metric in selected_metrics:
        st.markdown(f"---")
        st.markdown(f"**🎯 {ScoutingFilters._shorten_metric_name(metric)}**")

        # Handle custom metrics differently
        if metric.startswith('Custom_'):
            # For custom metrics, we might need to calculate them first
            try:
                custom_metrics_manager = st.session_state.custom_metrics_manager
                temp_df = custom_metrics_manager.apply_custom_metrics_to_df(position_df, position)
                metric_values = pd.to_numeric(temp_df[metric], errors='coerce').dropna()
            except:
                metric_values = pd.Series([])
        else:
            # Calculate statistics for this metric
            metric_values = pd.to_numeric(position_df[metric], errors='coerce').dropna()

        if metric_values.empty:
            st.warning(f"No valid data for {metric}")
            continue

        # Overall statistics
        overall_mean = metric_values.mean()
        overall_median = metric_values.median()
        overall_max = metric_values.max()
        overall_min = metric_values.min()

        # Team-specific statistics (only for non-custom metrics)
        if not metric.startswith('Custom_'):
            team_df = position_df[position_df['Time'] == current_team]
            team_values = pd.to_numeric(team_df[metric], errors='coerce').dropna()
            team_mean = team_values.mean() if not team_values.empty else overall_mean
            team_median = team_values.median() if not team_values.empty else overall_median
        else:
            team_mean = overall_mean
            team_median = overall_median

        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Average", f"{overall_mean:.2f}")
        with col2:
            st.metric("Your Team Average", f"{team_mean:.2f}")
        with col3:
            st.metric("League Maximum", f"{overall_max:.2f}")

        # Threshold selection method
        threshold_method = st.radio(
            "Set minimum threshold:",
            [
                "Custom Value",
                "League Average",
                "Your Team Average",
                "Above League Average (+10%)",
                "Top 25% (75th percentile)",
                "Top 10% (90th percentile)"
            ],
            key=f"{key}_{metric}_method",
            horizontal=True
        )

        # Calculate threshold based on method
        if threshold_method == "Custom Value":
            threshold = st.number_input(
                f"Minimum {ScoutingFilters._shorten_metric_name(metric)}:",
                min_value=float(overall_min),
                max_value=float(overall_max),
                value=float(overall_mean),
                step=0.1,
                key=f"{key}_{metric}_custom",
                help=f"Range: {overall_min:.1f} - {overall_max:.1f}"
            )
        elif threshold_method == "League Average":
            threshold = overall_mean
            st.info(f"✅ Using league average: **{threshold:.2f}**")
        elif threshold_method == "Your Team Average":
            threshold = team_mean
            st.info(f"✅ Using your team average: **{threshold:.2f}**")
        elif threshold_method == "Above League Average (+10%)":
            threshold = overall_mean * 1.1
            st.info(f"✅ Using 110% of league average: **{threshold:.2f}**")
        elif threshold_method == "Top 25% (75th percentile)":
            threshold = metric_values.quantile(0.75)
            st.info(f"✅ Using 75th percentile: **{threshold:.2f}**")
        elif threshold_method == "Top 10% (90th percentile)":
            threshold = metric_values.quantile(0.90)
            st.info(f"✅ Using 90th percentile: **{threshold:.2f}**")

        # Store the filter
        filters[f'min_{metric}'] = threshold

    return filters


def show_results_panel_updated(ranking_system: RankingSystem, current_team: str):
    """Show results panel with updated tabs (removed Charts, renamed Table Settings)"""

    st.subheader("🏆 Search Results")

    # Get filters
    filters = st.session_state.get('scout_filters', {})
    position = filters.get('position')

    if not position:
        st.info("👆 Select a position to see player rankings")
        return

    # Show ranking description (check for custom ranking first)
    ranking_info = None
    try:
        # Check if there's an active custom ranking
        if 'custom_rankings_manager' in st.session_state:
            custom_rankings_manager = st.session_state.custom_rankings_manager
            custom_ranking = custom_rankings_manager.get_custom_ranking_for_position(position)
            if custom_ranking:
                ranking_info = {
                    'name': f"Custom: {custom_ranking['name']}",
                    'description': custom_ranking['description'],
                    'metrics': [(m['metric'], m['weight'] / 100, 1 if m['direction'] == 'positive' else -1)
                                for m in custom_ranking['metrics']],
                    'is_custom': True
                }
    except Exception as e:
        st.warning(f"Could not load custom ranking: {str(e)}")

    # Fall back to default ranking
    if not ranking_info:
        ranking_info = ranking_system.get_ranking_description(position)

    if ranking_info:
        with st.expander(f"ℹ️ {ranking_info['name']} - Ranking System"):
            st.markdown(f"**{ranking_info['description']}**")
            st.markdown("**Metrics and Weights:**")
            for metric, weight, direction in ranking_info['metrics']:
                weight_pct = abs(weight) * 100
                direction_text = "↑ Higher is better" if weight > 0 else "↓ Lower is better"
                st.markdown(f"• **{metric}**: {weight_pct:.0f}% {direction_text}")

    # Apply filters and get results
    try:
        # Get and filter data
        filtered_df = get_filtered_results_updated(ranking_system, filters, position, current_team)

        if filtered_df.empty:
            st.warning("🚫 No players found matching the selected filters")
            return

        # Calculate rankings (check for custom ranking)
        if ranking_info and ranking_info.get('is_custom'):
            # Use custom ranking
            custom_rankings_manager = st.session_state.custom_rankings_manager
            custom_ranking = custom_rankings_manager.get_custom_ranking_for_position(position)
            ranked_df = custom_rankings_manager.calculate_custom_ranking_score(filtered_df, custom_ranking)
        else:
            # Use default ranking
            ranked_df = ranking_system.calculate_position_score(filtered_df, position)

        # Show results count
        st.success(f"✅ Found **{len(ranked_df)}** players matching filters")

        # Results tabs (UPDATED - removed Charts, renamed Table Settings to Player View)
        results_tab1, results_tab2 = st.tabs(["🏆 Rankings", "👁️ Player View"])

        with results_tab1:
            show_rankings_tab_updated(ranked_df, ranking_info, position)

        with results_tab2:
            show_player_view_tab(ranked_df, ranking_info, position)

    except Exception as e:
        st.error(f"Error processing results: {str(e)}")


def get_filtered_results_updated(ranking_system: RankingSystem, filters: Dict, position: str,
                                 current_team: str) -> pd.DataFrame:
    """Apply all filters and return filtered dataframe (updated to handle custom metrics)"""

    # Get base data for position
    df = st.session_state.data_processor.dataframes[position].copy()

    # Apply custom metrics if available
    try:
        if 'custom_metrics_manager' in st.session_state:
            custom_metrics_manager = st.session_state.custom_metrics_manager
            df = custom_metrics_manager.apply_custom_metrics_to_df(df, position)
    except Exception as e:
        st.warning(f"Could not apply custom metrics: {str(e)}")

    # Apply basic filters
    exclude_teams = []
    if filters.get('exclude_own_team'):
        exclude_teams.append(current_team)
    if filters.get('exclude_teams'):
        exclude_teams.extend(filters['exclude_teams'])

    filtered_df = ranking_system.filter_players(
        position=position,
        min_age=filters.get('min_age'),
        max_age=filters.get('max_age'),
        min_minutes=filters.get('min_minutes'),
        nationality=filters.get('nationality'),
        exclude_team=None  # We'll handle this separately
    )

    # Apply custom metrics to filtered data too
    try:
        if 'custom_metrics_manager' in st.session_state:
            custom_metrics_manager = st.session_state.custom_metrics_manager
            filtered_df = custom_metrics_manager.apply_custom_metrics_to_df(filtered_df, position)
    except Exception as e:
        pass  # Continue without custom metrics

    # Apply team exclusion
    if exclude_teams and 'Time' in filtered_df.columns:
        filtered_df = filtered_df[~filtered_df['Time'].isin(exclude_teams)]

    # Apply search filter
    if filters.get('search'):
        search_mask = filtered_df['Jogador'].str.contains(filters['search'], case=False, na=False)
        filtered_df = filtered_df[search_mask]

    # Apply performance filters (including custom metrics)
    performance_filters = filters.get('performance', {})
    if performance_filters:
        filtered_df = apply_enhanced_performance_filters(filtered_df, performance_filters, position)

    return filtered_df


def apply_enhanced_performance_filters(df: pd.DataFrame, performance_filters: Dict, position: str) -> pd.DataFrame:
    """Apply performance filters including custom metrics"""

    if df.empty or not performance_filters:
        return df

    result_df = df.copy()

    for filter_name, filter_value in performance_filters.items():
        if filter_value <= 0:  # Skip zero/empty filters
            continue

        # Extract metric name from filter name (remove 'min_' prefix)
        if filter_name.startswith('min_'):
            metric_name = filter_name[4:]  # Remove 'min_' prefix

            if metric_name in result_df.columns:
                # Convert to numeric and apply filter
                numeric_values = pd.to_numeric(result_df[metric_name], errors='coerce')
                result_df = result_df[numeric_values >= filter_value]

    return result_df


def show_rankings_tab_updated(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show rankings table (updated)"""

    if ranked_df.empty:
        return

    # Show rankings table (without percentiles as requested)
    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]
    ScoutingCharts.show_rankings_table(
        ranked_df,
        ranking_metrics,
        show_percentiles=False,  # Changed to False
        max_rows=50
    )


def show_player_view_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show player view tab (renamed from Table Settings) with customizable columns"""

    if ranked_df.empty:
        return

    st.subheader("👁️ Player View - Customizable Table")

    # Get all available numeric columns
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                    'Index', 'Position_File']

    available_columns = []
    for col in ranked_df.columns:
        if col not in exclude_cols and not col.endswith('_percentile'):
            available_columns.append(col)

    # Always include basic info columns
    base_columns = ['Jogador', 'Time', 'Idade', 'Minutos jogados']

    # Let user select additional columns
    default_metrics = [col for col in available_columns if
                       col in [metric[0] for metric in ranking_info.get('metrics', [])]]

    selected_columns = st.multiselect(
        "📋 Select columns to display:",
        available_columns,
        default=default_metrics,
        key=f"table_columns_{position}",
        help="Choose which statistics to show in the table. Includes custom metrics if available."
    )

    # Show column count info
    st.info(f"📊 Showing {len(base_columns)} base columns + {len(selected_columns)} selected columns")

    # Combine base columns with selected columns
    final_columns = base_columns + selected_columns
    final_columns = [col for col in final_columns if col in ranked_df.columns]

    # Show customized table
    display_df = ranked_df[final_columns].head(50).copy()
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

    # Make table interactive with player selection
    st.markdown("**📊 Customizable Results Table:**")
    st.caption("👆 Customize columns above • 👁️ Click player names to view profiles")

    # Display table with player names as clickable elements (improved version)
    for idx, (_, row) in enumerate(display_df.iterrows()):
        if idx >= 20:  # Limit to first 20 for performance
            break

        with st.container():
            # Create expandable row for each player
            player_name = row['Jogador']
            team_name = row['Time']
            age = row['Idade']

            with st.expander(f"#{idx + 1} 👤 {player_name} - {team_name} (Age: {age})", expanded=False):
                # Show selected metrics in a grid
                if selected_columns:
                    # Create columns for metrics (max 4 per row)
                    metrics_per_row = 4
                    for i in range(0, len(selected_columns), metrics_per_row):
                        cols = st.columns(min(metrics_per_row, len(selected_columns) - i))

                        for j, col_name in enumerate(selected_columns[i:i + metrics_per_row]):
                            if col_name in row.index and j < len(cols):
                                with cols[j]:
                                    value = row[col_name]
                                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                                    st.metric(
                                        label=ScoutingFilters._shorten_metric_name(col_name),
                                        value=formatted_value
                                    )

                # Action button
                if st.button(f"👁️ View {player_name} Profile", key=f"view_profile_{idx}_{player_name}"):
                    st.session_state.selected_player = {
                        'name': player_name,
                        'position': position
                    }
                    st.session_state.show_player_profile = True
                    st.rerun()

    # Export option
    st.markdown("---")
    if st.button("📥 Export Table as CSV", key=f"export_csv_{position}"):
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            "📊 Download CSV",
            csv_data,
            f"{position}_scouting_results.csv",
            "text/csv",
            key=f"download_csv_{position}"
        )