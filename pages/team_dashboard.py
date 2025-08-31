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

    # Position order for display
    position_order = ["GR", "DCE", "DCD", "DE", "DD", "EE", "ED", "MCD", "MC", "PL"]
    position_names = {
        "GR": "🥅 Goalkeepers",
        "DCE": "🛡️ Centre-Backs (Left)",
        "DCD": "🛡️ Centre-Backs (Right)",
        "DE": "⬅️ Left-Backs",
        "DD": "➡️ Right-Backs",
        "EE": "⬅️ Left Wingers",
        "ED": "➡️ Right Wingers",
        "MCD": "🛡️ Defensive Midfielders",
        "MC": "⚽ Central Midfielders",
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
                    show_player_card(player_data, f"{position}_{i}_{j}")


def show_player_card(player_data: dict, unique_id: str = ""):
    """Display individual player card with clickable name"""

    status_icon = "🟢" if player_data['is_starter'] else "⚪"

    # Create unique key
    card_key = f"player_{unique_id}_{player_data['name']}_{player_data['minutes']}"

    with st.container():
        # Player header with clickable name
        col1, col2 = st.columns([3, 1])
        with col1:
            # Make player name clickable
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

        with col2:
            if st.button("👁️", key=f"view_{card_key}", help="View Profile"):
                # Store player info for profile page
                st.session_state.selected_player = {
                    'name': player_data['name'],
                    'position': player_data['position_file']
                }
                st.session_state.show_player_profile = True
                st.rerun()

        # Player stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Minutes", player_data['minutes'])
        with col2:
            st.metric("Goals", player_data['goals'])
        with col3:
            st.metric("Assists", player_data['assists'])

        # Additional info
        st.caption(f"👣 {player_data['foot']} foot")

        # Add subtle separator
        st.markdown("---")


def show_detailed_stats(analysis: dict):
    """Display detailed team statistics"""
    st.subheader("📊 Detailed Statistics")

    if not analysis or not analysis.get('starters'):
        st.warning("No statistics available")
        return

    # Position breakdown
    st.markdown("**Players by Position**")

    position_stats = {}
    all_positions = set(list(analysis.get('starters', {}).keys()) + list(analysis.get('subs', {}).keys()))

    for pos in all_positions:
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

    # Age distribution
    st.markdown("**Age Analysis**")

    ages_by_position = {}
    for pos in all_positions:
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

    st.markdown("---")

    # Performance summary
    st.markdown("**Performance Overview**")

    total_goals = 0
    total_assists = 0
    total_matches = 0

    for pos in all_positions:
        # Count from starters
        if pos in analysis.get('starters', {}):
            df = analysis['starters'][pos]
            if 'Gols' in df.columns:
                total_goals += df['Gols'].sum()
            if 'Assistências' in df.columns:
                total_assists += df['Assistências'].sum()
            if 'Partidas jogadas' in df.columns:
                total_matches += df['Partidas jogadas'].sum()

        # Count from subs
        if pos in analysis.get('subs', {}):
            df = analysis['subs'][pos]
            if 'Gols' in df.columns:
                total_goals += df['Gols'].sum()
            if 'Assistências' in df.columns:
                total_assists += df['Assistências'].sum()
            if 'Partidas jogadas' in df.columns:
                total_matches += df['Partidas jogadas'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Goals", int(total_goals))
    with col2:
        st.metric("Total Assists", int(total_assists))
    with col3:
        st.metric("Total Matches", int(total_matches))