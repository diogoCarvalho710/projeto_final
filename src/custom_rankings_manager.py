import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class CustomRankingsManager:
    """Manager for creating and managing custom ranking systems"""

    def __init__(self, data_processor, ranking_system):
        self.data_processor = data_processor
        self.ranking_system = ranking_system
        self.rankings_file = Path("data/temp/custom_rankings.json")
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """Ensure data directory exists"""
        self.rankings_file.parent.mkdir(parents=True, exist_ok=True)

    def load_custom_rankings(self) -> Dict:
        """Load custom rankings from file"""
        if self.rankings_file.exists():
            try:
                with open(self.rankings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading custom rankings: {str(e)}")
        return {}

    def save_custom_rankings(self, rankings: Dict):
        """Save custom rankings to file"""
        try:
            with open(self.rankings_file, 'w', encoding='utf-8') as f:
                json.dump(rankings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving custom rankings: {str(e)}")
            return False

    def get_available_metrics(self, position: str) -> List[str]:
        """Get available metrics for a position"""
        if position not in self.data_processor.dataframes:
            return []

        df = self.data_processor.dataframes[position]
        exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                        'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                        'Index', 'Position_File']

        available = []
        for col in df.columns:
            if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col]):
                available.append(col)

        return sorted(available)

    def create_ranking_ui_updated(self, position: str):
        """Updated UI for creating custom rankings"""
        st.subheader(f"🏆 Create Custom Ranking for {position}")

        # Ranking name
        ranking_name = st.text_input(
            "Ranking Name",
            placeholder="e.g., Complete Midfielder Assessment",
            key=f"ranking_name_{position}"
        )

        if not ranking_name:
            st.info("👆 Enter a ranking name to continue")
            return

        # Description
        description = st.text_area(
            "Description",
            placeholder="Describe what this ranking evaluates...",
            key=f"ranking_desc_{position}"
        )

        # Get available metrics
        available_metrics = self.get_available_metrics(position)

        if not available_metrics:
            st.error(f"No numeric metrics available for {position}")
            return

        # Number of metrics
        num_metrics = st.slider(
            "Number of Variables",
            min_value=3,
            max_value=10,
            value=5,
            key=f"num_metrics_{position}"
        )

        st.markdown("### 🔧 Ranking Metrics & Weights")

        # Metrics selection
        metrics = []
        weights_sum = 0

        for i in range(num_metrics):
            st.markdown(f"**Variable {i + 1}**")

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                metric = st.selectbox(
                    f"Variable {i + 1}",
                    available_metrics,
                    key=f"ranking_metric_{position}_{i}",
                    index=i if i < len(available_metrics) else 0
                )

            with col2:
                weight = st.number_input(
                    "Weight %",
                    min_value=1,
                    max_value=100,
                    value=20,
                    key=f"ranking_weight_{position}_{i}"
                )

            with col3:
                direction = st.selectbox(
                    "Direction",
                    ["Higher is better", "Lower is better"],
                    key=f"ranking_direction_{position}_{i}"
                )

            metrics.append({
                'metric': metric,
                'weight': weight,
                'direction': 'positive' if direction == "Higher is better" else 'negative'
            })

            weights_sum += weight

        # Weight validation
        if weights_sum != 100:
            st.warning(f"⚠️ Weights sum to {weights_sum}%. Should sum to 100%.")

        # Age filtering (simplified - just min/max)
        st.markdown("### 🎂 Age Filtering")
        col1, col2 = st.columns(2)

        with col1:
            min_age = st.number_input(
                "Minimum Age",
                min_value=16,
                max_value=40,
                value=18,
                key=f"min_age_{position}"
            )

        with col2:
            max_age = st.number_input(
                "Maximum Age",
                min_value=16,
                max_value=40,
                value=35,
                key=f"max_age_{position}"
            )

        # Create ranking
        if weights_sum == 100 and st.button(f"Create Ranking", key=f"create_ranking_{position}"):
            self.create_custom_ranking(ranking_name, description, position, metrics, min_age, max_age)

    def create_custom_ranking(self, name: str, description: str, position: str,
                              metrics: List[Dict], min_age: int, max_age: int):
        """Create and save custom ranking"""
        try:
            # Load existing rankings
            custom_rankings = self.load_custom_rankings()

            # Create ranking ID
            ranking_id = f"{position}_{name.lower().replace(' ', '_')}"

            # Create ranking definition
            ranking_def = {
                'name': name,
                'description': description,
                'position': position,
                'metrics': metrics,
                'age_filter': {
                    'min_age': min_age,
                    'max_age': max_age
                },
                'created_at': pd.Timestamp.now().isoformat()
            }

            # Save ranking
            custom_rankings[ranking_id] = ranking_def

            if self.save_custom_rankings(custom_rankings):
                st.success(f"✅ Custom ranking '{name}' created successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save custom ranking")

        except Exception as e:
            st.error(f"Error creating ranking: {str(e)}")

    def show_manage_rankings_ui(self):
        """Show manage rankings UI"""
        st.subheader("🏆 Manage Custom Rankings")

        custom_rankings = self.load_custom_rankings()

        if not custom_rankings:
            st.info("📭 No custom rankings created yet. Create one in the 'Create Ranking' tab.")
            return

        # Group by position
        rankings_by_position = {}
        for ranking_id, ranking_def in custom_rankings.items():
            position = ranking_def['position']
            if position not in rankings_by_position:
                rankings_by_position[position] = {}
            rankings_by_position[position][ranking_id] = ranking_def

        # Show rankings by position
        for position, position_rankings in rankings_by_position.items():
            st.markdown(f"### 📍 {position} Rankings")

            for ranking_id, ranking_def in position_rankings.items():
                with st.expander(f"🏆 {ranking_def['name']}", expanded=False):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Description:** {ranking_def.get('description', 'No description')}")

                        st.markdown("**Variables:**")
                        for metric in ranking_def['metrics']:
                            direction_icon = "📈" if metric['direction'] == 'positive' else "📉"
                            st.markdown(f"• {metric['metric']}: {metric['weight']}% {direction_icon}")

                        age_filter = ranking_def.get('age_filter', {})
                        if age_filter:
                            st.markdown(
                                f"**Age Range:** {age_filter.get('min_age', 18)}-{age_filter.get('max_age', 35)} years")

                        st.caption(f"Created: {ranking_def.get('created_at', 'Unknown')}")

                    with col2:
                        if st.button(f"🔍 Use Ranking", key=f"use_{ranking_id}"):
                            st.session_state[f"active_custom_ranking_{position}"] = ranking_id
                            st.success(f"Now using {ranking_def['name']}")

                        if st.button(f"🗑️ Delete", key=f"delete_ranking_{ranking_id}"):
                            if self.delete_ranking(ranking_id):
                                st.success(f"Deleted {ranking_def['name']}")
                                st.rerun()

                st.markdown("---")

    def delete_ranking(self, ranking_id: str) -> bool:
        """Delete a custom ranking"""
        try:
            custom_rankings = self.load_custom_rankings()
            if ranking_id in custom_rankings:
                del custom_rankings[ranking_id]
                return self.save_custom_rankings(custom_rankings)
            return False
        except Exception as e:
            st.error(f"Error deleting ranking: {str(e)}")
            return False

    def calculate_custom_ranking_score(self, df: pd.DataFrame, ranking_def: Dict) -> pd.DataFrame:
        """Calculate custom ranking scores for a dataframe"""
        try:
            result_df = df.copy()
            scores = pd.Series(0.0, index=df.index)

            for metric_def in ranking_def['metrics']:
                metric_name = metric_def['metric']
                weight = metric_def['weight'] / 100
                direction = metric_def['direction']

                if metric_name in df.columns:
                    values = pd.to_numeric(df[metric_name], errors='coerce').fillna(0)

                    # Normalize to 0-100 scale using percentiles
                    if len(values) > 1:
                        percentiles = values.rank(pct=True) * 100
                    else:
                        percentiles = pd.Series(50.0, index=values.index)

                    # Apply direction
                    if direction == 'negative':
                        percentiles = 100 - percentiles

                    # Apply weight
                    scores += percentiles * weight

            result_df['Custom_Ranking_Score'] = scores.round(2)

            # Apply age filter if specified
            age_filter = ranking_def.get('age_filter', {})
            if age_filter and 'Idade' in result_df.columns:
                min_age = age_filter.get('min_age', 0)
                max_age = age_filter.get('max_age', 100)
                result_df = result_df[
                    (result_df['Idade'] >= min_age) &
                    (result_df['Idade'] <= max_age)
                    ]

            # Sort by score
            result_df = result_df.sort_values('Custom_Ranking_Score', ascending=False)

            return result_df

        except Exception as e:
            st.error(f"Error calculating custom ranking: {str(e)}")
            return df

    def get_custom_ranking_for_position(self, position: str) -> Optional[Dict]:
        """Get active custom ranking for a position"""
        active_ranking_key = f"active_custom_ranking_{position}"

        if active_ranking_key in st.session_state:
            ranking_id = st.session_state[active_ranking_key]
            custom_rankings = self.load_custom_rankings()
            return custom_rankings.get(ranking_id)

        return None

    def get_ranking_templates(self) -> Dict:
        """Get predefined ranking templates"""
        return {
            'complete_midfielder': {
                'name': 'Complete Midfielder',
                'category': 'Midfield',
                'description': 'Evaluates all aspects of midfield play',
                'positions': ['MC', 'MCD'],
                'metrics': [
                    {'metric': 'Passes precisos', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Passes chave', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Desarmes', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Bolas recuperadas', 'weight': 15, 'direction': 'positive'},
                    {'metric': 'Assistências', 'weight': 10, 'direction': 'positive'},
                    {'metric': 'Gols', 'weight': 10, 'direction': 'positive'}
                ]
            },
            'modern_fullback': {
                'name': 'Modern Full-Back',
                'category': 'Defense',
                'description': 'Evaluates both defensive and attacking contributions',
                'positions': ['DE', 'DD'],
                'metrics': [
                    {'metric': 'Desarmes', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Cruzamentos precisos', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'weight': 20,
                     'direction': 'positive'},
                    {'metric': 'Passes chave', 'weight': 15, 'direction': 'positive'},
                    {'metric': 'Dribles bem-sucedidos', 'weight': 10, 'direction': 'positive'},
                    {'metric': 'Assistências', 'weight': 10, 'direction': 'positive'}
                ]
            },
            'clinical_striker': {
                'name': 'Clinical Striker',
                'category': 'Attack',
                'description': 'Focuses on goalscoring and finishing ability',
                'positions': ['PL'],
                'metrics': [
                    {'metric': 'Gols', 'weight': 35, 'direction': 'positive'},
                    {'metric': 'xG', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Chutes no gol', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Toques na área', 'weight': 10, 'direction': 'positive'},
                    {'metric': 'Assistências', 'weight': 10, 'direction': 'positive'}
                ]
            },
            'defensive_rock': {
                'name': 'Defensive Rock',
                'category': 'Defense',
                'description': 'Pure defensive solidity and reliability',
                'positions': ['DCE', 'DCD'],
                'metrics': [
                    {'metric': 'Desarmes', 'weight': 30, 'direction': 'positive'},
                    {'metric': 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'weight': 25,
                     'direction': 'positive'},
                    {'metric': 'Disputas aéreas ganhas', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Passes precisos', 'weight': 15, 'direction': 'positive'},
                    {'metric': 'Faltas', 'weight': 10, 'direction': 'negative'}
                ]
            },
            'creative_winger': {
                'name': 'Creative Winger',
                'category': 'Attack',
                'description': 'Evaluates creativity and wing play effectiveness',
                'positions': ['EE', 'ED'],
                'metrics': [
                    {'metric': 'Dribles bem-sucedidos', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Cruzamentos precisos', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Passes chave', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'xA', 'weight': 15, 'direction': 'positive'},
                    {'metric': 'Assistências', 'weight': 15, 'direction': 'positive'}
                ]
            }
        }

    def apply_ranking_template(self, template_id: str, position: str) -> bool:
        """Apply a ranking template"""
        templates = self.get_ranking_templates()

        if template_id not in templates:
            return False

        template = templates[template_id]
        available_metrics = self.get_available_metrics(position)

        # Check if template is applicable to position
        if template.get('positions') != ['all'] and position not in template.get('positions', []):
            st.warning(f"{template['name']} is not designed for {position} position")

        # Check if all required metrics are available
        valid_metrics = []
        for metric in template['metrics']:
            if metric['metric'] in available_metrics:
                valid_metrics.append(metric)

        if not valid_metrics:
            st.error(f"No compatible metrics found for {template['name']} in {position}")
            return False

        # Adjust weights if some metrics are missing
        if len(valid_metrics) < len(template['metrics']):
            total_weight = sum(metric['weight'] for metric in valid_metrics)
            for metric in valid_metrics:
                metric['weight'] = int((metric['weight'] / total_weight) * 100)

        # Create the ranking
        ranking_name = f"{template['name']} ({position})"
        self.create_custom_ranking(
            ranking_name,
            template['description'],
            position,
            valid_metrics,
            18,  # default min age
            35  # default max age
        )
        return True

    def export_rankings_config(self) -> Optional[str]:
        """Export rankings configuration as JSON"""
        try:
            custom_rankings = self.load_custom_rankings()
            if custom_rankings:
                export_data = {
                    'export_type': 'custom_rankings',
                    'version': '1.0',
                    'rankings': custom_rankings
                }
                return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting rankings: {str(e)}")
        return None

    def import_rankings_config(self, json_data: str) -> bool:
        """Import rankings configuration from JSON"""
        try:
            import_data = json.loads(json_data)

            if 'rankings' not in import_data:
                st.error("Invalid rankings file format")
                return False

            # Load existing rankings
            existing_rankings = self.load_custom_rankings()

            # Merge imported rankings
            imported_count = 0
            for ranking_id, ranking_def in import_data['rankings'].items():
                existing_rankings[ranking_id] = ranking_def
                imported_count += 1

            # Save merged rankings
            if self.save_custom_rankings(existing_rankings):
                st.success(f"Imported {imported_count} custom rankings")
                return True
            else:
                st.error("Failed to save imported rankings")
                return False

        except Exception as e:
            st.error(f"Error importing rankings: {str(e)}")
            return False

    def get_ranking_info(self, position: str) -> Optional[Dict]:
        """Get ranking information for display"""
        # First check for active custom ranking
        custom_ranking = self.get_custom_ranking_for_position(position)
        if custom_ranking:
            return {
                'name': f"Custom: {custom_ranking['name']}",
                'description': custom_ranking['description'],
                'metrics': [(m['metric'], m['weight'] / 100, 1 if m['direction'] == 'positive' else -1)
                            for m in custom_ranking['metrics']],
                'is_custom': True
            }

        # Fall back to default ranking system
        return self.ranking_system.get_ranking_description(position)