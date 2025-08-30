import streamlit as st
import pandas as pd
from typing import List, Dict, Optional


class ComparisonManager:
    """Manages player comparison functionality"""

    def __init__(self, data_processor, ranking_system):
        self.data_processor = data_processor
        self.ranking_system = ranking_system

    def add_player(self, player_name: str, position: str, df: pd.DataFrame = None) -> bool:
        """Add player to comparison list"""

        # Initialize comparison list if not exists
        if 'comparison_players' not in st.session_state:
            st.session_state.comparison_players = []

        # Check if already in comparison
        for existing in st.session_state.comparison_players:
            if existing['name'] == player_name and existing['position'] == position:
                st.warning(f"⚠️ {player_name} already in comparison!")
                return False

        # Limit to 5 players max
        if len(st.session_state.comparison_players) >= 5:
            st.warning("⚠️ Maximum 5 players in comparison!")
            return False

        # Get player data
        if df is not None:
            player_data = df[df['Jogador'] == player_name]
        else:
            # Get from data processor
            if position in self.data_processor.dataframes:
                position_df = self.data_processor.dataframes[position]
                player_data = position_df[position_df['Jogador'] == player_name]
            else:
                st.error(f"Position {position} not found!")
                return False

        if player_data.empty:
            st.error(f"Player {player_name} not found!")
            return False

        # Extract player info
        player_info = {
            'name': player_name,
            'position': position,
            'team': player_data['Time'].iloc[0],
            'age': int(player_data['Idade'].iloc[0]),
            'minutes': int(player_data['Minutos jogados'].iloc[0]),
            'overall_score': float(
                player_data.get('Overall_Score', 0).iloc[0]) if 'Overall_Score' in player_data.columns else 0.0
        }

        st.session_state.comparison_players.append(player_info)
        st.success(f"✅ {player_name} added to comparison!")
        return True

    def remove_player(self, index: int) -> bool:
        """Remove player from comparison list"""

        if 'comparison_players' not in st.session_state:
            return False

        if 0 <= index < len(st.session_state.comparison_players):
            removed_player = st.session_state.comparison_players.pop(index)
            st.success(f"✅ {removed_player['name']} removed from comparison")
            return True
        return False

    def clear_all(self) -> None:
        """Clear all players from comparison"""
        st.session_state.comparison_players = []
        st.success("🗑️ All players removed from comparison")

    def get_comparison_players(self) -> List[Dict]:
        """Get current comparison players list"""
        return st.session_state.get('comparison_players', [])

    def get_comparison_count(self) -> int:
        """Get number of players in comparison"""
        return len(st.session_state.get('comparison_players', []))

    def get_comparison_data(self) -> pd.DataFrame:
        """Get detailed comparison data for all players"""

        comparison_players = self.get_comparison_players()
        if not comparison_players:
            return pd.DataFrame()

        table_data = []

        for player_info in comparison_players:
            # Get full player data
            if player_info['position'] in self.data_processor.dataframes:
                position_df = self.data_processor.dataframes[player_info['position']]
                player_row = position_df[position_df['Jogador'] == player_info['name']]

                if not player_row.empty:
                    player_stats = {
                        'Player': player_info['name'],
                        'Position': player_info['position'],
                        'Team': player_info['team'],
                        'Age': player_info['age'],
                        'Minutes': player_info['minutes'],
                        'Overall Score': player_info['overall_score']
                    }

                    # Add key metrics based on position
                    ranking_info = self.ranking_system.get_ranking_description(player_info['position'])
                    if ranking_info:
                        for metric, weight, direction in ranking_info['metrics']:
                            if metric in player_row.columns:
                                value = player_row[metric].iloc[0]
                                player_stats[metric] = value

                    table_data.append(player_stats)

        return pd.DataFrame(table_data) if table_data else pd.DataFrame()

    def get_radar_data(self) -> List[Dict]:
        """Get radar chart data for comparison players"""

        comparison_players = self.get_comparison_players()
        if not comparison_players:
            return []

        # Use first player's position for metrics (or find most common position)
        main_position = comparison_players[0]['position']

        # Get ranking info for metrics
        ranking_info = self.ranking_system.get_ranking_description(main_position)
        if not ranking_info:
            return []

        metrics = [metric[0] for metric in ranking_info['metrics']]

        # Prepare data for radar chart
        players_data = []

        for player_info in comparison_players:
            # Get full player data
            if player_info['position'] in self.data_processor.dataframes:
                position_df = self.data_processor.dataframes[player_info['position']]
                player_row = position_df[position_df['Jogador'] == player_info['name']]

                if not player_row.empty:
                    # Calculate percentiles for this player
                    df_with_percentiles = self.ranking_system.calculate_percentiles(position_df, metrics)
                    player_percentiles = df_with_percentiles[df_with_percentiles['Jogador'] == player_info['name']]

                    if not player_percentiles.empty:
                        player_data = {'Player': player_info['name']}
                        for metric in metrics:
                            percentile_col = f'{metric}_percentile'
                            if percentile_col in player_percentiles.columns:
                                player_data[percentile_col] = player_percentiles[percentile_col].iloc[0]

                        players_data.append(player_data)

        return players_data

    def get_percentiles_data(self) -> Dict[str, Dict]:
        """Get percentiles data for all comparison players"""

        comparison_players = self.get_comparison_players()
        percentiles_data = {}

        for player_info in comparison_players:
            percentiles = self.ranking_system.get_player_percentiles(
                player_info['name'],
                player_info['position']
            )

            if percentiles:
                percentiles_data[player_info['name']] = {
                    'percentiles': percentiles,
                    'position': player_info['position'],
                    'team': player_info['team'],
                    'age': player_info['age']
                }

        return percentiles_data

    def export_comparison_csv(self) -> Optional[str]:
        """Export comparison data as CSV"""

        comparison_df = self.get_comparison_data()
        if comparison_df.empty:
            return None

        return comparison_df.to_csv(index=False)

    def get_comparison_summary_stats(self) -> Dict:
        """Get summary statistics for comparison players"""

        comparison_players = self.get_comparison_players()
        if not comparison_players:
            return {}

        ages = [p['age'] for p in comparison_players]
        minutes = [p['minutes'] for p in comparison_players]
        scores = [p['overall_score'] for p in comparison_players if p['overall_score'] > 0]

        teams = list(set([p['team'] for p in comparison_players]))
        positions = list(set([p['position'] for p in comparison_players]))

        return {
            'count': len(comparison_players),
            'avg_age': sum(ages) / len(ages) if ages else 0,
            'avg_minutes': sum(minutes) / len(minutes) if minutes else 0,
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'teams_count': len(teams),
            'positions_count': len(positions),
            'teams': teams,
            'positions': positions
        }

    def find_similar_players(self, player_name: str, position: str, limit: int = 5) -> List[Dict]:
        """Find players similar to the given player"""

        if position not in self.data_processor.dataframes:
            return []

        position_df = self.data_processor.dataframes[position]
        target_player = position_df[position_df['Jogador'] == player_name]

        if target_player.empty:
            return []

        # Get ranking metrics for position
        ranking_info = self.ranking_system.get_ranking_description(position)
        if not ranking_info:
            return []

        metrics = [metric[0] for metric in ranking_info['metrics']]

        # Calculate similarity based on key metrics
        similarities = []
        target_values = {}

        # Get target player values
        for metric in metrics:
            if metric in target_player.columns:
                target_values[metric] = pd.to_numeric(target_player[metric].iloc[0], errors='coerce')

        # Compare with all other players
        for _, player in position_df.iterrows():
            if player['Jogador'] == player_name:
                continue

            similarity_score = 0
            valid_metrics = 0

            for metric in metrics:
                if metric in target_values and metric in player.index:
                    target_val = target_values[metric]
                    player_val = pd.to_numeric(player[metric], errors='coerce')

                    if pd.notna(target_val) and pd.notna(player_val):
                        # Calculate normalized difference (lower = more similar)
                        if target_val != 0:
                            diff = abs(target_val - player_val) / abs(target_val)
                        else:
                            diff = abs(player_val)

                        similarity_score += (1 - min(diff, 1))  # Convert to similarity (higher = more similar)
                        valid_metrics += 1

            if valid_metrics > 0:
                avg_similarity = similarity_score / valid_metrics
                similarities.append({
                    'name': player['Jogador'],
                    'team': player['Time'],
                    'age': int(player['Idade']),
                    'minutes': int(player['Minutos jogados']),
                    'similarity': avg_similarity
                })

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]

    def batch_add_similar_players(self, player_name: str, position: str, count: int = 3) -> None:
        """Add similar players to comparison automatically"""

        similar_players = self.find_similar_players(player_name, position,
                                                    count + 5)  # Get more to account for already added players

        added_count = 0
        for similar in similar_players:
            if added_count >= count:
                break

            # Check if player is already in comparison
            already_added = False
            for existing in st.session_state.get('comparison_players', []):
                if existing['name'] == similar['name']:
                    already_added = True
                    break

            if not already_added and self.get_comparison_count() < 5:
                success = self.add_player(similar['name'], position)
                if success:
                    added_count += 1

        if added_count > 0:
            st.success(f"✅ Added {added_count} similar players to comparison")