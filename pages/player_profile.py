import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List


def show_player_profile():
    """Display detailed player profile page"""

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    # Check if player is selected
    if not st.session_state.get('selected_player'):
        st.title("👤 Player Profile")
        st.info("👆 Select a player from the Team Dashboard or Scouting page to view their profile!")

        # Back button
        if st.button("🏠 Back to Team Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        return

    player_name = st.session_state.selected_player['name']
    position = st.session_state.selected_player['position']

    # Get player data
    player_data = st.session_state.data_processor.get_player_data(player_name, position)

    if player_data is None:
        st.error(f"Player {player_name} not found in {position} data!")
        return

    # Page header
    st.title(f"👤 Player Profile")
    st.subheader(f"{player_name} ({position})")

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()

    with col2:
        if st.button("🔍 Back to Scouting"):
            st.session_state.current_page = 'scouting'
            st.rerun()

    with col3:
        # Add to favorites button (moved here as requested)
        if st.button("⭐ Add to Favorites", key="add_to_favorites"):
            try:
                if 'favorites_manager' not in st.session_state:
                    from src.favorites_manager import FavoritesManager
                    st.session_state.favorites_manager = FavoritesManager(st.session_state.data_processor)

                favorites_manager = st.session_state.favorites_manager

                if favorites_manager.add_to_favorites(
                        player_name,
                        position,
                        reason="Added from player profile",
                        collection="Player Profiles"
                ):
                    st.success(f"✅ {player_name} added to favorites!")
                else:
                    st.warning(f"⚠️ {player_name} is already in favorites or could not be added")
            except Exception as e:
                st.error(f"Error adding to favorites: {str(e)}")

    st.divider()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "📊 Statistics", "📈 Performance", "🎯 Radar Chart"])

    with tab1:
        show_player_overview(player_data, position)

    with tab2:
        show_player_statistics(player_data, position)

    with tab3:
        show_performance_analysis(player_data, position)

    with tab4:
        show_customizable_radar_chart(player_data, position)


def show_player_overview(player_data: pd.Series, position: str):
    """Show player overview with basic info and key metrics"""

    # Personal Information
    st.subheader("ℹ️ Personal Information")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Age", f"{player_data.get('Idade', 'N/A')} years")

    with col2:
        st.metric("Height", player_data.get('Altura', 'N/A'))

    with col3:
        st.metric("Nationality", player_data.get('Nacionalidade', 'N/A'))

    with col4:
        st.metric("Preferred Foot", player_data.get('Pé', 'N/A'))

    with col5:
        st.metric("Market Value", player_data.get('Valor de mercado', 'N/A'))

    st.markdown("---")

    # Playing Time
    st.subheader("⏱️ Playing Time")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        minutes = int(player_data.get('Minutos jogados', 0))
        st.metric("Minutes Played", f"{minutes:,}")

    with col2:
        matches = int(player_data.get('Partidas jogadas', 0))
        st.metric("Matches Played", matches)

    with col3:
        avg_minutes = round(minutes / matches, 1) if matches > 0 else 0
        st.metric("Minutes per Match", avg_minutes)

    with col4:
        # Playing time consistency
        if matches > 0:
            consistency = min(100, (minutes / (matches * 90)) * 100)
            st.metric("Playing Time %", f"{consistency:.1f}%")
        else:
            st.metric("Playing Time %", "0.0%")

    st.markdown("---")

    # Key Performance Metrics
    st.subheader("⚽ Key Performance Metrics")

    show_key_metrics_by_position(player_data, position)


