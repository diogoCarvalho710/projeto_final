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
        st.info("👆 Select a player from the Team Dashboard to view their profile!")

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
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()

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
        show_radar_chart(player_data, position)


def show_position_player_selector(position: str, current_player: str):
    """Show selector for other players in same position"""

    team = st.session_state.selected_team
    team_players = st.session_state.data_processor.get_team_players(team)

    if position in team_players:
        position_df = team_players[position]
        other_players = position_df[position_df['Jogador'] != current_player]['Jogador'].tolist()

        if other_players:
            # Create options list with current player first
            all_players = [current_player] + other_players

            # Find current index
            current_index = 0
            if current_player in all_players:
                current_index = all_players.index(current_player)

            selected = st.selectbox(
                f"🔄 Other {position} players:",
                all_players,
                index=current_index,
                key=f"player_selector_{position}"
            )

            # Only change if different player selected
            if selected != current_player:
                st.session_state.selected_player = {
                    'name': selected,
                    'position': position
                }
                # Force rerun to update profile
                st.rerun()


def show_player_overview(player_data: pd.Series, position: str):
    """Show player overview with basic info and key metrics"""

    # Personal Information
    st.subheader("ℹ️ Personal Information")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Age", f"{player_data.get('Idade', 'N/A')} years")

    with col2:
        st.metric("Height", player_data.get('Altura', 'N/A'))

    with col3:
        st.metric("Nationality", player_data.get('Nacionalidade', 'N/A'))

    with col4:
        st.metric("Preferred Foot", player_data.get('Pé', 'N/A'))

    st.divider()

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
        st.metric("Market Value", player_data.get('Valor de mercado', 'N/A'))

    st.divider()

    # Key Performance Metrics
    st.subheader("⚽ Key Performance")

    show_key_metrics_by_position(player_data, position)


def show_key_metrics_by_position(player_data: pd.Series, position: str):
    """Show position-specific key metrics"""

    if position == 'GR':
        # Goalkeeper metrics - using actual available columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            defenses = int(player_data.get('Defesas', 0))
            st.metric("Saves", defenses)
        with col2:
            save_pct = player_data.get('Defesas, %', 0)
            # Handle percentage strings like "72%"
            if pd.notna(save_pct):
                if isinstance(save_pct, str) and '%' in str(save_pct):
                    # Remove % and convert to float
                    try:
                        pct_value = float(str(save_pct).replace('%', ''))
                        st.metric("Save %", f"{pct_value:.1f}%")
                    except:
                        st.metric("Save %", str(save_pct))
                else:
                    try:
                        st.metric("Save %", f"{float(save_pct):.1f}%")
                    except:
                        st.metric("Save %", str(save_pct))
            else:
                st.metric("Save %", "0.0%")
        with col3:
            goals_conceded = int(player_data.get('Gols sofridos', 0))
            st.metric("Goals Conceded", goals_conceded)
        with col4:
            passes = int(player_data.get('Passes', 0))
            st.metric("Passes", passes)

    elif position in ['DCE', 'DCD', 'DE', 'DD']:
        # Defender metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            passes = int(player_data.get('Passes', 0))
            st.metric("Passes", passes)
        with col2:
            accurate_passes = int(player_data.get('Passes precisos', 0))
            st.metric("Accurate Passes", accurate_passes)
        with col3:
            interceptions = int(player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0))
            st.metric("Interceptions", interceptions)
        with col4:
            fouls = int(player_data.get('Faltas', 0))
            st.metric("Fouls", fouls)

    elif position in ['EE', 'ED', 'MCD', 'MC']:
        # Midfielder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            passes = int(player_data.get('Passes', 0))
            st.metric("Passes", passes)
        with col2:
            key_passes = int(player_data.get('Passes chave', 0))
            st.metric("Key Passes", key_passes)
        with col3:
            scoring_attacks = int(player_data.get('Participação em ataques de pontuação', 0))
            st.metric("Scoring Attacks", scoring_attacks)
        with col4:
            successful_actions = player_data.get('Ações / com sucesso', 0)
            # Handle potential string values
            try:
                if pd.notna(successful_actions):
                    st.metric("Successful Actions", int(float(successful_actions)))
                else:
                    st.metric("Successful Actions", 0)
            except:
                st.metric("Successful Actions", str(successful_actions))

    elif position == 'PL':
        # Forward metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            key_passes = int(player_data.get('Passes chave', 0))
            st.metric("Key Passes", key_passes)
        with col2:
            scoring_attacks = int(player_data.get('Participação em ataques de pontuação', 0))
            st.metric("Scoring Attacks", scoring_attacks)
        with col3:
            successful_actions = player_data.get('Ações / com sucesso', 0)
            # Handle potential string values
            try:
                if pd.notna(successful_actions):
                    st.metric("Successful Actions", int(float(successful_actions)))
                else:
                    st.metric("Successful Actions", 0)
            except:
                st.metric("Successful Actions", str(successful_actions))
        with col4:
            fouls = int(player_data.get('Faltas', 0))
            st.metric("Fouls", fouls)


