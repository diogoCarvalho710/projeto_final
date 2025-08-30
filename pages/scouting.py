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

    # Initialize ranking system safely
    try:
        if 'ranking_system' not in st.session_state or st.session_state.ranking_system is None:
            st.session_state.ranking_system = RankingSystem(st.session_state.data_processor)

        ranking_system = st.session_state.ranking_system
        current_team = st.session_state.selected_team

    except Exception as e:
        st.error(f"Error initializing ranking system: {str(e)}")
        return

    # Page header
    st.title("🔍 Scouting System")
    st.markdown(f"**Current Team:** {current_team} | Find players across Liga 2")

    # Main layout - 3 columns
    filter_col, results_col, comparison_col = st.columns([1, 2, 1])

    with filter_col:
        show_filters_panel(ranking_system, current_team)

    with results_col:
        show_results_panel(ranking_system, current_team)

    with comparison_col:
        show_comparison_panel(ranking_system)


def show_filters_panel(ranking_system: RankingSystem, current_team: str):
    """Show filters panel"""

    st.subheader("🎯 Filters")

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

    # Performance filters (if position selected)
    performance_filters = {}
    if selected_position:
        with st.expander("📊 Performance Filters"):
            performance_filters = ScoutingFilters.show_performance_filters(selected_position, "scout_perf")

    st.divider()

    # Clear filters button
    if st.button("🗑️ Clear All Filters", key="clear_scout_filters"):
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


def show_results_panel(ranking_system: RankingSystem, current_team: str):
    """Show results panel with rankings"""

    st.subheader("🏆 Results")

    # Get filters
    filters = st.session_state.get('scout_filters', {})
    position = filters.get('position')

    if not position:
        st.info("👆 Select a position to see rankings")
        return

    # Show ranking description
    ranking_info = ranking_system.get_ranking_description(position)
    if ranking_info:
        with st.expander(f"ℹ️ {ranking_info['name']} - How it works"):
            st.markdown(f"**{ranking_info['description']}**")
            st.markdown("**Metrics and Weights:**")
            for metric, weight, direction in ranking_info['metrics']:
                weight_pct = abs(weight) * 100
                direction_text = "↑ Higher is better" if weight > 0 else "↓ Lower is better"
                st.markdown(f"• **{metric}**: {weight_pct:.0f}% {direction_text}")

    # Apply filters and get results
    try:
        # Get base data for position
        df = st.session_state.data_processor.dataframes[position].copy()

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

        # Apply team exclusion
        if exclude_teams and 'Time' in filtered_df.columns:
            filtered_df = filtered_df[~filtered_df['Time'].isin(exclude_teams)]

        # Apply search filter
        if filters.get('search'):
            search_mask = filtered_df['Jogador'].str.contains(filters['search'], case=False, na=False)
            filtered_df = filtered_df[search_mask]

        # Apply performance filters
        performance_filters = filters.get('performance', {})
        if performance_filters:
            filtered_df = FilterValidator.validate_performance_filters(
                filtered_df, performance_filters, position
            )

        if filtered_df.empty:
            st.warning("🚫 No players found matching the selected filters")
            return

        # Calculate rankings
        ranked_df = ranking_system.calculate_position_score(filtered_df, position)

        # Show results count
        st.success(f"✅ Found {len(ranked_df)} players matching filters")

        # Results tabs
        results_tab1, results_tab2, results_tab3 = st.tabs(["🏆 Rankings", "📊 Charts", "📈 Analysis"])

        with results_tab1:
            show_rankings_tab(ranked_df, ranking_info, position)

        with results_tab2:
            show_charts_tab(ranked_df, ranking_info, position)

        with results_tab3:
            show_analysis_tab(ranked_df, position)

    except Exception as e:
        st.error(f"Error processing results: {str(e)}")


def show_rankings_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show rankings table"""

    if ranked_df.empty:
        return

    # Show rankings table
    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]
    ScoutingCharts.show_rankings_table(
        ranked_df,
        ranking_metrics,
        show_percentiles=True,
        max_rows=50
    )

    # Add players to comparison
    if st.session_state.get('comparison_players') is None:
        st.session_state.comparison_players = []

    st.markdown("---")
    st.markdown("**🔄 Add to Comparison:**")

    # Show top players for quick selection
    top_players = ranked_df.head(10)['Jogador'].tolist()

    cols = st.columns(min(5, len(top_players)))
    for i, player in enumerate(top_players[:5]):
        with cols[i]:
            if st.button(f"➕ {player}", key=f"add_{position}_{player}_{i}"):
                add_to_comparison(player, position)

    # Player selector for all players
    with st.expander("🔍 Add Any Player to Comparison"):
        all_players = ranked_df['Jogador'].tolist()
        selected_player = st.selectbox(
            "Select player",
            all_players,
            key=f"select_any_{position}"
        )
        if st.button("➕ Add Selected Player", key=f"add_selected_{position}"):
            add_to_comparison(selected_player, position)


def show_charts_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show charts and visualizations"""

    if ranked_df.empty:
        return

    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]

    # Chart selection
    chart_type = st.selectbox(
        "📊 Select Chart Type",
        ["Scatter Plot", "Distribution", "Trends by Age"],
        key=f"chart_type_{position}"
    )

    if chart_type == "Scatter Plot":
        col1, col2 = st.columns(2)
        with col1:
            x_metric = st.selectbox("X-axis metric", ranking_metrics, key=f"x_metric_{position}")
        with col2:
            y_metric = st.selectbox("Y-axis metric", ranking_metrics, key=f"y_metric_{position}",
                                    index=1 if len(ranking_metrics) > 1 else 0)

        if x_metric and y_metric:
            # Highlight comparison players if any
            highlight_players = []
            if st.session_state.get('comparison_players'):
                highlight_players = [p['name'] for p in st.session_state.comparison_players]

            ScoutingCharts.show_scatter_plot(
                ranked_df, x_metric, y_metric,
                color_by='Time',
                highlight_players=highlight_players
            )

    elif chart_type == "Distribution":
        selected_metric = st.selectbox("Select metric", ranking_metrics, key=f"dist_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_distribution_plot(ranked_df, selected_metric)

    elif chart_type == "Trends by Age":
        selected_metric = st.selectbox("Select metric", ranking_metrics, key=f"trend_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_metric_trends(ranked_df, selected_metric, 'Idade')


def show_analysis_tab(ranked_df: pd.DataFrame, position: str):
    """Show statistical analysis"""

    if ranked_df.empty:
        return

    st.markdown("### 📈 Statistical Summary")

    # Key stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_age = ranked_df['Idade'].mean()
        st.metric("Average Age", f"{avg_age:.1f}")

    with col2:
        avg_minutes = ranked_df['Minutos jogados'].mean()
        st.metric("Avg Minutes", f"{avg_minutes:.0f}")

    with col3:
        top_score = ranked_df['Overall_Score'].max()
        st.metric("Top Score", f"{top_score:.1f}")

    with col4:
        unique_teams = ranked_df['Time'].nunique()
        st.metric("Teams", unique_teams)

    st.markdown("---")

    # Top performers by individual metrics
    st.markdown("### 🏅 Top Performers by Metric")

    filters = st.session_state.get('scout_filters', {})
    ranking_info = st.session_state.ranking_system.get_ranking_description(position)