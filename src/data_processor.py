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
        self._remove_duplicates()  # New step to handle cross-position duplicates

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

    def _remove_duplicates(self):
        """Remove duplicate players across positions, keeping the one with most minutes"""

        # Create a combined dataframe with all players and their positions
        all_players = []

        for pos, df in self.dataframes.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['Position_File'] = pos
                all_players.append(df_copy)

        if not all_players:
            return

        # Combine all data
        combined_df = pd.concat(all_players, ignore_index=True)

        # Create more robust duplicate detection
        # Use name + age + nationality if birth date not available
        duplicate_columns = ['Jogador']

        # Add additional columns for better duplicate detection
        if 'Data de nascimento' in combined_df.columns:
            # Check if birth date column has meaningful data
            birth_date_not_null = combined_df['Data de nascimento'].notna().sum()
            if birth_date_not_null > len(combined_df) * 0.5:  # If >50% have birth dates
                duplicate_columns.append('Data de nascimento')
                print(f"Using birth date for duplicate detection ({birth_date_not_null} records have birth dates)")
            else:
                # Fallback to age + nationality
                if 'Idade' in combined_df.columns:
                    duplicate_columns.append('Idade')
                if 'Nacionalidade' in combined_df.columns:
                    duplicate_columns.append('Nacionalidade')
                print(
                    f"Birth date sparse ({birth_date_not_null} records), using age + nationality for duplicate detection")
        else:
            # No birth date column, use age + nationality
            if 'Idade' in combined_df.columns:
                duplicate_columns.append('Idade')
            if 'Nacionalidade' in combined_df.columns:
                duplicate_columns.append('Nacionalidade')
            print("No birth date column found, using age + nationality for duplicate detection")

        print(f"Duplicate detection using columns: {duplicate_columns}")

        # Find duplicates using the selected columns
        duplicates = combined_df.duplicated(subset=duplicate_columns, keep=False)
        duplicate_players = combined_df[duplicates].copy()

        if duplicate_players.empty:
            print("No duplicate players found across positions")
            return

        print(f"Found {len(duplicate_players)} duplicate records across positions")

        # For each duplicate group, keep only the one with most minutes
        players_to_remove = []

        # Group duplicates by the duplicate columns
        for _, group in duplicate_players.groupby(duplicate_columns):
            if len(group) > 1:
                # Sort by minutes played (descending) and keep only the first one
                sorted_records = group.sort_values('Minutos jogados', ascending=False)

                # Records to remove (all except the first one)
                records_to_remove = sorted_records.iloc[1:]

                for _, record in records_to_remove.iterrows():
                    players_to_remove.append({
                        'name': record['Jogador'],
                        'position': record['Position_File'],
                        'minutes': record['Minutos jogados'],
                        'age': record.get('Idade', 'N/A'),
                        'nationality': record.get('Nacionalidade', 'N/A')
                    })

                # Log the decision
                kept_record = sorted_records.iloc[0]
                removed_positions = [r['Position_File'] for r in records_to_remove.to_dict('records')]

                print(
                    f"Player '{kept_record['Jogador']}' (Age: {kept_record.get('Idade', 'N/A')}, {kept_record.get('Nacionalidade', 'N/A')}): "
                    f"Keeping {kept_record['Position_File']} ({kept_record['Minutos jogados']} min), "
                    f"removing from {', '.join(removed_positions)}")

        # Remove the duplicate players from their respective dataframes
        for player_info in players_to_remove:
            pos = player_info['position']
            name = player_info['name']
            age = player_info['age']
            nationality = player_info['nationality']

            if pos in self.dataframes:
                # More precise removal - match by name, age, and nationality to avoid removing wrong player
                original_count = len(self.dataframes[pos])

                # Create mask for more precise matching
                mask = (self.dataframes[pos]['Jogador'] == name)

                # Add age filter if available
                if 'Idade' in self.dataframes[pos].columns and pd.notna(age) and age != 'N/A':
                    mask = mask & (self.dataframes[pos]['Idade'] == age)

                # Add nationality filter if available
                if 'Nacionalidade' in self.dataframes[pos].columns and pd.notna(nationality) and nationality != 'N/A':
                    mask = mask & (self.dataframes[pos]['Nacionalidade'] == nationality)

                # Remove matching records
                self.dataframes[pos] = self.dataframes[pos][~mask]
                removed_count = original_count - len(self.dataframes[pos])

                if removed_count > 0:
                    print(f"Removed {removed_count} duplicate(s) of '{name}' from {pos}")

        # Final summary
        total_players_after = sum(len(df) for df in self.dataframes.values())
        print(f"Deduplication complete. Total players after cleanup: {total_players_after}")

        # Double-check for remaining duplicates by name only
        remaining_combined = []
        for pos, df in self.dataframes.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['Position_File'] = pos
                remaining_combined.append(df_copy)

        if remaining_combined:
            remaining_df = pd.concat(remaining_combined, ignore_index=True)
            name_counts = remaining_df['Jogador'].value_counts()
            still_duplicated = name_counts[name_counts > 1]

            if len(still_duplicated) > 0:
                print(f"⚠️  Warning: {len(still_duplicated)} players still appear in multiple positions:")
                for name, count in still_duplicated.items():
                    positions = remaining_df[remaining_df['Jogador'] == name]['Position_File'].tolist()
                    print(f"  - {name}: {positions}")
            else:
                print("✅ No remaining duplicates found!")

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

    def get_duplicate_analysis(self) -> Dict:
        """Get analysis of duplicate players for debugging"""

        # Create combined dataframe
        all_players = []
        for pos, df in self.dataframes.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['Position_File'] = pos
                all_players.append(df_copy)

        if not all_players:
            return {"total_players": 0, "duplicates": []}

        combined_df = pd.concat(all_players, ignore_index=True)

        # Find duplicates by name only (to catch all potential cases)
        name_counts = combined_df['Jogador'].value_counts()
        potential_duplicates = name_counts[name_counts > 1]

        duplicate_info = []
        for name, count in potential_duplicates.items():
            player_records = combined_df[combined_df['Jogador'] == name]

            records_info = []
            for _, record in player_records.iterrows():
                records_info.append({
                    'position': record['Position_File'],
                    'minutes': record.get('Minutos jogados', 0),
                    'birth_date': record.get('Data de nascimento', 'N/A'),
                    'age': record.get('Idade', 'N/A'),
                    'nationality': record.get('Nacionalidade', 'N/A'),
                    'team': record.get('Time', 'N/A')
                })

            # Check if these are likely the same person
            ages = [r['age'] for r in records_info if r['age'] != 'N/A']
            nationalities = [r['nationality'] for r in records_info if r['nationality'] != 'N/A']

            # Determine if likely duplicate
            same_age = len(set(ages)) <= 1 if ages else True
            same_nationality = len(set(nationalities)) <= 1 if nationalities else True
            likely_duplicate = same_age and same_nationality

            duplicate_info.append({
                'name': name,
                'count': count,
                'records': records_info,
                'likely_duplicate': likely_duplicate,
                'max_minutes': max(r['minutes'] for r in records_info),
                'positions': [r['position'] for r in records_info]
            })

        # Sort by likelihood of being duplicates and number of occurrences
        duplicate_info.sort(key=lambda x: (x['likely_duplicate'], x['count']), reverse=True)

        return {
            "total_players": len(combined_df),
            "unique_names": len(combined_df['Jogador'].unique()),
            "potential_duplicates": len(potential_duplicates),
            "duplicates": duplicate_info
        }