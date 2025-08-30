import streamlit as st
import pandas as pd
from typing import List, Dict
from src.ranking_system import RankingSystem
from src.comparison_manager import ComparisonManager
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

        if 'comparison_manager' not in st.session_state or st.session_state.comparison_manager is None:
            st.session_state.comparison_manager = ComparisonManager(
                st.session_state.data_processor,
                st.session_state.ranking_system
            )

        ranking_system = st.session_state.ranking_system
        comparison_manager = st.session_state.comparison_manager
        current_team = st.session_state.selected_team

    except Exception as e:
        st.error(f"Error initializing scouting systems: {str(e)}")
        return

    # Page header
    st.title("🔍 Advanced Scouting System")

    # Show comparison summary if players selected
    comparison_count = comparison_manager.get_comparison_count()
    if comparison_count > 0:
        st.info(f"📊 **{comparison_count}/5 players** in comparison - Use right panel to analyze")

    st.markdown(f"**Current Team:** {current_team} | Find and compare players across Liga 2")

    # Main layout - 3 columns
    filter_col, results_col, comparison_col = st.columns([1, 2, 1])

    with filter_col:
        show_filters_panel(ranking_system, current_team)

    with results_col:
        show_results_panel(ranking_system, comparison_manager, current_team)

    with comparison_col:
        show_comparison_panel(comparison_manager)


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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Filters", key="clear_scout_filters", use_container_width=True):
            ScoutingFilters.clear_filters()

    with col2:
        if st.button("⚡ Reset All", key="reset_all", use_container_width=True):
            ScoutingFilters.clear_filters()
            st.session_state.comparison_players = []
            st.rerun()

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


def show_results_panel(ranking_system: RankingSystem, comparison_manager: ComparisonManager, current_team: str):
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
        results_tab1, results_tab2, results_tab3 = st.tabs(["🏆 Rankings", "📊 Charts", "📈 Analysis"])

        with results_tab1:
            show_rankings_tab(ranked_df, ranking_info, position, comparison_manager)

        with results_tab2:
            show_charts_tab(ranked_df, ranking_info, position)

        with results_tab3:
            show_analysis_tab(ranked_df, position, comparison_manager)

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


def show_rankings_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str,
                      comparison_manager: ComparisonManager):
    """Show rankings table with comparison options"""

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

    st.markdown("---")
    st.markdown("**🔄 Add Players to Comparison:**")

    # Quick add top players
    top_players = ranked_df.head(5)['Jogador'].tolist()

    if len(top_players) > 0:
        st.markdown("**⚡ Quick Add Top Players:**")
        cols = st.columns(min(3, len(top_players)))
        for i, player in enumerate(top_players[:3]):
            with cols[i]:
                if st.button(f"➕ {player}", key=f"quick_add_{position}_{player}_{i}", use_container_width=True):
                    comparison_manager.add_player(player, position, ranked_df)
                    st.rerun()

    # Advanced add options
    with st.expander("🔍 Advanced Add Options"):

        # Select any player
        all_players = ranked_df['Jogador'].tolist()
        selected_player = st.selectbox(
            "Select any player:",
            all_players,
            key=f"select_any_{position}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Selected", key=f"add_selected_{position}"):
                comparison_manager.add_player(selected_player, position, ranked_df)
                st.rerun()

        with col2:
            if st.button("🎯 Add + Similar", key=f"add_similar_{position}"):
                comparison_manager.add_player(selected_player, position, ranked_df)
                comparison_manager.batch_add_similar_players(selected_player, position, 2)
                st.rerun()


