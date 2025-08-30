import streamlit as st
import pandas as pd


def show_team_dashboard():
    """Display team dashboard with squad overview"""
    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    # Use inline team manager to avoid import issues
    team_manager = BasicTeamManager(st.session_state.data_processor)
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

    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📋 Squad List", "⚽ Formation", "📊 Statistics"])

    with tab1:
        show_squad_list(analysis, team_manager)

    with tab2:
        show_formation_view(team_manager, team)

    with tab3:
        show_detailed_stats(analysis)


class BasicTeamManager:
    """Simple team manager without complex imports"""

    def __init__(self, data_processor):
        self.data_processor = data_processor

    def get_squad_analysis(self, team: str):
        """Get basic squad analysis"""
        team_players = self.data_processor.get_team_players(team)

        if not team_players:
            return {}

        analysis = {'starters': {}, 'subs': {}, 'stats': {}}

        # Basic stats
        total_players = sum(len(df) for df in team_players.values())
        ages = []
        total_minutes = 0

        for df in team_players.values():
            if 'Idade' in df.columns:
                ages.extend(df['Idade'].dropna().tolist())
            if 'Minutos jogados' in df.columns:
                total_minutes += df['Minutos jogados'].sum()

        analysis['stats'] = {
            'total_players': total_players,
            'average_age': round(sum(ages) / len(ages), 1) if ages else 0,
            'total_minutes': total_minutes,
            'positions': len(team_players)
        }

        # Simple classification
        for pos, df in team_players.items():
            if not df.empty:
                df_sorted = df.sort_values('Minutos jogados', ascending=False)
                # First player is starter, rest are subs
                analysis['starters'][pos] = df_sorted.head(1)
                analysis['subs'][pos] = df_sorted.tail(len(df_sorted) - 1)

        return analysis

    def get_player_card_data(self, player, is_starter: bool):
        """Get basic player card data"""
        return {
            'name': player.get('Jogador', 'Unknown'),
            'age': player.get('Idade', 'N/A'),
            'minutes': int(player.get('Minutos jogados', 0)),
            'goals': int(player.get('Gols', 0)),
            'assists': int(player.get('Assistências', 0)),
            'is_starter': is_starter,
            'position_file': player.get('Position_File', ''),
            'nationality': player.get('Nacionalidade', 'N/A'),
            'foot': player.get('Pé', 'N/A')
        }

    def get_formation_data(self, team: str):
        """Get simple formation data"""
        analysis = self.get_squad_analysis(team)
        formation = {'GK': [], 'DEF': [], 'MID': [], 'ATT': []}

        # Group positions
        position_groups = {
            'GK': ['GR'],
            'DEF': ['DCE', 'DCD', 'DE', 'DD'],
            'MID': ['EE', 'ED', 'MCD', 'MC'],
            'ATT': ['PL']
        }

        for line, positions in position_groups.items():
            for pos in positions:
                if pos in analysis.get('starters', {}):
                    starters_df = analysis['starters'][pos]
                    for _, player in starters_df.iterrows():
                        formation[line].append(self.get_player_card_data(player, True))

        return formation


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
                show_position_players(analysis['starters'][pos], team_manager, True)

            # Show substitutes
            if pos in analysis['subs'] and not analysis['subs'][pos].empty:
                st.markdown("**⚪ Substitutes**")
                show_position_players(analysis['subs'][pos], team_manager, False)

            st.divider()


def show_position_players(df, team_manager, is_starter: bool):
    """Display players for a specific position"""

    # Show players in rows of 3
    players_per_row = 3
    players_list = df.to_dict('records')

    for i in range(0, len(players_list), players_per_row):
        cols = st.columns(players_per_row)

        for j, col in enumerate(cols):
            if i + j < len(players_list):
                player = players_list[i + j]
                player_data = team_manager.get_player_card_data(pd.Series(player), is_starter)

                with col:
                    show_player_card(player_data, f"{i}_{j}")


def show_player_card(player_data: dict, unique_id: str = ""):
    """Display individual player card"""

    # Card styling
    border_color = "#28a745" if player_data['is_starter'] else "#6c757d"
    status_icon = "🟢" if player_data['is_starter'] else "⚪"

    # Create unique key using position + unique_id + minutes to avoid duplicates
    card_key = f"player_{player_data['position_file']}_{unique_id}_{player_data['minutes']}"

    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: rgba(255,255,255,0.05);
            cursor: pointer;
        ">
        """, unsafe_allow_html=True)

        # Player header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{status_icon} {player_data['name']}**")
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
        st.caption(f"👣 {player_data['foot']} foot | {player_data['nationality']}")

        st.markdown("</div>", unsafe_allow_html=True)


def show_formation_view(team_manager, team: str):
    """Display simple formation view without field"""
    st.subheader("⚽ Starting XI")

    formation_data = team_manager.get_formation_data(team)

    # Simple formation display without field visualization
    formation_order = [('🥅 Goalkeeper', 'GK'), ('🛡️ Defense', 'DEF'), ('⚽ Midfield', 'MID'), ('🎯 Attack', 'ATT')]

    for line_name, line_key in formation_order:
        if line_key in formation_data and formation_data[line_key]:
            st.markdown(f"**{line_name}**")

            players = formation_data[line_key]
            cols = st.columns(len(players))

            for i, player in enumerate(players):
                with cols[i]:
                    show_simple_formation_card(player, f"{line_key}_{i}")

            st.markdown("---")


def show_simple_formation_card(player_data: dict, unique_id: str):
    """Display simple player card for formation view"""

    st.markdown(f"""
    <div style="
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 10px;
        margin: 5px auto;
        text-align: center;
        background-color: rgba(40, 167, 69, 0.1);
        max-width: 150px;
    ">
        <div style="font-weight: bold; color: #ffffff; margin-bottom: 5px;">
            {player_data.get('name', 'Unknown')}
        </div>
        <div style="color: #cccccc; font-size: 0.85em;">
            {player_data.get('age', 'N/A')} | {player_data.get('minutes', 0)} min
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add view button with unique key
    button_key = f"formation_view_{unique_id}_{player_data.get('minutes', 0)}"
    if st.button("View", key=button_key, help=f"View {player_data.get('name')} profile"):
        st.session_state.selected_player = {
            'name': player_data.get('name'),
            'position': player_data.get('position_file')
        }
        st.session_state.show_player_profile = True
        st.rerun()


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


# Import pandas for the stats function
import pandas as pd