def show_player_statistics(player_data: pd.Series, position: str):
    """Show detailed player statistics"""

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
            st.subheader(f"📈 {category}")

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
    """Show performance analysis with comparisons"""

    st.subheader("📈 Performance Analysis")

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
            st.subheader("🔄 vs Position Average")

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

    # Performance over time (if available)
    show_performance_trends(player_data)


def show_performance_trends(player_data: pd.Series):
    """Show performance trends if data is available"""

    st.subheader("📊 Season Performance")

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


def show_radar_chart(player_data: pd.Series, position: str):
    """Show radar chart for player analysis"""

    st.subheader("🎯 Radar Chart Analysis")

    # Get metrics for radar chart based on actual available columns
    radar_metrics = get_radar_metrics_for_position_actual(position, player_data.index)

    # Prepare data
    radar_data = []
    radar_labels = []

    for metric in radar_metrics:
        if metric in player_data.index:
            value = player_data[metric]

            # Convert to numeric, handling strings
            try:
                numeric_value = pd.to_numeric(value, errors='coerce')
                if pd.notna(numeric_value):
                    radar_data.append(float(numeric_value))
                    radar_labels.append(metric)
            except:
                continue

    if len(radar_data) < 3:
        st.warning("Not enough data points for radar chart. Need at least 3 metrics.")
        return

    # Normalize data for radar chart (0-100 scale)
    max_values = get_max_values_for_position(position)
    normalized_data = []

    for i, value in enumerate(radar_data):
        metric = radar_labels[i]
        max_val = max_values.get(metric, value * 2)  # Default to value * 2 if no max
        if max_val > 0:
            normalized_value = min(100, (value / max_val) * 100)
        else:
            normalized_value = 0
        normalized_data.append(normalized_value)

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=normalized_data + [normalized_data[0]],  # Close the polygon
        theta=radar_labels + [radar_labels[0]],  # Close the polygon
        fill='toself',
        name=player_data.get('Jogador', 'Player'),
        line_color='rgb(79, 70, 229)',
        fillcolor='rgba(79, 70, 229, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20
            )
        ),
        showlegend=True,
        title=f"Performance Radar - {player_data.get('Jogador', 'Player')}",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show radar metrics explanation
    with st.expander("📖 Radar Chart Explanation"):
        st.markdown(f"""
        **Radar Chart for {position} Position:**

        This radar chart shows the player's performance across key metrics for their position.
        Values are normalized on a 0-100 scale based on typical ranges for the position.

        **Metrics shown:**
        """)

        for i, metric in enumerate(radar_labels):
            original_value = radar_data[i]
            normalized_value = normalized_data[i]
            st.markdown(f"- **{metric}**: {original_value:.2f} (Score: {normalized_value:.0f}/100)")


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


