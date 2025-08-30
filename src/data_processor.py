import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import io
from .config import POSITIONS_ORDER, METRICS_PER_90


class DataProcessor:
    def __init__(self, uploaded_files):
        self.dataframes = {}
        self.positions_order = POSITIONS_ORDER
        self._load_data(uploaded_files)
        self._process_data()

    def _load_data(self, uploaded_files):
        # Load CSV files with cp1252 encoding
        for file in uploaded_files:
            try:
                # Extract position from filename
                filename = file.name
                for pos in self.positions_order:
                    if pos in filename:
                        # Read with cp1252 encoding
                        content = file.getvalue().decode('cp1252')
                        df = pd.read_csv(io.StringIO(content))
                        self.dataframes[pos] = df
                        break
            except Exception as e:
                print(f"Error loading {file.name}: {str(e)}")

    def _process_data(self):
        # Clean and process data
        for pos, df in self.dataframes.items():
            # Basic cleaning
            df = df.dropna(subset=['Jogador'])

            # Remove duplicates
            if all(col in df.columns for col in ['Jogador', 'Minutos jogados', 'Idade']):
                df = df.drop_duplicates(subset=['Jogador', 'Minutos jogados', 'Idade'])

            # Convert numeric columns more carefully
            for col in df.columns:
                if col not in ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                               'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada']:
                    # Try to convert to numeric
                    try:
                        # Handle percentage strings like "72%"
                        if df[col].dtype == 'object':
                            # First convert to string and handle percentages
                            df[col] = df[col].astype(str)

                            # Remove % symbol if present
                            df[col] = df[col].str.replace('%', '')

                            # Handle European decimal format (comma to dot)
                            df[col] = df[col].str.replace(',', '.')

                            # Replace 'nan' strings with actual NaN
                            df[col] = df[col].replace('nan', np.nan)

                        # Convert to numeric
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                        # Fill NaN with 0 for numeric columns
                        df[col] = df[col].fillna(0)

                    except Exception as e:
                        # If conversion fails, leave as is
                        print(f"Could not convert column {col} in {pos}: {e}")
                        continue

            # Calculate per 90 metrics
            if 'Minutos jogados' in df.columns:
                minutes_played = df['Minutos jogados'].replace(0, 1)  # Avoid division by zero

                for metric in METRICS_PER_90:
                    if metric in df.columns:
                        # Ensure both metric and minutes are numeric
                        try:
                            metric_values = pd.to_numeric(df[metric], errors='coerce').fillna(0)
                            df[f'{metric}_per90'] = (metric_values * 90 / minutes_played).round(2)
                        except Exception as e:
                            print(f"Could not calculate per90 for {metric} in {pos}: {e}")
                            continue

            self.dataframes[pos] = df

    def get_teams(self) -> List[str]:
        # Get list of all teams
        teams = set()
        for df in self.dataframes.values():
            if 'Time' in df.columns:
                teams.update(df['Time'].dropna().unique())
        return sorted(list(teams))

    def get_team_players(self, team: str) -> Dict[str, pd.DataFrame]:
        # Get players by position for specific team
        team_players = {}
        for pos in self.positions_order:
            if pos in self.dataframes:
                df = self.dataframes[pos]
                if 'Time' in df.columns:
                    team_df = df[df['Time'] == team].copy()
                    if not team_df.empty:
                        team_players[pos] = team_df
        return team_players

    def get_player_data(self, player_name: str, position: str) -> Optional[pd.Series]:
        # Get specific player data
        if position in self.dataframes:
            df = self.dataframes[position]
            player_data = df[df['Jogador'] == player_name]
            if not player_data.empty:
                return player_data.iloc[0]
        return None

    def get_all_players(self) -> pd.DataFrame:
        # Get all players from all positions
        all_players = []
        for pos, df in self.dataframes.items():
            df_copy = df.copy()
            df_copy['Position_File'] = pos
            all_players.append(df_copy)

        if all_players:
            return pd.concat(all_players, ignore_index=True)
        return pd.DataFrame()

    def get_numeric_columns(self, position: str) -> List[str]:
        """Get list of numeric columns for a position"""
        if position in self.dataframes:
            df = self.dataframes[position]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            return numeric_cols
        return []