def show_key_metrics_by_position(player_data: pd.Series, position: str):
    """Show position-specific key metrics"""

    minutes = player_data.get('Minutos jogados', 0)

    if position == 'GR':
        # Goalkeeper metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            saves = player_data.get('Defesas', 0)
            saves_per90 = (saves * 90 / minutes) if minutes > 0 else 0
            st.metric("Saves /90", f"{saves_per90:.2f}")

        with col2:
            save_pct = player_data.get('Defesas, %', 0)
            if isinstance(save_pct, str) and '%' in str(save_pct):
                try:
                    pct_value = float(str(save_pct).replace('%', ''))
                    st.metric("Saves %", f"{pct_value:.1f}%")
                except:
                    st.metric("Saves %", str(save_pct))
            else:
                try:
                    st.metric("Saves %", f"{float(save_pct):.1f}%")
                except:
                    st.metric("Saves %", "0.0%")

        with col3:
            goals_conceded = player_data.get('Gols sofridos', 0)
            goals_per90 = (goals_conceded * 90 / minutes) if minutes > 0 else 0
            st.metric("Goals Conceded /90", f"{goals_per90:.2f}")

        with col4:
            pass_pct = player_data.get('Passes precisos %', 0)
            if isinstance(pass_pct, str) and '%' in str(pass_pct):
                try:
                    pct_value = float(str(pass_pct).replace('%', ''))
                    st.metric("Pass Accuracy %", f"{pct_value:.1f}%")
                except:
                    st.metric("Pass Accuracy %", str(pass_pct))
            else:
                try:
                    st.metric("Pass Accuracy %", f"{float(pass_pct):.1f}%")
                except:
                    st.metric("Pass Accuracy %", "0.0%")

        with col5:
            # Cross interceptions - using available metric
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Cross Interceptions /90", f"{inter_per90:.2f}")

    elif position in ['DCE', 'DCD']:
        # Centre-Back metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            tackles = player_data.get('Desarmes', 0)
            tackles_per90 = (tackles * 90 / minutes) if minutes > 0 else 0
            st.metric("Tackles /90", f"{tackles_per90:.2f}")

        with col2:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col3:
            aerial_duels = player_data.get('Disputas aéreas', 0)
            aerial_per90 = (aerial_duels * 90 / minutes) if minutes > 0 else 0
            st.metric("Aerial Duels /90", f"{aerial_per90:.2f}")

        with col4:
            accurate_passes = player_data.get('Passes precisos', 0)
            passes_per90 = (accurate_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Accurate Passes /90", f"{passes_per90:.2f}")

        with col5:
            prog_passes = player_data.get('Passes progressivos', 0)
            prog_per90 = (prog_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Progressive Passes /90", f"{prog_per90:.2f}")

    elif position in ['DE', 'DD']:
        # Full-Back metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            tackles = player_data.get('Desarmes', 0)
            tackles_per90 = (tackles * 90 / minutes) if minutes > 0 else 0
            st.metric("Tackles /90", f"{tackles_per90:.2f}")

        with col2:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col3:
            accurate_crosses = player_data.get('Cruzamentos precisos', 0)
            crosses_per90 = (accurate_crosses * 90 / minutes) if minutes > 0 else 0
            st.metric("Accurate Crosses /90", f"{crosses_per90:.2f}")

        with col4:
            successful_dribbles = player_data.get('Dribles bem-sucedidos', 0)
            dribbles_per90 = (successful_dribbles * 90 / minutes) if minutes > 0 else 0
            st.metric("Successful Dribbles /90", f"{dribbles_per90:.2f}")

        with col5:
            # Passes to penalty area - using available metric
            key_passes = player_data.get('Passes chave', 0)
            key_per90 = (key_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Key Passes /90", f"{key_per90:.2f}")

    elif position == 'MCD':
        # Defensive Midfielder metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            recoveries = player_data.get('Bolas recuperadas', 0)
            rec_per90 = (recoveries * 90 / minutes) if minutes > 0 else 0
            st.metric("Ball Recoveries /90", f"{rec_per90:.2f}")

        with col2:
            tackles = player_data.get('Desarmes', 0)
            tackles_per90 = (tackles * 90 / minutes) if minutes > 0 else 0
            st.metric("Tackles /90", f"{tackles_per90:.2f}")

        with col3:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col4:
            def_duels = player_data.get('Disputas na defesa', 0)
            def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
            if def_duels > 0:
                def_win_pct = (def_duels_won / def_duels) * 100
                st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
            else:
                st.metric("Defensive Duels Won %", "0.0%")

        with col5:
            prog_passes = player_data.get('Passes progressivos', 0)
            prog_per90 = (prog_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Progressive Passes /90", f"{prog_per90:.2f}")

    elif position == 'MC':
        # Central Midfielder metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            successful_passes = player_data.get('Passes precisos', 0)
            passes_per90 = (successful_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Successful Passes /90", f"{passes_per90:.2f}")

        with col2:
            successful_dribbles = player_data.get('Dribles bem-sucedidos', 0)
            dribbles_per90 = (successful_dribbles * 90 / minutes) if minutes > 0 else 0
            st.metric("Successful Dribbles /90", f"{dribbles_per90:.2f}")

        with col3:
            shots_on_target = player_data.get('Chutes no gol', 0)
            shots_per90 = (shots_on_target * 90 / minutes) if minutes > 0 else 0
            st.metric("Shots on Target /90", f"{shots_per90:.2f}")

        with col4:
            key_passes = player_data.get('Passes chave', 0)
            key_per90 = (key_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Key Passes /90", f"{key_per90:.2f}")

        with col5:
            xa = player_data.get('xA', 0)
            xa_per90 = (xa * 90 / minutes) if minutes > 0 else 0
            st.metric("Expected Assists /90", f"{xa_per90:.2f}")

    elif position in ['EE', 'ED']:
        # Winger metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            successful_dribbles = player_data.get('Dribles bem-sucedidos', 0)
            dribbles_per90 = (successful_dribbles * 90 / minutes) if minutes > 0 else 0
            st.metric("Successful Dribbles /90", f"{dribbles_per90:.2f}")

        with col2:
            accurate_crosses = player_data.get('Cruzamentos precisos', 0)
            crosses_per90 = (accurate_crosses * 90 / minutes) if minutes > 0 else 0
            st.metric("Accurate Crosses /90", f"{crosses_per90:.2f}")

        with col3:
            # Final third actions - using available metric
            final_third = player_data.get('Ações no terço final', 0)
            final_per90 = (final_third * 90 / minutes) if minutes > 0 else 0
            st.metric("Final Third Actions /90", f"{final_per90:.2f}")

        with col4:
            shots_on_target = player_data.get('Chutes no gol', 0)
            shots_per90 = (shots_on_target * 90 / minutes) if minutes > 0 else 0
            st.metric("Shots on Target /90", f"{shots_per90:.2f}")

        with col5:
            xa = player_data.get('xA', 0)
            xa_per90 = (xa * 90 / minutes) if minutes > 0 else 0
            st.metric("Expected Assists /90", f"{xa_per90:.2f}")

        with col6:
            xg = player_data.get('xG', 0)
            xg_per90 = (xg * 90 / minutes) if minutes > 0 else 0
            st.metric("Expected Goals /90", f"{xg_per90:.2f}")

    elif position == 'PL':
        # Forward metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            goals = player_data.get('Gols', 0)
            goals_per90 = (goals * 90 / minutes) if minutes > 0 else 0
            st.metric("Goals /90", f"{goals_per90:.2f}")

        with col2:
            xg = player_data.get('xG', 0)
            xg_per90 = (xg * 90 / minutes) if minutes > 0 else 0
            st.metric("Expected Goals /90", f"{xg_per90:.2f}")

        with col3:
            shots_on_target = player_data.get('Chutes no gol', 0)
            shots_per90 = (shots_on_target * 90 / minutes) if minutes > 0 else 0
            st.metric("Shots on Target /90", f"{shots_per90:.2f}")

        with col4:
            successful_dribbles = player_data.get('Dribles bem-sucedidos', 0)
            dribbles_per90 = (successful_dribbles * 90 / minutes) if minutes > 0 else 0
            st.metric("Successful Dribbles /90", f"{dribbles_per90:.2f}")

        with col5:
            penalty_area_touches = player_data.get('Toques na área', 0)
            touches_per90 = (penalty_area_touches * 90 / minutes) if minutes > 0 else 0
            st.metric("Penalty Area Touches /90", f"{touches_per90:.2f}")


def show_player_statistics(player_data: pd.Series, position: str):
    """Show detailed player statistics with better section divisions"""

    st.subheader("📊 Detailed Statistics")

    # Get numeric columns
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado', 'Position_File']

    # Get all columns and filter numeric ones
    all_metrics = {}
    for col in player_data.index:
        if col not in exclude_cols:
            value = player_data[col]
            # Check if it's numeric
            if pd.api.types.is_numeric_dtype(type(value)):
                all_metrics[col] = value

    if not all_metrics:
        st.warning("No numeric statistics available for this player.")
        return

    # Group metrics by category
    metric_categories = categorize_metrics(all_metrics, position)

    for category, metrics in metric_categories.items():
        if metrics:
            # Section header with strong divider
            st.markdown(f"## 📈 {category}")
            st.markdown("---")

            # Show metrics in columns
            metrics_per_row = 4
            metric_items = list(metrics.items())

            for i in range(0, len(metric_items), metrics_per_row):
                cols = st.columns(metrics_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(metric_items):
                        metric_name, metric_value = metric_items[i + j]

                        # Format value
                        if isinstance(metric_value, float):
                            formatted_value = f"{metric_value:.2f}"
                        else:
                            formatted_value = str(metric_value)

                        with col:
                            st.metric(metric_name, formatted_value)

            # Lighter divider between sections
            st.markdown("---")


def categorize_metrics(metrics: Dict, position: str) -> Dict[str, Dict]:
    """Categorize metrics by type"""

    categories = {
        "Offensive": {},
        "Defensive": {},
        "Passing": {},
        "Physical": {},
        "Per 90 Minutes": {},
        "Advanced": {}
    }

    # Keywords for categorization
    offensive_keywords = ['gol', 'assist', 'chute', 'xg', 'xa']
    defensive_keywords = ['desarme', 'intercepta', 'defes', 'disputa na defesa', 'bola recuperada']
    passing_keywords = ['pass', 'cruz', 'cruzamento']
    physical_keywords = ['falta', 'cartão', 'disputa']
    per90_keywords = ['per90', '_per90']
    advanced_keywords = ['xg', 'xa', '%']

    for metric_name, value in metrics.items():
        metric_lower = metric_name.lower()

        # Check per 90 first
        if any(keyword in metric_lower for keyword in per90_keywords):
            categories["Per 90 Minutes"][metric_name] = value
        elif any(keyword in metric_lower for keyword in advanced_keywords):
            categories["Advanced"][metric_name] = value
        elif any(keyword in metric_lower for keyword in offensive_keywords):
            categories["Offensive"][metric_name] = value
        elif any(keyword in metric_lower for keyword in defensive_keywords):
            categories["Defensive"][metric_name] = value
        elif any(keyword in metric_lower for keyword in passing_keywords):
            categories["Passing"][metric_name] = value
        elif any(keyword in metric_lower for keyword in physical_keywords):
            categories["Physical"][metric_name] = value
        else:
            # Default category based on position
            if position == 'GR':
                categories["Defensive"][metric_name] = value
            elif position in ['DCE', 'DCD', 'DE', 'DD']:
                categories["Defensive"][metric_name] = value
            elif position in ['EE', 'ED', 'MCD', 'MC']:
                categories["Passing"][metric_name] = value
            elif position == 'PL':
                categories["Offensive"][metric_name] = value
            else:
                categories["Physical"][metric_name] = value

    return categories


def show_performance_analysis(player_data: pd.Series, position: str):
    """Show performance analysis with comparisons and better section divisions"""

    # Main section header
    st.subheader("📈 Performance Analysis")
    st.markdown("---")

    # Position comparison section
    st.markdown("## 🔄 vs Position Average")

    # Get position averages for comparison
    team_players = st.session_state.data_processor.get_team_players(st.session_state.selected_team)

    if position in team_players:
        position_df = team_players[position]

        # Key metrics for comparison
        key_metrics = get_key_metrics_for_position(position)

        comparison_data = []

        for metric in key_metrics:
            if metric in player_data.index and metric in position_df.columns:
                player_value = player_data[metric]

                # Convert metric column to numeric, handling strings
                try:
                    position_series = pd.to_numeric(position_df[metric], errors='coerce')
                    position_avg = position_series.mean()

                    # Convert player value to numeric
                    player_value_numeric = pd.to_numeric(player_value, errors='coerce')

                    if pd.notna(player_value_numeric) and pd.notna(position_avg):
                        comparison_data.append({
                            'Metric': metric,
                            'Player': float(player_value_numeric),
                            'Position Average': float(position_avg),
                            'Difference': float(player_value_numeric - position_avg)
                        })
                except Exception as e:
                    # Skip metric if conversion fails
                    continue

        if comparison_data:
            # Display comparison
            for data in comparison_data:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        data['Metric'],
                        f"{data['Player']:.2f}"
                    )

                with col2:
                    st.metric(
                        "Position Avg",
                        f"{data['Position Average']:.2f}"
                    )

                with col3:
                    diff = data['Difference']
                    delta_color = "normal"
                    if diff > 0:
                        delta_text = f"+{diff:.2f}"
                        delta_color = "normal"
                    else:
                        delta_text = f"{diff:.2f}"
                        delta_color = "inverse"

                    st.metric(
                        "Difference",
                        delta_text,
                        delta=delta_text,
                        delta_color=delta_color
                    )
        else:
            st.info("No comparable metrics found for position analysis.")

    # Section divider
    st.markdown("---")

    # Performance over time section
    st.markdown("## 📊 Season Performance")

    show_performance_trends(player_data)


def show_performance_trends(player_data: pd.Series):
    """Show performance trends if data is available"""

    # Show key season metrics
    col1, col2, col3 = st.columns(3)

    minutes = int(player_data.get('Minutos jogados', 0))
    matches = int(player_data.get('Partidas jogadas', 0))

    with col1:
        if matches > 0:
            consistency = min(100, (minutes / (matches * 90)) * 100)
            st.metric("Playing Time %", f"{consistency:.1f}%")
        else:
            st.metric("Playing Time %", "0.0%")

    with col2:
        goals = int(player_data.get('Gols', 0))
        if minutes > 0:
            goals_per_90 = (goals * 90) / minutes
            st.metric("Goals per 90min", f"{goals_per_90:.2f}")
        else:
            st.metric("Goals per 90min", "0.00")

    with col3:
        assists = int(player_data.get('Assistências', 0))
        if minutes > 0:
            assists_per_90 = (assists * 90) / minutes
            st.metric("Assists per 90min", f"{assists_per_90:.2f}")
        else:
            st.metric("Assists per 90min", "0.00")


def show_customizable_radar_chart(player_data: pd.Series, position: str):
    """Show customizable radar chart for player analysis"""

    st.subheader("🎯 Customizable Radar Chart Analysis")

    # Get available numeric metrics
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                    'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados']

    available_metrics = []
    for col in player_data.index:
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(type(player_data[col])):
            if not col.endswith('_percentile') and col != 'Overall_Score':
                available_metrics.append(col)

    available_metrics = sorted(available_metrics)

    if not available_metrics:
        st.warning("No metrics available for radar chart.")
        return

    # Metric selection
    st.markdown("### 🔧 Select Variables for Radar Chart")

    # Number of metrics selector
    max_metrics = min(8, len(available_metrics))
    num_metrics = st.slider(
        "Number of variables:",
        min_value=3,
        max_value=max_metrics,
        value=min(6, max_metrics),
        key="radar_num_metrics"
    )

    # Metric selection
    selected_metrics = []
    cols = st.columns(2)

    for i in range(num_metrics):
        col_idx = i % 2
        with cols[col_idx]:
            metric = st.selectbox(
                f"Variable {i + 1}",
                available_metrics,
                index=i if i < len(available_metrics) else 0,
                key=f"radar_metric_{i}"
            )
            selected_metrics.append(metric)

    # Player comparison option
    st.markdown("### 👥 Compare with Other Players")

    # Get all players from same position across all teams
    position_df = st.session_state.data_processor.dataframes[position]
    all_players = position_df['Jogador'].tolist()

    # Remove current player from options
    other_players = [p for p in all_players if p != player_data.get('Jogador')]

    compare_players = st.multiselect(
        "Select players to compare with (optional):",
        other_players,
        max_selections=4,
        key="radar_compare_players"
    )

    if st.button("Generate Radar Chart", key="generate_radar"):
        if len(set(selected_metrics)) >= 3:
            create_customizable_radar_chart(
                player_data, position, selected_metrics, compare_players
            )
        else:
            st.error("Please select at least 3 different variables")


def create_customizable_radar_chart(player_data: pd.Series, position: str,
                                    selected_metrics: List[str], compare_players: List[str]):
    """Create the actual customizable radar chart"""

    # Get position dataframe for percentile calculations
    position_df = st.session_state.data_processor.dataframes[position]

    # Prepare players data for radar
    players_data = []

    # Add main player
    main_player_data = {'Player': player_data.get('Jogador', 'Main Player')}
    for metric in selected_metrics:
        if metric in player_data.index:
            # Calculate percentile for this metric
            values = pd.to_numeric(position_df[metric], errors='coerce')
            percentile = (values.rank(pct=True) * 100).fillna(0)

            # Find player's percentile
            player_row_idx = position_df[position_df['Jogador'] == player_data.get('Jogador')].index
            if len(player_row_idx) > 0:
                player_percentile = percentile.iloc[player_row_idx[0]]
            else:
                player_percentile = 50  # Default to median

            main_player_data[f'{metric}_percentile'] = player_percentile

    players_data.append(main_player_data)

    # Add comparison players
    for comp_player_name in compare_players:
        comp_player_row = position_df[position_df['Jogador'] == comp_player_name]
        if not comp_player_row.empty:
            comp_player_data = {'Player': comp_player_name}
            for metric in selected_metrics:
                if metric in position_df.columns:
                    values = pd.to_numeric(position_df[metric], errors='coerce')
                    percentile = (values.rank(pct=True) * 100).fillna(0)

                    comp_player_percentile = percentile.iloc[comp_player_row.index[0]]
                    comp_player_data[f'{metric}_percentile'] = comp_player_percentile

            players_data.append(comp_player_data)

    # Create radar chart
    from components.charts import ScoutingCharts

    ScoutingCharts.show_radar_comparison(
        players_data,
        selected_metrics,
        position,
        f"Custom Radar Chart - {player_data.get('Jogador', 'Player')}"
    )

    # Show explanation
    with st.expander("📖 Chart Explanation"):
        st.markdown(f"""
        **Custom Radar Chart Explanation:**

        - Each axis represents one of your selected variables
        - Values are shown as **percentiles** (0-100) compared to all {position} players in the dataset
        - **Higher values = better performance** for that variable
        - The colored area shows each player's overall profile across selected variables
        - **Larger area = better overall performance** in the selected metrics

        **Selected Variables:**
        """)

        for i, metric in enumerate(selected_metrics):
            original_value = player_data.get(metric, 0)
            st.markdown(f"• **{metric}**: {original_value:.2f}")


def get_key_metrics_for_position(position: str) -> List[str]:
    """Get key metrics for performance comparison by position"""

    # Updated to use actual CSV column names from the data you showed
    metrics = {
        'GR': ['Gols sofridos', 'Defesas', 'Passes', 'Defesas, %'],
        'DCE': ['Passes', 'Passes precisos', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                'Faltas'],
        'DCD': ['Passes', 'Passes precisos', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                'Faltas'],
        'DE': ['Passes', 'Passes chave', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'Faltas'],
        'DD': ['Passes', 'Passes chave', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'Faltas'],
        'EE': ['Passes chave', 'Passes precisos', 'Participação em ataques de pontuação', 'Ações / com sucesso'],
        'ED': ['Passes chave', 'Passes precisos', 'Participação em ataques de pontuação', 'Ações / com sucesso'],
        'MCD': ['Passes', 'Passes chave', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'Faltas'],
        'MC': ['Passes', 'Passes chave', 'Participação em ataques de pontuação', 'Ações / com sucesso'],
        'PL': ['Passes chave', 'Participação em ataques de pontuação', 'Ações / com sucesso', 'Passes precisos']
    }

    return metrics.get(position, ['Passes', 'Passes precisos', 'Faltas', 'Ações / com sucesso'])