import streamlit as st
import pandas as pd
from src.team_manager import TeamManager


def show_team_dashboard():
    """Display team dashboard with squad overview"""
    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    team_manager = TeamManager(st.session_state.data_processor)
    team = st.session_state.selected_team

    # Page header
    st.title(f"🏠 {team} - Squad Dashboard")

    # Get squad analysis
    analysis = team_manager.get_squad_analysis(team)

    if not analysis:
        st.error(f"No players found for {team}")
        return

    # Team statistics
    show_team_stats(analysis['stats'])

    # Navigation tabs (removed Formation tab as requested)
    tab1, tab2 = st.tabs(["📋 Squad List", "📊 Statistics"])

    with tab1:
        show_squad_list(analysis, team_manager)

    with tab2:
        show_detailed_stats(analysis)


def show_team_stats(stats: dict):
    """Display team statistics cards"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="👥 Total Players",
            value=stats['total_players']
        )

    with col2:
        st.metric(
            label="📊 Average Age",
            value=f"{stats['average_age']} years"
        )

    with col3:
        st.metric(
            label="⏱️ Total Minutes",
            value=f"{stats['total_minutes']:,}"
        )


def show_squad_list(analysis: dict, team_manager: TeamManager):
    """Display squad organized by position with player cards"""

    # Position order for display (updated as requested)
    position_order = ["GR", "DCE", "DCD", "DE", "DD", "MCD", "MC", "EE", "ED", "PL"]
    position_names = {
        "GR": "🥅 Goalkeepers",
        "DCE": "🛡️ Centre-Backs (Left)",
        "DCD": "🛡️ Centre-Backs (Right)",
        "DE": "⬅️ Left-Backs",
        "DD": "➡️ Right-Backs",
        "MCD": "🛡️ Defensive Midfielders",
        "MC": "⚽ Central Midfielders",
        "EE": "⬅️ Left Wingers",
        "ED": "➡️ Right Wingers",
        "PL": "🎯 Forwards"
    }

    for pos in position_order:
        if pos in analysis['starters'] or pos in analysis['subs']:
            st.subheader(position_names.get(pos, pos))

            # Show starters first
            if pos in analysis['starters'] and not analysis['starters'][pos].empty:
                st.markdown("**🟢 Starters**")
                show_position_players(analysis['starters'][pos], team_manager, True, pos)

            # Show substitutes
            if pos in analysis['subs'] and not analysis['subs'][pos].empty:
                st.markdown("**⚪ Substitutes**")
                show_position_players(analysis['subs'][pos], team_manager, False, pos)

            st.divider()


def show_position_players(df, team_manager, is_starter: bool, position: str):
    """Display players for a specific position"""

    # Show players in rows of 3
    players_per_row = 3
    players_list = df.to_dict('records')

    for i in range(0, len(players_list), players_per_row):
        cols = st.columns(players_per_row)

        for j, col in enumerate(cols):
            if i + j < len(players_list):
                player = players_list[i + j]

                # Add position info to player data
                player_series = pd.Series(player)
                player_series['Position_File'] = position

                player_data = team_manager.get_player_card_data(player_series, is_starter)

                with col:
                    show_player_card_updated(player_data, position, f"{position}_{i}_{j}")


def show_player_card_updated(player_data: dict, position: str, unique_id: str = ""):
    """Display individual player card with position-specific stats (UPDATED VERSION)"""

    status_icon = "🟢" if player_data['is_starter'] else "⚪"

    # Create unique key
    card_key = f"player_{unique_id}_{player_data['name']}_{player_data['minutes']}"

    with st.container():
        # Player header - only clickable name (removed eye icon)
        if st.button(
                f"{status_icon} {player_data['name']}",
                key=f"name_{card_key}",
                help="Click to view player profile",
                use_container_width=True
        ):
            # Store player info for profile page
            st.session_state.selected_player = {
                'name': player_data['name'],
                'position': player_data['position_file']
            }
            st.session_state.show_player_profile = True
            st.rerun()

        st.caption(f"Age: {player_data['age']} | {player_data['nationality']}")

        # Position-specific stats (UPDATED)
        stat1, stat2, stat3 = get_position_specific_stats(player_data, position)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(stat1['name'], stat1['value'])
        with col2:
            st.metric(stat2['name'], stat2['value'])
        with col3:
            st.metric(stat3['name'], stat3['value'])

        # Additional info
        st.caption(f"👣 {player_data['foot']} foot")

        # Add subtle separator
        st.markdown("---")


def get_position_specific_stats(player_data: dict, position: str) -> tuple:
    """Get position-specific statistics for player card"""

    # Get the raw player data to access all metrics
    player_name = player_data['name']
    position_file = player_data['position_file']

    # Get player data from data processor
    player_series = st.session_state.data_processor.get_player_data(player_name, position_file)

    if player_series is None:
        # Fallback to basic stats
        return (
            {"name": "Minutes", "value": player_data.get('minutes', 0)},
            {"name": "Goals", "value": player_data.get('goals', 0)},
            {"name": "Assists", "value": player_data.get('assists', 0)}
        )

    minutes = player_series.get('Minutos jogados', 0)

    if position == 'GR':
        # Goalkeeper: Defesas/90, Defesas %, Ações/com sucesso %
        defesas = player_series.get('Defesas', 0)
        defesas_per90 = (defesas * 90 / minutes) if minutes > 0 else 0

        defesas_pct = player_series.get('Defesas, %', 0)
        if isinstance(defesas_pct, str) and '%' in str(defesas_pct):
            defesas_pct = str(defesas_pct).replace('%', '')

        acoes_sucesso = player_series.get('Ações / com sucesso', 0)
        acoes_pct = player_series.get('Ações / com sucesso %', 0)
        if isinstance(acoes_pct, str) and '%' in str(acoes_pct):
            acoes_pct = str(acoes_pct).replace('%', '')

        return (
            {"name": "Saves /90", "value": f"{defesas_per90:.1f}"},
            {"name": "Save %", "value": f"{defesas_pct}%"},
            {"name": "Actions Success %", "value": f"{acoes_pct}%"}
        )

    elif position in ['DCE', 'DCD']:
        # Centre-Back: Desarmes/90, Interceptações/90, % desarmes bem sucedidos
        desarmes = player_series.get('Desarmes', 0)
        desarmes_per90 = (desarmes * 90 / minutes) if minutes > 0 else 0

        intercept = player_series.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
        intercept_per90 = (intercept * 90 / minutes) if minutes > 0 else 0

        # Calculate tackle success % (if we have both attempts and successful)
        desarmes_sucesso = player_series.get('Desarmes bem-sucedidos', desarmes)  # fallback to total
        desarmes_pct = (desarmes_sucesso / desarmes * 100) if desarmes > 0 else 0

        return (
            {"name": "Tackles /90", "value": f"{desarmes_per90:.1f}"},
            {"name": "Interceptions /90", "value": f"{intercept_per90:.1f}"},
            {"name": "Tackle Success %", "value": f"{desarmes_pct:.1f}%"}
        )

    elif position in ['DE', 'DD']:
        # Full-Back: Disputas defensivas ganhas %, Passes progressivos/90, % precisão cruzamentos
        disputas_def = player_series.get('Disputas na defesa', 0)
        disputas_def_ganhas = player_series.get('Disputas na defesa ganhas', 0)
        disputas_pct = (disputas_def_ganhas / disputas_def * 100) if disputas_def > 0 else 0

        passes_prog = player_series.get('Passes progressivos', 0)
        passes_prog_per90 = (passes_prog * 90 / minutes) if minutes > 0 else 0

        cruzamentos = player_series.get('Cruzamentos', 0)
        cruzamentos_precisos = player_series.get('Cruzamentos precisos', 0)
        cruzamentos_pct = (cruzamentos_precisos / cruzamentos * 100) if cruzamentos > 0 else 0

        return (
            {"name": "Def. Duels Won %", "value": f"{disputas_pct:.1f}%"},
            {"name": "Prog. Passes /90", "value": f"{passes_prog_per90:.1f}"},
            {"name": "Cross Accuracy %", "value": f"{cruzamentos_pct:.1f}%"}
        )

    elif position == 'MCD':
        # Defensive Midfielder: Disputas defensivas ganhas %, Interceptações/90, Passes progressivos/90
        disputas_def = player_series.get('Disputas na defesa', 0)
        disputas_def_ganhas = player_series.get('Disputas na defesa ganhas', 0)
        disputas_pct = (disputas_def_ganhas / disputas_def * 100) if disputas_def > 0 else 0

        intercept = player_series.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
        intercept_per90 = (intercept * 90 / minutes) if minutes > 0 else 0

        passes_prog = player_series.get('Passes progressivos', 0)
        passes_prog_per90 = (passes_prog * 90 / minutes) if minutes > 0 else 0

        return (
            {"name": "Def. Duels Won %", "value": f"{disputas_pct:.1f}%"},
            {"name": "Interceptions /90", "value": f"{intercept_per90:.1f}"},
            {"name": "Prog. Passes /90", "value": f"{passes_prog_per90:.1f}"}
        )

    elif position == 'MC':
        # Central Midfielder: Disputas defensivas ganhas %, Interceptações/90, Passes progressivos/90
        disputas_def = player_series.get('Disputas na defesa', 0)
        disputas_def_ganhas = player_series.get('Disputas na defesa ganhas', 0)
        disputas_pct = (disputas_def_ganhas / disputas_def * 100) if disputas_def > 0 else 0

        intercept = player_series.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
        intercept_per90 = (intercept * 90 / minutes) if minutes > 0 else 0

        passes_prog = player_series.get('Passes progressivos', 0)
        passes_prog_per90 = (passes_prog * 90 / minutes) if minutes > 0 else 0

        return (
            {"name": "Def. Duels Won %", "value": f"{disputas_pct:.1f}%"},
            {"name": "Interceptions /90", "value": f"{intercept_per90:.1f}"},
            {"name": "Prog. Passes /90", "value": f"{passes_prog_per90:.1f}"}
        )

    elif position in ['EE', 'ED']:
        # Winger: Dribles último terço sucesso %, Cruzamentos/90, xA
        dribles_ultimo_terco = player_series.get('Dribles no último terço do campo com sucesso', 0)
        # Calculate percentage (need total attempts)
        dribles_ultimo_total = player_series.get('Dribles no último terço do campo', dribles_ultimo_terco)
        dribles_pct = (dribles_ultimo_terco / dribles_ultimo_total * 100) if dribles_ultimo_total > 0 else 0

        cruzamentos = player_series.get('Cruzamentos', 0)
        cruzamentos_per90 = (cruzamentos * 90 / minutes) if minutes > 0 else 0

        xa = player_series.get('xA', 0)

        return (
            {"name": "Final 3rd Dribbles %", "value": f"{dribles_pct:.1f}%"},
            {"name": "Crosses /90", "value": f"{cruzamentos_per90:.1f}"},
            {"name": "xA", "value": f"{xa:.2f}"}
        )

    elif position == 'PL':
        # Forward: Gols/90, xG, Chutes no gol %
        gols = player_series.get('Gols', 0)
        gols_per90 = (gols * 90 / minutes) if minutes > 0 else 0

        xg = player_series.get('xG', 0)

        chutes_total = player_series.get('Chutes', 0)
        chutes_gol = player_series.get('Chutes no gol', 0)
        chutes_pct = (chutes_gol / chutes_total * 100) if chutes_total > 0 else 0

        return (
            {"name": "Goals /90", "value": f"{gols_per90:.2f}"},
            {"name": "xG", "value": f"{xg:.2f}"},
            {"name": "Shots on Target %", "value": f"{chutes_pct:.1f}%"}
        )

    else:
        # Fallback to original stats
        return (
            {"name": "Minutes", "value": player_data.get('minutes', 0)},
            {"name": "Goals", "value": player_data.get('goals', 0)},
            {"name": "Assists", "value": player_data.get('assists', 0)}
        )


def show_detailed_stats(analysis: dict):
    """Display detailed team statistics (UPDATED - removed Performance Overview)"""
    st.subheader("📊 Detailed Statistics")

    if not analysis or not analysis.get('starters'):
        st.warning("No statistics available")
        return

    # Position breakdown (ordered as requested)
    st.markdown("**Players by Position**")

    # Define position order
    position_order = ["GR", "DCE", "DCD", "DE", "DD", "MCD", "MC", "EE", "ED", "PL"]
    all_positions = set(list(analysis.get('starters', {}).keys()) + list(analysis.get('subs', {}).keys()))

    # Filter and order positions
    ordered_positions = [pos for pos in position_order if pos in all_positions]

    position_stats = {}
    for pos in ordered_positions:
        starters_count = len(analysis['starters'].get(pos, []))
        subs_count = len(analysis['subs'].get(pos, []))
        position_stats[pos] = {
            'Starters': starters_count,
            'Substitutes': subs_count,
            'Total': starters_count + subs_count
        }

    # Create stats table
    if position_stats:
        stats_df = pd.DataFrame.from_dict(position_stats, orient='index')
        stats_df = stats_df.reset_index()
        stats_df.columns = ['Position', 'Starters', 'Substitutes', 'Total']
        st.dataframe(stats_df, use_container_width=True)

    st.markdown("---")

    # Age distribution (ordered)
    st.markdown("**Age Analysis**")

    ages_by_position = {}
    for pos in ordered_positions:
        ages = []

        # Get ages from starters
        if pos in analysis.get('starters', {}):
            starters_df = analysis['starters'][pos]
            if 'Idade' in starters_df.columns:
                ages.extend(starters_df['Idade'].dropna().tolist())

        # Get ages from subs
        if pos in analysis.get('subs', {}):
            subs_df = analysis['subs'][pos]
            if 'Idade' in subs_df.columns:
                ages.extend(subs_df['Idade'].dropna().tolist())

        if ages:
            ages_by_position[pos] = {
                'Average Age': round(sum(ages) / len(ages), 1),
                'Youngest': min(ages),
                'Oldest': max(ages),
                'Players': len(ages)
            }

    if ages_by_position:
        age_df = pd.DataFrame.from_dict(ages_by_position, orient='index')
        age_df = age_df.reset_index()
        age_df.columns = ['Position', 'Average Age', 'Youngest', 'Oldest', 'Players']
        st.dataframe(age_df, use_container_width=True)
    else:
        st.info("No age data available")

