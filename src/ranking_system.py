import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class RankingSystem:
    """System for creating rankings and calculating percentiles"""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.position_rankings = self._initialize_position_rankings()

    def _initialize_position_rankings(self) -> Dict:
        """Initialize pre-defined rankings for each position"""
        return {
            'GR': {
                'name': 'Goalkeeper Performance',
                'description': 'Overall goalkeeper rating based on saves, distribution and goals conceded',
                'metrics': [
                    ('Defesas', 0.30, 'higher'),  # More saves = better
                    ('Defesas, %', 0.25, 'higher'),  # Higher save percentage = better
                    ('Passes', 0.20, 'higher'),  # More passes = better distribution
                    ('Passes precisos', 0.15, 'higher'),  # More accurate passes = better
                    ('Gols sofridos', -0.10, 'lower')  # Fewer goals conceded = better
                ]
            },
            'DCE': {
                'name': 'Centre-Back Performance',
                'description': 'Defensive solidity with passing ability',
                'metrics': [
                    ('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0.25, 'higher'),
                    ('Passes', 0.20, 'higher'),
                    ('Passes precisos', 0.20, 'higher'),
                    ('Desarmes', 0.15, 'higher'),
                    ('Disputas aéreas', 0.10, 'higher'),
                    ('Faltas', -0.10, 'lower')  # Fewer fouls = better
                ]
            },
            'DCD': {
                'name': 'Centre-Back Performance',
                'description': 'Defensive solidity with passing ability',
                'metrics': [
                    ('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0.25, 'higher'),
                    ('Passes', 0.20, 'higher'),
                    ('Passes precisos', 0.20, 'higher'),
                    ('Desarmes', 0.15, 'higher'),
                    ('Disputas aéreas', 0.10, 'higher'),
                    ('Faltas', -0.10, 'lower')
                ]
            },
            'DE': {
                'name': 'Left-Back Performance',
                'description': 'Attacking contribution with defensive stability',
                'metrics': [
                    ('Passes chave', 0.25, 'higher'),
                    ('Cruzamentos precisos', 0.25, 'higher'),
                    ('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0.20, 'higher'),
                    ('Dribles bem-sucedidos', 0.15, 'higher'),
                    ('Passes precisos', 0.15, 'higher')
                ]
            },
            'DD': {
                'name': 'Right-Back Performance',
                'description': 'Attacking contribution with defensive stability',
                'metrics': [
                    ('Passes chave', 0.25, 'higher'),
                    ('Cruzamentos precisos', 0.25, 'higher'),
                    ('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0.20, 'higher'),
                    ('Dribles bem-sucedidos', 0.15, 'higher'),
                    ('Passes precisos', 0.15, 'higher')
                ]
            },
            'MCD': {
                'name': 'Defensive Midfielder Performance',
                'description': 'Ball recovery and defensive contribution',
                'metrics': [
                    ('Bolas recuperadas', 0.25, 'higher'),
                    ('Desarmes', 0.25, 'higher'),
                    ('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0.20, 'higher'),
                    ('Passes progressivos', 0.20, 'higher'),
                    ('Passes precisos', 0.10, 'higher')
                ]
            },
            'MC': {
                'name': 'Central Midfielder Performance',
                'description': 'Creativity and passing ability',
                'metrics': [
                    ('Passes', 0.25, 'higher'),
                    ('Passes chave', 0.20, 'higher'),
                    ('xA', 0.20, 'higher'),
                    ('Passes precisos', 0.15, 'higher'),
                    ('Dribles bem-sucedidos', 0.10, 'higher'),
                    ('Participação em ataques de pontuação', 0.10, 'higher')
                ]
            },
            'EE': {
                'name': 'Left Winger Performance',
                'description': 'Dribbling, crossing and goal threat',
                'metrics': [
                    ('Dribles bem-sucedidos', 0.30, 'higher'),
                    ('Cruzamentos precisos', 0.25, 'higher'),
                    ('xA', 0.15, 'higher'),
                    ('xG', 0.15, 'higher'),
                    ('Passes chave', 0.15, 'higher')
                ]
            },
            'ED': {
                'name': 'Right Winger Performance',
                'description': 'Dribbling, crossing and goal threat',
                'metrics': [
                    ('Dribles bem-sucedidos', 0.30, 'higher'),
                    ('Cruzamentos precisos', 0.25, 'higher'),
                    ('xA', 0.15, 'higher'),
                    ('xG', 0.15, 'higher'),
                    ('Passes chave', 0.15, 'higher')
                ]
            },
            'PL': {
                'name': 'Forward Performance',
                'description': 'Goal scoring and attacking threat',
                'metrics': [
                    ('Gols', 0.25, 'higher'),
                    ('xG', 0.25, 'higher'),
                    ('Chutes no gol', 0.20, 'higher'),
                    ('Toques na área', 0.15, 'higher'),
                    ('Dribles bem-sucedidos', 0.15, 'higher')
                ]
            }
        }

    def calculate_percentiles(self, df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
        """Calculate percentiles for given metrics"""

        result_df = df.copy()

        for metric in metrics:
            if metric in df.columns:
                # Convert to numeric, handle errors
                values = pd.to_numeric(df[metric], errors='coerce')

                # Calculate percentile rank (0-100)
                percentiles = values.rank(pct=True) * 100

                # Handle NaN values
                percentiles = percentiles.fillna(0)

                # Store percentile
                result_df[f'{metric}_percentile'] = percentiles.round(1)
            else:
                # If metric doesn't exist, set to 0
                result_df[f'{metric}_percentile'] = 0

        return result_df

    def calculate_position_score(self, df: pd.DataFrame, position: str) -> pd.DataFrame:
        """Calculate overall position score based on pre-defined weights"""

        if position not in self.position_rankings:
            return df

        ranking_config = self.position_rankings[position]
        metrics_config = ranking_config['metrics']

        # Extract metrics and weights
        metrics = [metric[0] for metric in metrics_config]
        weights = [metric[1] for metric in metrics_config]
        directions = [metric[2] for metric in metrics_config]

        # Calculate percentiles for all metrics
        df_with_percentiles = self.calculate_percentiles(df, metrics)

        # Calculate weighted score
        total_score = pd.Series(0.0, index=df.index)
        total_weight = 0

        for i, (metric, weight, direction) in enumerate(metrics_config):
            percentile_col = f'{metric}_percentile'

            if percentile_col in df_with_percentiles.columns:
                # For negative weights (like fouls, goals conceded), invert the percentile
                if weight < 0:
                    contribution = (100 - df_with_percentiles[percentile_col]) * abs(weight)
                else:
                    contribution = df_with_percentiles[percentile_col] * weight

                total_score += contribution
                total_weight += abs(weight)

        # Normalize to 0-100 scale
        if total_weight > 0:
            df_with_percentiles['Overall_Score'] = (total_score / total_weight).round(1)
        else:
            df_with_percentiles['Overall_Score'] = 0

        # Sort by overall score
        df_with_percentiles = df_with_percentiles.sort_values('Overall_Score', ascending=False)

        return df_with_percentiles

    def get_top_players_by_position(self, position: str, limit: int = 20,
                                    min_minutes: int = 500, exclude_team: str = None) -> pd.DataFrame:
        """Get top players for a specific position"""

        if position not in self.data_processor.dataframes:
            return pd.DataFrame()

        # Get position dataframe
        df = self.data_processor.dataframes[position].copy()

        # Apply filters
        if 'Minutos jogados' in df.columns:
            df = df[df['Minutos jogados'] >= min_minutes]

        if exclude_team and 'Time' in df.columns:
            df = df[df['Time'] != exclude_team]

        if df.empty:
            return pd.DataFrame()

        # Calculate scores
        df_scored = self.calculate_position_score(df, position)

        return df_scored.head(limit)

    def get_player_percentiles(self, player_name: str, position: str) -> Dict:
        """Get percentiles for a specific player"""

        if position not in self.data_processor.dataframes:
            return {}

        df = self.data_processor.dataframes[position].copy()
        player_data = df[df['Jogador'] == player_name]

        if player_data.empty:
            return {}

        # Get ranking configuration
        if position not in self.position_rankings:
            return {}

        ranking_config = self.position_rankings[position]
        metrics = [metric[0] for metric in ranking_config['metrics']]

        # Calculate percentiles for entire position
        df_with_percentiles = self.calculate_percentiles(df, metrics)

        # Get player's percentiles
        player_percentiles = df_with_percentiles[df_with_percentiles['Jogador'] == player_name]

        if player_percentiles.empty:
            return {}

        result = {}
        for metric in metrics:
            percentile_col = f'{metric}_percentile'
            if percentile_col in player_percentiles.columns:
                result[metric] = player_percentiles[percentile_col].iloc[0]

        return result

    def filter_players(self, position: str = None, min_age: int = None, max_age: int = None,
                       min_minutes: int = None, nationality: str = None,
                       exclude_team: str = None) -> pd.DataFrame:
        """Filter players based on various criteria"""

        if position and position in self.data_processor.dataframes:
            # Filter specific position
            df = self.data_processor.dataframes[position].copy()
            df['Position_File'] = position
        else:
            # Get all players
            df = self.data_processor.get_all_players()

        if df.empty:
            return df

        # Apply filters
        if min_age and 'Idade' in df.columns:
            df = df[df['Idade'] >= min_age]

        if max_age and 'Idade' in df.columns:
            df = df[df['Idade'] <= max_age]

        if min_minutes and 'Minutos jogados' in df.columns:
            df = df[df['Minutos jogados'] >= min_minutes]

        if nationality and 'Nacionalidade' in df.columns:
            df = df[df['Nacionalidade'] == nationality]

        if exclude_team and 'Time' in df.columns:
            df = df[df['Time'] != exclude_team]

        return df

    def search_players(self, name_query: str, position: str = None) -> pd.DataFrame:
        """Search players by name"""

        if position and position in self.data_processor.dataframes:
            df = self.data_processor.dataframes[position].copy()
            df['Position_File'] = position
        else:
            df = self.data_processor.get_all_players()

        if df.empty:
            return df

        # Case-insensitive search
        mask = df['Jogador'].str.contains(name_query, case=False, na=False)
        return df[mask]

    def get_available_nationalities(self) -> List[str]:
        """Get list of all available nationalities"""

        all_players = self.data_processor.get_all_players()
        if 'Nacionalidade' in all_players.columns:
            nationalities = all_players['Nacionalidade'].dropna().unique()
            return sorted(nationalities.tolist())
        return []

    def get_ranking_description(self, position: str) -> Dict:
        """Get ranking description for a position"""

        if position in self.position_rankings:
            return self.position_rankings[position]
        return {}

    def compare_players(self, players_data: List[Dict], position: str) -> pd.DataFrame:
        """Compare multiple players with percentiles"""

        if not players_data or position not in self.data_processor.dataframes:
            return pd.DataFrame()

        # Get position dataframe for percentile calculation
        position_df = self.data_processor.dataframes[position].copy()

        # Get ranking metrics
        if position not in self.position_rankings:
            return pd.DataFrame()

        ranking_config = self.position_rankings[position]
        metrics = [metric[0] for metric in ranking_config['metrics']]

        # Calculate percentiles for entire position
        df_with_percentiles = self.calculate_percentiles(position_df, metrics)

        # Extract comparison data
        comparison_data = []

        for player_info in players_data:
            player_name = player_info['name']
            player_row = df_with_percentiles[df_with_percentiles['Jogador'] == player_name]

            if not player_row.empty:
                player_data = {
                    'Player': player_name,
                    'Age': player_row['Idade'].iloc[0] if 'Idade' in player_row.columns else 'N/A',
                    'Team': player_row['Time'].iloc[0] if 'Time' in player_row.columns else 'N/A',
                    'Minutes': player_row['Minutos jogados'].iloc[0] if 'Minutos jogados' in player_row.columns else 0
                }

                # Add metric values and percentiles
                for metric in metrics:
                    if metric in player_row.columns:
                        player_data[f'{metric}_value'] = player_row[metric].iloc[0]

                    percentile_col = f'{metric}_percentile'
                    if percentile_col in player_row.columns:
                        player_data[f'{metric}_percentile'] = player_row[percentile_col].iloc[0]

                comparison_data.append(player_data)

        return pd.DataFrame(comparison_data)