def get_radar_metrics_for_position_actual(position: str, available_columns: List) -> List[str]:
    """Get radar metrics based on actual available columns in the data"""

    # Convert to list if it's an Index
    if hasattr(available_columns, 'tolist'):
        available_columns = available_columns.tolist()

    # Priority metrics by position based on actual CSV columns
    position_priorities = {
        'GR': [
            'Defesas', 'Gols sofridos', 'Passes', 'Passes precisos', 'Defesas, %',
            'Chutes do adv.', 'Defesas difíceis', 'Passes precisos %'
        ],
        'DCE': [
            'Passes', 'Passes precisos', 'Passes precisos %',
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',
            'Defesas', 'Faltas', 'Cartões amarelos'
        ],
        'DCD': [
            'Passes', 'Passes precisos', 'Passes precisos %',
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',
            'Defesas', 'Faltas', 'Cartões amarelos'
        ],
        'DE': [
            'Passes', 'Passes precisos', 'Passes chave', 'Cruzamentos do adversário',
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'Faltas'
        ],
        'DD': [
            'Passes', 'Passes precisos', 'Passes chave', 'Cruzamentos do adversário',
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'Faltas'
        ],
        'EE': [
            'Passes chave', 'Passes precisos', 'Passes', 'Participação em ataques de pontuação',
            'Ações / com sucesso', 'Faltas'
        ],
        'ED': [
            'Passes chave', 'Passes precisos', 'Passes', 'Participação em ataques de pontuação',
            'Ações / com sucesso', 'Faltas'
        ],
        'MCD': [
            'Passes', 'Passes precisos', 'Tentativas bem-sucedidas de interceptação de cruzamento e passe',
            'Passes chave', 'Ações / com sucesso', 'Faltas'
        ],
        'MC': [
            'Passes', 'Passes chave', 'Passes precisos', 'Participação em ataques de pontuação',
            'Ações / com sucesso', 'Passes chave precisos'
        ],
        'PL': [
            'Passes chave', 'Participação em ataques de pontuação', 'Ações / com sucesso',
            'Passes', 'Passes precisos', 'Faltas'
        ]
    }

    # Get priority list for position
    priorities = position_priorities.get(position, [
        'Passes', 'Passes precisos', 'Passes chave', 'Ações / com sucesso', 'Faltas'
    ])

    # Find metrics that exist in the data
    found_metrics = []
    for metric in priorities:
        if metric in available_columns:
            found_metrics.append(metric)
            if len(found_metrics) >= 5:  # Limit to 5 metrics for readability
                break

    # If not enough specific metrics found, add general numeric ones
    if len(found_metrics) < 3:
        exclude = ['Idade', 'Partidas jogadas', 'Minutos jogados', 'Index'] + found_metrics

        for col in available_columns:
            if col not in exclude and len(found_metrics) < 5:
                # Check if it looks like a numeric performance metric
                if any(word in col.lower() for word in ['pass', 'gol', 'defes', 'chute', 'falta', 'açõ', 'cruzamento']):
                    found_metrics.append(col)

    return found_metrics[:5]  # Return max 5 metrics


def get_radar_metrics_for_position(position: str) -> List[str]:
    """Get metrics for radar chart by position - DEPRECATED, kept for compatibility"""

    # Basic fallback metrics
    radar_metrics = {
        'GR': ['Gols sofridos', 'Passes', 'Defesas', 'Partidas jogadas', 'Minutos jogados'],
        'DCE': ['Passes', 'Passes precisos', 'Defesas', 'Faltas', 'Cartões amarelos'],
        'DCD': ['Passes', 'Passes precisos', 'Defesas', 'Faltas', 'Cartões amarelos'],
        'DE': ['Passes', 'Passes chave', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'DD': ['Passes', 'Passes chave', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'EE': ['Passes chave', 'Passes', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'ED': ['Passes chave', 'Passes', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'MCD': ['Passes', 'Passes chave', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'MC': ['Passes', 'Passes chave', 'Faltas', 'Defesas', 'Cartões amarelos'],
        'PL': ['Passes chave', 'Passes', 'Faltas', 'Defesas', 'Cartões amarelos']
    }

    return radar_metrics.get(position, ['Passes', 'Faltas', 'Defesas', 'Cartões amarelos', 'Partidas jogadas'])


def get_max_values_for_position(position: str) -> Dict[str, float]:
    """Get typical maximum values for radar chart normalization"""

    max_values = {
        # Goalkeepers
        'Defesas': 150, 'Passes': 1000, 'Passes longos': 200, 'Defesas %': 100, 'Jogos sem sofrer gols': 15,

        # Defenders
        'Desarmes': 100, 'Interceptações': 80, 'Disputas na defesa': 200, 'Disputas aéreas': 150,
        'Cruzamentos': 80, 'Passes progressivos': 200,

        # Midfielders
        'Passes': 2000, 'Passes para chute': 80, 'Bolas recuperadas': 200,

        # Wingers/Forwards
        'Dribles': 100, 'Disputas no ataque': 150, 'Chutes': 100,

        # General
        'Gols': 30, 'Assistências': 20, 'xG': 25, 'Faltas': 50
    }

    return max_values