def show_charts_tab(ranked_df: pd.DataFrame, ranking_info: Dict, position: str):
    """Show charts and visualizations"""

    if ranked_df.empty:
        return

    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]

    # Chart selection
    chart_type = st.selectbox(
        "📊 Select Visualization:",
        ["Scatter Plot", "Distribution Analysis", "Age Trends", "Performance Heatmap"],
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
            # Highlight comparison players
            highlight_players = []
            if st.session_state.get('comparison_players'):
                highlight_players = [p['name'] for p in st.session_state.comparison_players]

            ScoutingCharts.show_scatter_plot(
                ranked_df, x_metric, y_metric,
                color_by='Time',
                highlight_players=highlight_players
            )

    elif chart_type == "Distribution Analysis":
        selected_metric = st.selectbox("Select metric:", ranking_metrics, key=f"dist_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_distribution_plot(ranked_df, selected_metric)

    elif chart_type == "Age Trends":
        selected_metric = st.selectbox("Select metric:", ranking_metrics, key=f"trend_metric_{position}")
        if selected_metric:
            ScoutingCharts.show_metric_trends(ranked_df, selected_metric, 'Idade')

    elif chart_type == "Performance Heatmap":
        st.info("🚧 Performance heatmap coming in next update!")


def show_analysis_tab(ranked_df: pd.DataFrame, position: str, comparison_manager: ComparisonManager):
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

    st.markdown("---")

    # Top performers analysis
    st.markdown("### 🏅 Top Performers by Metric")

    ranking_info = st.session_state.ranking_system.get_ranking_description(position)
    ranking_metrics = [metric[0] for metric in ranking_info.get('metrics', [])]

    selected_metric = st.selectbox(
        "Choose metric to analyze:",
        ranking_metrics,
        key=f"analysis_metric_{position}"
    )

    if selected_metric:
        # Show top 5 for this metric
        top_performers = ranked_df.nlargest(5, selected_metric)

        st.markdown(f"**🎯 Top 5 in {selected_metric}:**")

        for i, (_, player) in enumerate(top_performers.iterrows()):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**{i + 1}.** {player['Jogador']} ({player['Time']})")
            with col2:
                st.markdown(f"**{player[selected_metric]:.2f}**")
            with col3:
                percentile_col = f"{selected_metric}_percentile"
                if percentile_col in player.index:
                    st.markdown(f"{player[percentile_col]:.0f}th %ile")
            with col4:
                if st.button("➕", key=f"add_top_{i}_{player['Jogador']}", help="Add to comparison"):
                    comparison_manager.add_player(player['Jogador'], position, ranked_df)
                    st.rerun()

    st.markdown("---")

    # Market insights
    st.markdown("### 💰 Market Insights")

    # Value analysis if available
    if 'Valor de mercado' in ranked_df.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Value Distribution:**")
            # Simple value categories
            value_counts = ranked_df['Valor de mercado'].value_counts().head(5)
            st.dataframe(value_counts)

        with col2:
            st.markdown("**⭐ Best Value Players:**")
            # Players with high score and reasonable value
            if 'Overall_Score' in ranked_df.columns:
                best_value = ranked_df.nlargest(3, 'Overall_Score').head(3)
                for _, player in best_value.iterrows():
                    st.markdown(f"• **{player['Jogador']}** - Score: {player['Overall_Score']:.1f}")


def show_comparison_panel(comparison_manager: ComparisonManager):
    """Show enhanced comparison panel"""

    st.subheader("⚖️ Player Comparison")

    comparison_players = comparison_manager.get_comparison_players()
    comparison_count = comparison_manager.get_comparison_count()

    if comparison_count == 0:
        st.info("👆 **Add players** from search results to compare them here")

        # Show help
        with st.expander("💡 How to Use Comparison"):
            st.markdown("""
            **Getting Started:**
            1. Search for players using filters ⬅️
            2. Click ➕ buttons to add players
            3. Compare up to 5 players side-by-side

            **Comparison Features:**
            - 📊 **Radar Charts**: Visual performance comparison  
            - 📋 **Stats Table**: Detailed metrics side-by-side
            - 📈 **Percentiles**: Relative performance rankings
            - 📥 **Export**: Download comparison as CSV
            """)
        return

    # Show current players
    st.markdown(f"**Selected Players ({comparison_count}/5):**")

    for i, player_info in enumerate(comparison_players):
        col1, col2 = st.columns([4, 1])
        with col1:
            score_text = f"(Score: {player_info['overall_score']:.1f})" if player_info['overall_score'] > 0 else ""
            st.markdown(f"**{i + 1}.** {player_info['name']} - {player_info['team']} {score_text}")
            st.caption(f"{player_info['position']} | Age: {player_info['age']} | Minutes: {player_info['minutes']}")
        with col2:
            if st.button("❌", key=f"remove_comp_{i}", help="Remove player"):
                comparison_manager.remove_player(i)
                st.rerun()

    if comparison_count >= 2:
        st.markdown("---")

        # Comparison options
        comparison_type = st.radio(
            "**Analysis Type:**",
            ["📊 Radar Chart", "📋 Stats Table", "📈 Percentiles", "🔍 Summary"],
            key="comparison_type",
            horizontal=True
        )

        if comparison_type == "📊 Radar Chart":
            show_radar_comparison(comparison_manager)

        elif comparison_type == "📋 Stats Table":
            show_table_comparison(comparison_manager)

        elif comparison_type == "📈 Percentiles":
            show_percentiles_comparison(comparison_manager)

        elif comparison_type == "🔍 Summary":
            show_summary_comparison(comparison_manager)

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear All", key="clear_comparison", use_container_width=True):
            comparison_manager.clear_all()
            st.rerun()

    with col2:
        if comparison_count >= 2:
            csv_data = comparison_manager.export_comparison_csv()
            if csv_data:
                st.download_button(
                    "📥 Export CSV",
                    csv_data,
                    "player_comparison.csv",
                    "text/csv",
                    use_container_width=True
                )


def show_radar_comparison(comparison_manager: ComparisonManager):
    """Show radar chart comparison"""

    players_data = comparison_manager.get_radar_data()

    if not players_data:
        st.error("Could not load radar data for comparison players")
        return

    # Get metrics from first player's position
    comparison_players = comparison_manager.get_comparison_players()
    main_position = comparison_players[0]['position']

    ranking_info = st.session_state.ranking_system.get_ranking_description(main_position)
    metrics = [metric[0] for metric in ranking_info['metrics']]

    ScoutingCharts.show_radar_comparison(
        players_data,
        metrics,
        main_position,
        "Player Performance Comparison"
    )

    # Show comparison insights
    st.markdown("### 🔍 Quick Insights")

    summary = comparison_manager.get_comparison_summary_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Players", summary['count'])
    with col2:
        st.metric("Avg Age", f"{summary['avg_age']:.1f}")
    with col3:
        st.metric("Avg Score", f"{summary['avg_score']:.1f}")


def show_table_comparison(comparison_manager: ComparisonManager):
    """Show detailed table comparison"""

    comparison_df = comparison_manager.get_comparison_data()

    if comparison_df.empty:
        st.error("Could not load comparison data")
        return

    # Display formatted table
    st.dataframe(
        comparison_df,
        use_container_width=True,
        height=400
    )

    # Show column explanations
    with st.expander("📖 Column Explanations"):
        st.markdown("""
        **Basic Info:**
        - **Position**: Player's primary position
        - **Age**: Current age
        - **Minutes**: Total minutes played this season
        - **Overall Score**: Weighted performance score (0-100)

        **Performance Metrics:**
        - Values shown are raw numbers from the season
        - Higher values generally indicate better performance
        - Compare across similar positions for best insights
        """)


def show_percentiles_comparison(comparison_manager: ComparisonManager):
    """Show percentiles comparison for all players"""

    percentiles_data = comparison_manager.get_percentiles_data()

    if not percentiles_data:
        st.error("No percentile data available")
        return

    # Show percentile bars for each player
    for player_name, data in percentiles_data.items():
        st.markdown(f"### {player_name} ({data['team']})")

        # Get ranking metrics for this player's position
        ranking_info = st.session_state.ranking_system.get_ranking_description(data['position'])
        if ranking_info:
            metrics = [metric[0] for metric in ranking_info['metrics']]

            # Create player data for percentile bars
            player_data = {}
            for metric in metrics:
                if metric in data['percentiles']:
                    player_data[f'{metric}_percentile'] = data['percentiles'][metric]

            if player_data:
                ScoutingCharts.show_percentile_bars(player_data, metrics, player_name)
            else:
                st.warning(f"No percentile data available for {player_name}")

        st.markdown("---")


def show_summary_comparison(comparison_manager: ComparisonManager):
    """Show summary insights and recommendations"""

    comparison_players = comparison_manager.get_comparison_players()
    summary = comparison_manager.get_comparison_summary_stats()

    # Overview
    st.markdown("### 📊 Comparison Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Players", summary['count'])
    with col2:
        st.metric("Average Age", f"{summary['avg_age']:.1f}")
    with col3:
        st.metric("Teams", summary['teams_count'])
    with col4:
        st.metric("Positions", summary['positions_count'])

    # Age analysis
    st.markdown("### 👶 Age Analysis")
    ages = [p['age'] for p in comparison_players]
    youngest = min(ages)
    oldest = max(ages)

    col1, col2 = st.columns(2)
    with col1:
        youngest_player = next(p for p in comparison_players if p['age'] == youngest)
        st.markdown(f"**Youngest:** {youngest_player['name']} ({youngest} years)")
    with col2:
        oldest_player = next(p for p in comparison_players if p['age'] == oldest)
        st.markdown(f"**Oldest:** {oldest_player['name']} ({oldest} years)")

    # Performance analysis
    st.markdown("### ⚽ Performance Analysis")

    if summary['avg_score'] > 0:
        scores = [(p['name'], p['overall_score']) for p in comparison_players if p['overall_score'] > 0]
        if scores:
            scores.sort(key=lambda x: x[1], reverse=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Highest Rated:** {scores[0][0]} ({scores[0][1]:.1f})")
            with col2:
                if len(scores) > 1:
                    st.markdown(f"**Lowest Rated:** {scores[-1][0]} ({scores[-1][1]:.1f})")

    # Experience analysis
    st.markdown("### ⏱️ Experience Analysis")

    minutes = [p['minutes'] for p in comparison_players]
    most_minutes = max(minutes)
    least_minutes = min(minutes)

    col1, col2 = st.columns(2)
    with col1:
        most_experienced = next(p for p in comparison_players if p['minutes'] == most_minutes)
        st.markdown(f"**Most Minutes:** {most_experienced['name']} ({most_minutes:,})")
    with col2:
        least_experienced = next(p for p in comparison_players if p['minutes'] == least_minutes)
        st.markdown(f"**Least Minutes:** {least_experienced['name']} ({least_minutes:,})")

    # Teams representation
    if summary['teams_count'] > 1:
        st.markdown("### 🏆 Teams Represented")
        for team in summary['teams']:
            team_players = [p['name'] for p in comparison_players if p['team'] == team]
            st.markdown(f"**{team}:** {', '.join(team_players)}")

    # Quick recommendations
    st.markdown("### 💡 Quick Insights")

    insights = []

    # Age diversity
    age_range = oldest - youngest
    if age_range > 8:
        insights.append("🎯 **High age diversity** - Good mix of experience levels")
    elif age_range < 3:
        insights.append("👥 **Similar age group** - Consistent experience level")

    # Experience diversity
    minutes_range = most_minutes - least_minutes
    if minutes_range > 1500:
        insights.append("⚖️ **Mixed experience** - From regulars to squad players")
    elif minutes_range < 500:
        insights.append("🎪 **Similar playing time** - All regular players")

    # Multi-team comparison
    if summary['teams_count'] >= 3:
        insights.append("🌍 **Multi-team comparison** - Good market overview")

    for insight in insights:
        st.markdown(insight)

    if not insights:
        st.info("Add more players for detailed insights!")