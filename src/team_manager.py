import pandas as pd
from typing import Dict, List, Tuple


class TeamManager:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def get_squad_analysis(self, team: str) -> Dict:
        """Get complete squad analysis for team"""
        team_players = self.data_processor.get_team_players(team)

        if not team_players:
            return {}

        analysis = {
            'starters': {},
            'subs': {},
            'stats': self._calculate_team_stats(team_players)
        }

        # Classify players by position
        for pos, df in team_players.items():
            starters, subs = self._classify_players(df, pos)
            analysis['starters'][pos] = starters
            analysis['subs'][pos] = subs

        return analysis

    def _classify_players(self, df: pd.DataFrame, position: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Classify players as starters or substitutes"""
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Sort by minutes played (descending)
        df_sorted = df.sort_values('Minutos jogados', ascending=False)

        # Define starters based on position
        starter_count = self._get_starter_count(position)

        starters = df_sorted.head(starter_count)
        subs = df_sorted.tail(len(df_sorted) - starter_count)

        return starters, subs

    def _get_starter_count(self, position: str) -> int:
        """Get number of typical starters by position"""
        starter_counts = {
            'GR': 1,
            'DCE': 1, 'DCD': 1,
            'DE': 1, 'DD': 1,
            'EE': 1, 'ED': 1,
            'MCD': 1, 'MC': 2,
            'PL': 1
        }
        return starter_counts.get(position, 1)

    def _calculate_team_stats(self, team_players: Dict) -> Dict:
        """Calculate team statistics"""
        total_players = sum(len(df) for df in team_players.values())

        # Calculate ages
        ages = []
        total_minutes = 0

        for df in team_players.values():
            if 'Idade' in df.columns:
                ages.extend(df['Idade'].dropna().tolist())
            if 'Minutos jogados' in df.columns:
                total_minutes += df['Minutos jogados'].sum()

        return {
            'total_players': total_players,
            'average_age': round(sum(ages) / len(ages), 1) if ages else 0,
            'total_minutes': total_minutes,
            'positions': len(team_players)
        }

    def get_player_card_data(self, player: pd.Series, is_starter: bool) -> Dict:
        """Get formatted data for player card"""
        return {
            'name': player.get('Jogador', 'Unknown'),
            'age': player.get('Idade', 'N/A'),
            'minutes': int(player.get('Minutos jogados', 0)),
            'matches': int(player.get('Partidas jogadas', 0)),
            'goals': int(player.get('Gols', 0)),
            'assists': int(player.get('Assistências', 0)),
            'is_starter': is_starter,
            'position_file': player.get('Position_File', ''),
            'nationality': player.get('Nacionalidade', 'N/A'),
            'foot': player.get('Pé', 'N/A')
        }

    def get_formation_data(self, team: str) -> Dict:
        """Get formation data for tactical view"""
        analysis = self.get_squad_analysis(team)

        formation = {
            'GK': [],
            'DEF': [],
            'MID': [],
            'ATT': []
        }

        # Group positions by tactical lines
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