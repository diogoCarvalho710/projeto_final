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
        show_filters_panel(ranking_system, current_team)

    with results_col:
        show_results_panel(ranking_system, current_team)


def show_filters_panel(ranking_system: RankingSystem, current_team: str):
    """Show filters panel"""

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

    # Performance filters (if position selected)
    performance_filters = {}
    if selected_position:
        with st.expander("📊 Advanced Performance Filters"):
            performance_filters = ScoutingFilters.show_performance_filters(
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


def show_results_panel(ranking_system: RankingSystem, current_team: str):
    """Show results panel with rankings"""

    st.subheader("🏆 Search Results")

    # Get filters
    filters = st.session_state.get('scout_filters', {})
    position = filters.get('position')

    if not position:
        st.info("👆 Select a position to see player rankings")
        return

    # Show ranking description
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
        filtered_df = get_filtered_results(ranking_system, filters, position, current_team)

        if filtered_df.empty:
            st.warning("🚫 No players found matching the selected filters")
            return

        # Calculate rankings
        ranked_df = ranking_system.calculate_position_score(filtered_df, position)

        # Show results count
        st.success(f"✅ Found **{len(ranked_df)}** players matching filters")

        # Results tabs
        results_tab1, results_tab2, results_tab3 = st.tabs(["🏆 Rankings", "📊 Charts", "⚙️ Table Settings"])

        with results_tab1:
            show_rankings_tab(ranked_df, ranking_info, position)

        with results_tab2:
            show_charts_tab(ranked_df, ranking_info, position)

        with results_tab3:
            show_table_settings_tab(ranked_df, ranking_info, position)

    except Exception as e:
        st.error(f"Error processing results: {str(e)}")


def get_filtered_results(ranking_system: RankingSystem, filters: Dict, position: str,
                         current_team: str) -> pd.DataFrame:
    """Apply all filters and return filtered dataframe"""

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

    return filtered_df


def show_rankings_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show rankings table"""

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


def show_charts_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show charts and visualizations"""

    if ranked_df.empty:
        return

    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]

    # Chart selection
    chart_type = st.selectbox(
        "📊 Select Visualization:",
        ["Scatter Plot", "Distribution Analysis", "Age Trends"],
        key=f"chart_type_{position}"
    )

    if chart_type == "Scatter Plot":
        col1, col2 = st.columns(2)
        with col1:
            x_metric = st.selectbox("X-axis:", ranking_metrics, key=f"x_metric_{position}")
        with col2:
            y_metric = st.selectbox("Y-axis:", ranking_metrics, key=f"y_metric_{position}",
                                    index=1 if len(ranking_metrics) > 1 else 0)

        if x_metric and y_metric:
            ScoutingCharts.show_scatter_plot(
                ranked_df, x_metric, y_metric,
                color_by='Time'
            )

    elif chart_type == "Distribution Analysis":
        selected_metric = st.selectbox("Select metric:", ranking_metrics, key=f"dist_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_distribution_plot(ranked_df, selected_metric)

    elif chart_type == "Age Trends":
        selected_metric = st.selectbox("Select metric:", ranking_metrics, key=f"trend_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_metric_trends(ranked_df, selected_metric, 'Idade')


def show_table_settings_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show table customization settings"""

    if ranked_df.empty:
        return

    st.subheader("📋 Customize Table Columns")

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
    selected_columns = st.multiselect(
        "Select columns to display:",
        available_columns,
        default=[col for col in available_columns if col in [metric[0] for metric in ranking_info.get('metrics', [])]],
        key=f"table_columns_{position}"
    )

    # Combine base columns with selected columns
    final_columns = base_columns + selected_columns
    final_columns = [col for col in final_columns if col in ranked_df.columns]

    # Show customized table
    display_df = ranked_df[final_columns].head(50).copy()
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

    # Make player name clickable (show as button-like format)
    st.markdown("**📊 Customized Results Table:**")
    st.caption("Click on player names to view their profile")

    # Display table with player names as clickable elements
    for idx, (_, row) in enumerate(display_df.iterrows()):
        if idx >= 20:  # Limit to first 20 for performance
            break

        with st.container():
            col1, col2, col3 = st.columns([1, 6, 1])

            with col1:
                st.markdown(f"**{idx + 1}**")

            with col2:
                # Show player info in expandable format
                with st.expander(f"👤 {row['Jogador']} - {row['Time']} (Age: {row['Idade']})", expanded=False):
                    # Show selected metrics
                    cols = st.columns(min(4, len(selected_columns)))
                    for i, col_name in enumerate(selected_columns[:4]):
                        if col_name in row.index:
                            with cols[i]:
                                st.metric(col_name,
                                          f"{row[col_name]:.2f}" if isinstance(row[col_name], float) else row[col_name])

                    if len(selected_columns) > 4:
                        st.markdown("**Additional metrics:**")
                        for col_name in selected_columns[4:]:
                            if col_name in row.index:
                                st.markdown(f"• {col_name}: {row[col_name]:.2f}" if isinstance(row[col_name],
                                                                                               float) else f"• {col_name}: {row[col_name]}")

            with col3:
                if st.button("🔍 Profile", key=f"view_profile_{idx}_{row['Jogador']}",
                             help=f"View {row['Jogador']} profile"):
                    st.session_state.selected_player = {
                        'name': row['Jogador'],
                        'position': position
                    }
                    st.session_state.show_player_profile = True
                    st.rerun()

    # Export option
    st.markdown("---")
    if st.button("📥 Export Table as CSV", key=f"export_csv_{position}"):
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv_data,
            f"{position}_scouting_results.csv",
            "text/csv"
        )


def show_analysis_tab(ranked_df: pd.DataFrame, position: str):
    """Show statistical analysis and insights"""

    if ranked_df.empty:
        return

    # Summary statistics
    st.markdown("### 📈 Statistical Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_age = ranked_df['Idade'].mean()
        st.metric("Average Age", f"{avg_age:.1f} years")

    with col2:
        avg_minutes = ranked_df['Minutos jogados'].mean()
        st.metric("Avg Minutes", f"{avg_minutes:.0f}")

    with col3:
        top_score = ranked_df['Overall_Score'].max()
        st.metric("Top Score", f"{top_score:.1f}/100")

    with col4:
        unique_teams = ranked_df['Time'].nunique()
        st.metric("Teams", unique_teams)

    # Market insights
    st.markdown("### 💰 Market Insights")

    # Value analysis if available
    if 'Valor de mercado' in ranked_df.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Value Distribution:**")
            value_counts = ranked_df['Valor de mercado'].value_counts().head(5)
            st.dataframe(value_counts)

        with col2:
            st.markdown("**⭐ Best Players by Score:**")
            if 'Overall_Score' in ranked_df.columns:
                best_players = ranked_df.nlargest(3, 'Overall_Score').head(3)
                for _, player in best_players.iterrows():
                    st.markdown(f"• **{player['Jogador']}** - Score: {player['Overall_Score']:.1f}")