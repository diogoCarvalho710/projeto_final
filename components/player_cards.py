import streamlit as st


class PlayerCard:
    """Component for displaying player cards"""

    @staticmethod
    def show_basic_card(player_data: dict, key_suffix: str = ""):
        """Display basic player card"""

        border_color = "#28a745" if player_data.get('is_starter') else "#6c757d"
        status_icon = "🟢" if player_data.get('is_starter') else "⚪"

        card_html = f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <h4 style="margin: 0; color: #ffffff;">{status_icon} {player_data.get('name', 'Unknown')}</h4>
                    <small style="color: #cccccc;">Age: {player_data.get('age', 'N/A')} | {player_data.get('nationality', 'N/A')}</small>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: #ffffff;">{player_data.get('minutes', 0)}</div>
                    <small style="color: #cccccc;">Minutes</small>
                </div>
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: #ffffff;">{player_data.get('goals', 0)}</div>
                    <small style="color: #cccccc;">Goals</small>
                </div>
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: #ffffff;">{player_data.get('assists', 0)}</div>
                    <small style="color: #cccccc;">Assists</small>
                </div>
            </div>

            <div style="text-align: center; color: #cccccc; font-size: 0.85em;">
                💰 {player_data.get('market_value', 'N/A')} | 👣 {player_data.get('foot', 'N/A')} foot
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Add clickable button
        button_key = f"view_player_{player_data.get('name', '')}_{key_suffix}"
        if st.button(f"👁️ View {player_data.get('name', 'Player')} Profile", key=button_key):
            st.session_state.selected_player = {
                'name': player_data.get('name'),
                'position': player_data.get('position_file')
            }
            st.session_state.show_player_profile = True
            st.rerun()

    @staticmethod
    def show_compact_card(player_data: dict, key_suffix: str = ""):
        """Display compact player card for formation view"""

        card_html = f"""
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
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Add view button
        button_key = f"view_formation_{player_data.get('name', '')}_{key_suffix}"
        if st.button("View Profile", key=button_key, help=f"View {player_data.get('name')} profile"):
            st.session_state.selected_player = {
                'name': player_data.get('name'),
                'position': player_data.get('position_file')
            }
            st.session_state.show_player_profile = True
            st.rerun()

    @staticmethod
    def show_stats_card(player_data: dict, stats: dict = None):
        """Display player card with additional statistics"""

        if not stats:
            stats = {}

        border_color = "#28a745" if player_data.get('is_starter') else "#6c757d"
        status_icon = "🟢" if player_data.get('is_starter') else "⚪"

        card_html = f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 15px;
            background-color: rgba(255,255,255,0.05);
            margin-bottom: 15px;
        ">
            <div style="margin-bottom: 15px;">
                <h3 style="margin: 0; color: #ffffff;">{status_icon} {player_data.get('name', 'Unknown')}</h3>
                <p style="margin: 5px 0; color: #cccccc;">
                    {player_data.get('age', 'N/A')} years | {player_data.get('nationality', 'N/A')} | 
                    {player_data.get('height', 'N/A')} | {player_data.get('foot', 'N/A')} foot
                </p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px;">
        """

        # Basic stats
        basic_stats = [
            ('Minutes', player_data.get('minutes', 0)),
            ('Matches', player_data.get('matches', 0)),
            ('Goals', player_data.get('goals', 0)),
            ('Assists', player_data.get('assists', 0))
        ]

        for stat_name, stat_value in basic_stats:
            card_html += f"""
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: #ffffff; font-size: 1.2em;">{stat_value}</div>
                    <small style="color: #cccccc;">{stat_name}</small>
                </div>
            """

        # Additional stats if provided
        for stat_name, stat_value in stats.items():
            card_html += f"""
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: #ffffff; font-size: 1.2em;">{stat_value}</div>
                    <small style="color: #cccccc;">{stat_name}</small>
                </div>
            """

        card_html += f"""
            </div>

            <div style="margin-top: 15px; text-align: center; color: #cccccc;">
                💰 Market Value: {player_data.get('market_value', 'N/A')}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)


class PlayerCardGrid:
    """Component for displaying grids of player cards"""

    @staticmethod
    def show_position_grid(players_data: list, players_per_row: int = 3, card_type: str = "basic"):
        """Display players in a grid layout"""

        for i in range(0, len(players_data), players_per_row):
            cols = st.columns(players_per_row)

            for j, col in enumerate(cols):
                if i + j < len(players_data):
                    player_data = players_data[i + j]

                    with col:
                        if card_type == "compact":
                            PlayerCard.show_compact_card(player_data, f"grid_{i}_{j}")
                        else:
                            PlayerCard.show_basic_card(player_data, f"grid_{i}_{j}")

    @staticmethod
    def show_comparison_grid(players_data: list, max_players: int = 4):
        """Display players for comparison"""

        if len(players_data) > max_players:
            players_data = players_data[:max_players]

        cols = st.columns(len(players_data))

        for i, (col, player_data) in enumerate(zip(cols, players_data)):
            with col:
                PlayerCard.show_basic_card(player_data, f"comp_{i}")


# CSS Styling for cards
CARD_CSS = """
<style>
.player-card {
    transition: transform 0.2s ease-in-out;
    cursor: pointer;
}

.player-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.starter-card {
    border-color: #28a745 !important;
}

.substitute-card {
    border-color: #6c757d !important;
}

.compact-card {
    max-width: 150px;
    margin: 0 auto;
}
</style>
"""