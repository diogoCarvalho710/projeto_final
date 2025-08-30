import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime


class CustomRankingsManager:
    """Manages custom ranking systems and templates"""

    def __init__(self, data_processor, ranking_system):
        self.data_processor = data_processor
        self.ranking_system = ranking_system
        self.config_dir = Path("data/configs")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.rankings_file = self.config_dir / "custom_rankings.json"

    def create_ranking_ui(self, position: str) -> Optional[Dict]:
        """Show UI for creating custom rankings"""

        st.subheader("🏆 Create Custom Ranking")

        if not position or position not in self.data_processor.dataframes:
            # Show template options first
            self._show_ranking_templates(position)
            st.warning("Please select a position first")
            return None

        position_df = self.data_processor.dataframes[position]

        # Get available numeric metrics
        available_metrics = self._get_available_metrics(position_df)

        if not available_metrics:
            st.error("No numeric metrics available for this position")
            return None

        # Template options at the top
        self._show_ranking_templates(position)

        st.markdown("---")

        # Ranking basic info
        col1, col2 = st.columns(2)

        with col1:
            ranking_name = st.text_input(
                "📊 Ranking Name",
                placeholder="e.g., Elite Defensive Midfielders",
                help="Give your ranking system a descriptive name",
                key=f"custom_ranking_name_{position}"
            )

        with col2:
            ranking_category = st.selectbox(
                "🏷️ Category",
                ["Performance", "Potential", "Market Value", "Complete Player", "Specialized", "Custom"],
                help="Choose the category that best fits your ranking",
                key=f"custom_ranking_category_{position}"
            )

        ranking_description = st.text_area(
            "📝 Description",
            placeholder="Explain what this ranking measures and prioritizes...",
            help="Describe the focus and criteria of your ranking system",
            key=f"custom_ranking_description_{position}"
        )

        st.markdown("---")
        st.markdown("### 🔧 **Ranking Metrics & Weights**")
        st.markdown("Select metrics and their importance weights (must total 100%)")

        # Initialize session state for metrics
        metrics_key = f'custom_ranking_metrics_{position}'
        if metrics_key not in st.session_state:
            st.session_state[metrics_key] = [
                {'metric': '', 'weight': 0, 'direction': 'positive', 'min_threshold': None, 'importance': 'medium'}
            ]

        metrics_state = st.session_state[metrics_key]
        total_weight = 0

        # Show current metrics
        for i, metric_config in enumerate(metrics_state):
            st.markdown(f"**Metric {i + 1}:**")

            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

            with col1:
                selected_metric = st.selectbox(
                    "Metric",
                    [''] + available_metrics,
                    index=available_metrics.index(metric_config['metric']) + 1 if metric_config[
                                                                                      'metric'] in available_metrics else 0,
                    key=f"ranking_metric_{i}_{position}",
                    label_visibility="collapsed"
                )
                metric_config['metric'] = selected_metric

            with col2:
                weight = st.number_input(
                    "Weight %",
                    min_value=0,
                    max_value=100,
                    value=metric_config['weight'],
                    key=f"ranking_weight_{i}_{position}",
                    label_visibility="collapsed"
                )
                metric_config['weight'] = weight
                total_weight += weight

            with col3:
                direction = st.selectbox(
                    "Direction",
                    ["positive", "negative"],
                    index=0 if metric_config['direction'] == 'positive' else 1,
                    key=f"ranking_direction_{i}_{position}",
                    help="Positive: higher is better, Negative: lower is better",
                    label_visibility="collapsed"
                )
                metric_config['direction'] = direction

            with col4:
                importance = st.selectbox(
                    "Importance",
                    ["low", "medium", "high", "critical"],
                    index=["low", "medium", "high", "critical"].index(metric_config.get('importance', 'medium')),
                    key=f"ranking_importance_{i}_{position}",
                    help="How critical is this metric for the ranking?",
                    label_visibility="collapsed"
                )
                metric_config['importance'] = importance

            with col5:
                # Minimum threshold (optional)
                if selected_metric:
                    min_threshold = st.number_input(
                        "Min Value",
                        min_value=0.0,
                        value=metric_config.get('min_threshold', 0.0) or 0.0,
                        step=0.1,
                        key=f"ranking_threshold_{i}_{position}",
                        help="Minimum value required (0 = no minimum)",
                        label_visibility="collapsed"
                    )
                    metric_config['min_threshold'] = min_threshold if min_threshold > 0 else None
                else:
                    st.text_input("Min Value", disabled=True, key=f"disabled_threshold_{i}_{position}",
                                  label_visibility="collapsed")

            with col6:
                if len(metrics_state) > 1:
                    if st.button("❌", key=f"ranking_remove_{i}_{position}", help="Remove metric"):
                        metrics_state.pop(i)
                        st.rerun()
                else:
                    st.text("")  # Empty space to maintain alignment

            # Show metric preview if selected
            if selected_metric and selected_metric in position_df.columns:
                metric_values = pd.to_numeric(position_df[selected_metric], errors='coerce').dropna()
                if not metric_values.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.caption(f"Min: {metric_values.min():.2f}")
                    with col2:
                        st.caption(f"Max: {metric_values.max():.2f}")
                    with col3:
                        st.caption(f"Avg: {metric_values.mean():.2f}")
                    with col4:
                        st.caption(f"Median: {metric_values.median():.2f}")

            st.markdown("---")

        # Metric management buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add Metric", key=f"add_ranking_metric_{position}"):
                if len(metrics_state) < 10:
                    metrics_state.append({'metric': '', 'weight': 0, 'direction': 'positive',
                                          'min_threshold': None, 'importance': 'medium'})
                    st.rerun()
                else:
                    st.warning("Maximum 10 metrics allowed")

        with col2:
            if st.button("⚖️ Auto Balance Weights", key=f"auto_balance_ranking_{position}"):
                valid_metrics = [m for m in metrics_state if m['metric']]
                if valid_metrics:
                    # Weight by importance
                    importance_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                    total_importance = sum(importance_weights.get(m['importance'], 2) for m in valid_metrics)

                    for metric_config in metrics_state:
                        if metric_config['metric']:
                            importance_factor = importance_weights.get(metric_config['importance'], 2)
                            metric_config['weight'] = round((importance_factor / total_importance) * 100, 1)
                    st.rerun()

        with col3:
            if st.button("🗑️ Clear All", key=f"clear_ranking_metrics_{position}"):
                st.session_state[metrics_key] = [{'metric': '', 'weight': 0, 'direction': 'positive',
                                                  'min_threshold': None, 'importance': 'medium'}]
                st.rerun()

        # Weight validation
        if total_weight != 100 and any(m['metric'] for m in metrics_state):
            st.error(f"⚠️ Total weight must be 100%. Current: {total_weight}%")
        elif total_weight == 100:
            st.success(f"✅ Total weight: {total_weight}%")

        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                min_minutes_filter = st.number_input(
                    "Minimum Minutes Played",
                    min_value=0,
                    max_value=3000,
                    value=500,
                    step=50,
                    key=f"ranking_min_minutes_{position}",
                    help="Only include players with at least this many minutes"
                )

                age_weight_curve = st.selectbox(
                    "Age Weighting",
                    ["None", "Prefer Young (Under 25)", "Prefer Prime (25-30)", "Experience Bonus (30+)"],
                    key=f"ranking_age_weight_{position}",
                    help="Apply age-based adjustments to the ranking"
                )

            with col2:
                exclude_own_team = st.checkbox(
                    "Exclude Own Team Players",
                    value=True,
                    key=f"ranking_exclude_own_{position}",
                    help="Focus on external scouting targets"
                )

                market_value_consideration = st.selectbox(
                    "Market Value Factor",
                    ["None", "Value for Money (Lower = Better)", "Quality Premium (Higher = Better)"],
                    key=f"ranking_market_factor_{position}",
                    help="How to factor in market value"
                )

        # Preview ranking
        if ranking_name and total_weight == 100 and any(m['metric'] for m in metrics_state if m['weight'] > 0):
            st.markdown("---")
            st.markdown("### 👀 **Ranking Preview**")
            preview_data = self._calculate_ranking_preview(position_df, metrics_state, ranking_name,
                                                           min_minutes_filter, age_weight_curve,
                                                           exclude_own_team, market_value_consideration)
            if preview_data is not None:
                self._show_ranking_preview(preview_data, ranking_name)

        # Save ranking
        st.markdown("---")
        if st.button("💾 Save Custom Ranking", key=f"save_ranking_{position}"):
            if not ranking_name:
                st.error("Please enter a ranking name")
                return None

            valid_metrics = [m for m in metrics_state if m['metric'] and m['weight'] > 0]
            if not valid_metrics:
                st.error("Please select at least one metric with weight > 0")
                return None

            total_weight = sum(m['weight'] for m in valid_metrics)
            if total_weight != 100:
                st.error(f"Total weight must be 100%. Current: {total_weight}%")
                return None

            # Create ranking config
            ranking_config = {
                'name': ranking_name,
                'description': ranking_description,
                'category': ranking_category,
                'position': position,
                'metrics': valid_metrics,
                'min_minutes_filter': min_minutes_filter,
                'age_weight_curve': age_weight_curve,
                'exclude_own_team': exclude_own_team,
                'market_value_consideration': market_value_consideration,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Save ranking
            if self.save_custom_ranking(ranking_config):
                st.success(f"✅ Custom ranking '{ranking_name}' saved successfully!")
                # Clear the form
                if metrics_key in st.session_state:
                    del st.session_state[metrics_key]
                st.rerun()
            else:
                st.error("Failed to save custom ranking")

        return None

    def _show_ranking_templates(self, position: str):
        """Show ranking template options"""

        st.markdown("**🚀 Quick Start with Templates:**")

        templates = self.get_ranking_templates()
        position_templates = {k: v for k, v in templates.items()
                              if v.get('positions', [position]) == [position] or 'all' in v.get('positions', [])}

        if position_templates:
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_template = st.selectbox(
                    "Choose a template:",
                    [""] + list(position_templates.keys()),
                    format_func=lambda x: position_templates[x]['name'] if x else "Select template...",
                    key=f"ranking_template_select_{position}"
                )

            with col2:
                if selected_template and st.button("📋 Apply Template", key=f"apply_ranking_template_{position}"):
                    if position and self.apply_ranking_template(selected_template, position):
                        st.success(f"✅ Applied template: {position_templates[selected_template]['name']}")
                        st.rerun()
                    else:
                        st.error("Failed to apply template")

            # Show template description
            if selected_template:
                template_info = position_templates[selected_template]
                st.info(f"📖 **{template_info['name']}**: {template_info['description']}")

    def _get_available_metrics(self, df: pd.DataFrame) -> List[str]:
        """Get list of available numeric metrics"""

        exclude_cols = [
            'Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
            'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
            'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados'
        ]

        numeric_cols = []
        for col in df.columns:
            if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col]):
                if not col.endswith('_percentile') and col != 'Overall_Score':
                    numeric_cols.append(col)

        return sorted(numeric_cols)

    def _calculate_ranking_preview(self, df: pd.DataFrame, metrics_config: List[Dict],
                                   ranking_name: str, min_minutes: int, age_curve: str,
                                   exclude_own: bool, market_factor: str) -> Optional[pd.DataFrame]:
        """Calculate preview of custom ranking"""

        try:
            # Apply filters first
            filtered_df = df.copy()

            # Minutes filter
            if min_minutes > 0 and 'Minutos jogados' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Minutos jogados'] >= min_minutes]

            # Own team filter
            if exclude_own and 'Time' in filtered_df.columns and hasattr(st.session_state, 'selected_team'):
                filtered_df = filtered_df[filtered_df['Time'] != st.session_state.selected_team]

            if filtered_df.empty:
                st.warning("No players match the filters")
                return None

            # Calculate base score
            ranking_scores = pd.Series(0.0, index=filtered_df.index)

            for metric_config in metrics_config:
                if not metric_config['metric'] or metric_config['weight'] == 0:
                    continue

                metric_col = metric_config['metric']
                weight = metric_config['weight'] / 100
                direction = metric_config['direction']
                min_threshold = metric_config.get('min_threshold')

                if metric_col in filtered_df.columns:
                    values = pd.to_numeric(filtered_df[metric_col], errors='coerce').fillna(0)

                    # Apply minimum threshold filter
                    if min_threshold is not None:
                        mask = values >= min_threshold
                        values = values * mask  # Zero out values below threshold

                    # Calculate percentiles for normalization
                    percentiles = values.rank(pct=True) * 100

                    # Apply direction (negative means lower is better)
                    if direction == 'negative':
                        percentiles = 100 - percentiles

                    ranking_scores += percentiles * weight

            # Apply age weighting if selected
            if age_curve != "None" and 'Idade' in filtered_df.columns:
                age_multiplier = self._calculate_age_multiplier(filtered_df['Idade'], age_curve)
                ranking_scores *= age_multiplier

            # Apply market value consideration
            if market_factor != "None" and 'Valor de mercado' in filtered_df.columns:
                market_multiplier = self._calculate_market_multiplier(filtered_df['Valor de mercado'], market_factor)
                ranking_scores *= market_multiplier

            # Create preview dataframe
            preview_df = filtered_df[['Jogador', 'Time', 'Idade', 'Minutos jogados']].copy()
            preview_df[ranking_name] = ranking_scores.round(1)
            preview_df = preview_df.sort_values(ranking_name, ascending=False)

            return preview_df.head(15)  # Top 15 for preview

        except Exception as e:
            st.error(f"Error calculating ranking preview: {str(e)}")
            return None

    def _calculate_age_multiplier(self, ages: pd.Series, age_curve: str) -> pd.Series:
        """Calculate age-based multipliers"""

        multiplier = pd.Series(1.0, index=ages.index)

        if age_curve == "Prefer Young (Under 25)":
            # Bonus for young players, penalty for older
            multiplier = 1.2 - (ages - 20) * 0.02
            multiplier = multiplier.clip(lower=0.8, upper=1.2)

        elif age_curve == "Prefer Prime (25-30)":
            # Peak at 25-30, decline outside
            optimal_ages = (ages >= 25) & (ages <= 30)
            multiplier[optimal_ages] = 1.1
            multiplier[ages < 25] = 0.95 + (ages[ages < 25] - 18) * 0.02
            multiplier[ages > 30] = 1.1 - (ages[ages > 30] - 30) * 0.03
            multiplier = multiplier.clip(lower=0.7, upper=1.1)

        elif age_curve == "Experience Bonus (30+)":
            # Bonus for experienced players
            multiplier[ages >= 30] = 1.1
            multiplier[ages < 25] = 0.9

        return multiplier.fillna(1.0)

    def _calculate_market_multiplier(self, market_values: pd.Series, market_factor: str) -> pd.Series:
        """Calculate market value-based multipliers"""

        multiplier = pd.Series(1.0, index=market_values.index)

        # Convert market values to numeric (this is simplified)
        # In reality, you'd need to parse strings like "€2.5M"
        # For now, assume they're comparable

        if market_factor == "Value for Money (Lower = Better)":
            # Prefer lower market values
            multiplier = 1.1  # Simplified - would need actual value parsing

        elif market_factor == "Quality Premium (Higher = Better)":
            # Prefer higher market values
            multiplier = 1.0  # Simplified - would need actual value parsing

        return multiplier.fillna(1.0)

    def _show_ranking_preview(self, preview_df: pd.DataFrame, ranking_name: str):
        """Show preview of the custom ranking"""

        st.markdown(f"**🏆 Top 15 players by {ranking_name}:**")

        display_df = preview_df.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df = display_df[['Rank', 'Jogador', 'Time', 'Idade', 'Minutos jogados', ranking_name]]
        display_df.columns = ['Rank', 'Player', 'Team', 'Age', 'Minutes', ranking_name]

        st.dataframe(display_df, use_container_width=True)

        # Show distribution info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Top Score", f"{preview_df[ranking_name].max():.1f}")
        with col2:
            st.metric("Average", f"{preview_df[ranking_name].mean():.1f}")
        with col3:
            st.metric("Score Range", f"{preview_df[ranking_name].max() - preview_df[ranking_name].min():.1f}")

    def save_custom_ranking(self, ranking_config: Dict) -> bool:
        """Save custom ranking to JSON file"""

        try:
            existing_rankings = self.load_custom_rankings()

            ranking_id = f"{ranking_config['position']}_{ranking_config['name'].replace(' ', '_').lower()}"
            existing_rankings[ranking_id] = ranking_config

            with open(self.rankings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_rankings, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            st.error(f"Error saving custom ranking: {str(e)}")
            return False

    def load_custom_rankings(self) -> Dict:
        """Load custom rankings from JSON file"""

        if not self.rankings_file.exists():
            return {}

        try:
            with open(self.rankings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading custom rankings: {str(e)}")
            return {}

    def get_custom_rankings_by_position(self, position: str) -> Dict:
        """Get custom rankings for a specific position"""

        all_rankings = self.load_custom_rankings()
        return {k: v for k, v in all_rankings.items() if v.get('position') == position}

    def calculate_custom_ranking(self, df: pd.DataFrame, ranking_config: Dict) -> pd.DataFrame:
        """Calculate custom ranking for a dataframe"""

        try:
            # Apply filters
            filtered_df = df.copy()

            min_minutes = ranking_config.get('min_minutes_filter', 0)
            if min_minutes > 0 and 'Minutos jogados' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Minutos jogados'] >= min_minutes]

            exclude_own = ranking_config.get('exclude_own_team', False)
            if exclude_own and 'Time' in filtered_df.columns and hasattr(st.session_state, 'selected_team'):
                filtered_df = filtered_df[filtered_df['Time'] != st.session_state.selected_team]

            if filtered_df.empty:
                return pd.DataFrame()

            # Calculate ranking scores
            ranking_scores = pd.Series(0.0, index=filtered_df.index)

            for metric_config in ranking_config['metrics']:
                metric_col = metric_config['metric']
                weight = metric_config['weight'] / 100
                direction = metric_config['direction']
                min_threshold = metric_config.get('min_threshold')

                if metric_col in filtered_df.columns:
                    values = pd.to_numeric(filtered_df[metric_col], errors='coerce').fillna(0)

                    # Apply minimum threshold
                    if min_threshold is not None:
                        mask = values >= min_threshold
                        values = values * mask

                    # Calculate percentiles
                    percentiles = values.rank(pct=True) * 100

                    if direction == 'negative':
                        percentiles = 100 - percentiles

                    ranking_scores += percentiles * weight

            # Apply age and market value adjustments
            age_curve = ranking_config.get('age_weight_curve', 'None')
            if age_curve != "None" and 'Idade' in filtered_df.columns:
                age_multiplier = self._calculate_age_multiplier(filtered_df['Idade'], age_curve)
                ranking_scores *= age_multiplier

            market_factor = ranking_config.get('market_value_consideration', 'None')
            if market_factor != "None" and 'Valor de mercado' in filtered_df.columns:
                market_multiplier = self._calculate_market_multiplier(filtered_df['Valor de mercado'], market_factor)
                ranking_scores *= market_multiplier

            # Add to dataframe and sort
            result_df = filtered_df.copy()
            result_df['Custom_Ranking_Score'] = ranking_scores.round(1)
            result_df = result_df.sort_values('Custom_Ranking_Score', ascending=False)

            return result_df

        except Exception as e:
            st.error(f"Error calculating custom ranking: {str(e)}")
            return pd.DataFrame()

    def show_manage_rankings_ui(self):
        """Show UI for managing existing custom rankings"""

        st.subheader("🏆 Manage Custom Rankings")

        custom_rankings = self.load_custom_rankings()

        if not custom_rankings:
            st.info("No custom rankings created yet. Create your first ranking above!")
            return

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rankings", len(custom_rankings))
        with col2:
            positions = set(r.get('position', 'Unknown') for r in custom_rankings.values())
            st.metric("Positions", len(positions))
        with col3:
            categories = set(r.get('category', 'Unknown') for r in custom_rankings.values())
            st.metric("Categories", len(categories))

        # Filter options
        col1, col2 = st.columns(2)

        with col1:
            position_filter = st.selectbox(
                "Filter by Position",
                ["All"] + sorted(positions),
                key="rankings_position_filter"
            )

        with col2:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(categories),
                key="rankings_category_filter"
            )

        # Apply filters
        filtered_rankings = custom_rankings.copy()
        if position_filter != "All":
            filtered_rankings = {k: v for k, v in filtered_rankings.items() if v.get('position') == position_filter}
        if category_filter != "All":
            filtered_rankings = {k: v for k, v in filtered_rankings.items() if v.get('category') == category_filter}

        if not filtered_rankings:
            st.info("No rankings match the current filters")
            return

        st.markdown("---")

        # Group by position
        rankings_by_position = {}
        for ranking_id, ranking_config in filtered_rankings.items():
            position = ranking_config['position']
            if position not in rankings_by_position:
                rankings_by_position[position] = []
            rankings_by_position[position].append((ranking_id, ranking_config))

        for position, rankings in rankings_by_position.items():
            with st.expander(f"🎯 {position} Rankings ({len(rankings)})", expanded=True):

                for ranking_id, ranking_config in rankings:
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{ranking_config['name']}**")
                        st.caption(
                            f"📂 {ranking_config.get('category', 'N/A')} | 🕐 {ranking_config.get('created_date', 'Unknown')[:10]}")

                        if ranking_config.get('description'):
                            st.caption(f"📝 {ranking_config['description']}")

                        # Show metrics summary
                        metrics_summary = ", ".join([
                            f"{m['metric']} ({m['weight']}%)"
                            for m in ranking_config.get('metrics', [])
                        ])
                        if len(metrics_summary) > 100:
                            metrics_summary = metrics_summary[:100] + "..."
                        st.caption(f"📊 Metrics: {metrics_summary}")

                    with col2:
                        if st.button("🧪 Test", key=f"test_ranking_{ranking_id}", help="Test ranking on current data"):
                            self._test_custom_ranking(ranking_config)

                    with col3:
                        if st.button("▶️ Run", key=f"run_ranking_{ranking_id}", help="Run full ranking"):
                            self._run_custom_ranking(ranking_config)

                    with col4:
                        if st.button("📋 Copy", key=f"copy_ranking_{ranking_id}", help="Copy ranking for editing"):
                            self._copy_ranking_to_creator(ranking_config)

                    with col5:
                        if st.button("🗑️ Delete", key=f"delete_ranking_{ranking_id}", help="Delete ranking"):
                            if self.delete_custom_ranking(ranking_id):
                                st.success(f"Deleted {ranking_config['name']}")
                                st.rerun()

                    st.markdown("---")

    def _test_custom_ranking(self, ranking_config: Dict):
        """Test a custom ranking and show results"""

        position = ranking_config['position']
        if position not in self.data_processor.dataframes:
            st.error(f"Position {position} data not available")
            return

        df = self.data_processor.dataframes[position]
        ranked_df = self.calculate_custom_ranking(df, ranking_config)

        if ranked_df.empty:
            st.warning("No players match the ranking criteria")
            return

        st.markdown(f"**🧪 Test Results for '{ranking_config['name']}':**")

        # Show top 10 with ranking
        display_df = ranked_df.head(10)[['Jogador', 'Time', 'Idade', 'Minutos jogados', 'Custom_Ranking_Score']].copy()
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
        display_df.columns = ['Rank', 'Player', 'Team', 'Age', 'Minutes', 'Score']
        st.dataframe(display_df, use_container_width=True)

        # Show statistics
        scores = ranked_df['Custom_Ranking_Score']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Top Score", f"{scores.max():.1f}")
        with col2:
            st.metric("Average", f"{scores.mean():.1f}")
        with col3:
            st.metric("Median", f"{scores.median():.1f}")
        with col4:
            st.metric("Players", len(ranked_df))

    def _run_custom_ranking(self, ranking_config: Dict):
        """Run full custom ranking and show comprehensive results"""

        position = ranking_config['position']
        if position not in self.data_processor.dataframes:
            st.error(f"Position {position} data not available")
            return

        df = self.data_processor.dataframes[position]
        ranked_df = self.calculate_custom_ranking(df, ranking_config)

        if ranked_df.empty:
            st.warning("No players match the ranking criteria")
            return

        # Store results in session state for export
        st.session_state[f'ranking_results_{ranking_config["name"]}'] = ranked_df

        st.markdown(f"**🏆 Full Results for '{ranking_config['name']}':**")

        # Show full results table
        display_df = ranked_df[
            ['Jogador', 'Time', 'Idade', 'Minutos jogados', 'Nacionalidade', 'Custom_Ranking_Score']].copy()
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
        display_df.columns = ['Rank', 'Player', 'Team', 'Age', 'Minutes', 'Nationality', 'Score']

        st.dataframe(display_df, use_container_width=True, height=600)

        # Export options
        col1, col2 = st.columns(2)
        with col1:
            csv_data = display_df.to_csv(index=False)
            st.download_button(
                "📥 Export as CSV",
                csv_data,
                f"{ranking_config['name']}_ranking.csv",
                "text/csv",
                use_container_width=True
            )

        with col2:
            if st.button("⭐ Add Top 5 to Favorites", key=f"add_top5_{ranking_config['name']}"):
                self._add_top_players_to_favorites(ranked_df.head(5), ranking_config['name'])

    def _add_top_players_to_favorites(self, top_players_df: pd.DataFrame, ranking_name: str):
        """Add top players from ranking to favorites"""

        if 'favorites_manager' not in st.session_state:
            st.error("Favorites system not available")
            return

        favorites_manager = st.session_state.favorites_manager
        added_count = 0

        for _, player in top_players_df.iterrows():
            player_name = player['Jogador']
            position = player.get('Position_File', '')

            if not favorites_manager.is_favorite(player_name, position):
                if favorites_manager.add_to_favorites(
                        player_name,
                        position,
                        reason=f"Top performer in {ranking_name}",
                        tags=[f"ranking_{ranking_name.lower()}", "top_performer"],
                        collection=f"{ranking_name} Results"
                ):
                    added_count += 1

        if added_count > 0:
            st.success(f"Added {added_count} top players to favorites!")
        else:
            st.info("All top players are already in favorites")

    def _copy_ranking_to_creator(self, ranking_config: Dict):
        """Copy ranking configuration to the creator form"""

        position = ranking_config['position']
        metrics_key = f'custom_ranking_metrics_{position}'

        # Copy metrics to session state
        st.session_state[metrics_key] = ranking_config['metrics'].copy()

        st.success(f"📋 Copied '{ranking_config['name']}' configuration to creator. Switch to Create tab to modify.")

    def delete_custom_ranking(self, ranking_id: str) -> bool:
        """Delete a custom ranking"""

        try:
            existing_rankings = self.load_custom_rankings()

            if ranking_id in existing_rankings:
                del existing_rankings[ranking_id]

                with open(self.rankings_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_rankings, f, ensure_ascii=False, indent=2)

                return True

            return False

        except Exception as e:
            st.error(f"Error deleting custom ranking: {str(e)}")
            return False

    def get_ranking_templates(self) -> Dict:
        """Get predefined ranking templates"""

        return {
            "complete_player": {
                "name": "Complete Player Rating",
                "description": "Balanced evaluation across all key performance areas",
                "category": "Complete Player",
                "positions": ["all"],
                "metrics": [
                    {"metric": "Passes", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Passes precisos %", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Desarmes", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Interceptações", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Gols", "weight": 15, "direction": "positive", "importance": "high"},
                    {"metric": "Assistências", "weight": 10, "direction": "positive", "importance": "medium"},
                    {"metric": "Faltas", "weight": 10, "direction": "negative", "importance": "low"}
                ]
            },

            "attacking_threat": {
                "name": "Attacking Threat",
                "description": "Focus on goal scoring and creative output",
                "category": "Performance",
                "positions": ["PL", "EE", "ED", "MC"],
                "metrics": [
                    {"metric": "xG", "weight": 30, "direction": "positive", "importance": "critical"},
                    {"metric": "Gols", "weight": 25, "direction": "positive", "importance": "critical"},
                    {"metric": "xA", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Chutes no gol", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Passes chave", "weight": 10, "direction": "positive", "importance": "medium"}
                ]
            },

            "defensive_solidity": {
                "name": "Defensive Solidity",
                "description": "Comprehensive defensive performance evaluation",
                "category": "Performance",
                "positions": ["DCE", "DCD", "DE", "DD", "MCD"],
                "metrics": [
                    {"metric": "Desarmes", "weight": 25, "direction": "positive", "importance": "critical"},
                    {"metric": "Interceptações", "weight": 25, "direction": "positive", "importance": "critical"},
                    {"metric": "Disputas aéreas", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Bolas recuperadas", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Passes precisos %", "weight": 10, "direction": "positive", "importance": "medium"},
                    {"metric": "Faltas", "weight": 5, "direction": "negative", "importance": "low"}
                ]
            },

            "passing_master": {
                "name": "Passing Master",
                "description": "Exceptional passing ability and distribution",
                "category": "Specialized",
                "positions": ["MC", "MCD", "DCE", "DCD"],
                "metrics": [
                    {"metric": "Passes", "weight": 30, "direction": "positive", "importance": "critical"},
                    {"metric": "Passes precisos %", "weight": 25, "direction": "positive", "importance": "critical"},
                    {"metric": "Passes progressivos", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Passes longos", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Passes chave", "weight": 10, "direction": "positive", "importance": "medium"}
                ]
            },

            "young_prospect": {
                "name": "Young Prospect Potential",
                "description": "Identifies promising young talents with high potential",
                "category": "Potential",
                "positions": ["all"],
                "metrics": [
                    {"metric": "Minutos jogados", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Gols", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Assistências", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Passes", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Desarmes", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Dribles", "weight": 10, "direction": "positive", "importance": "medium"},
                    {"metric": "Faltas", "weight": 10, "direction": "negative", "importance": "low"}
                ],
                "age_weight_curve": "Prefer Young (Under 25)",
                "market_value_consideration": "Value for Money (Lower = Better)"
            },

            "versatile_utility": {
                "name": "Versatile Utility Player",
                "description": "Well-rounded players who can adapt to multiple roles",
                "category": "Complete Player",
                "positions": ["all"],
                "metrics": [
                    {"metric": "Passes", "weight": 20, "direction": "positive", "importance": "high"},
                    {"metric": "Desarmes", "weight": 18, "direction": "positive", "importance": "high"},
                    {"metric": "Disputas no ataque", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Disputas na defesa", "weight": 15, "direction": "positive", "importance": "medium"},
                    {"metric": "Bolas recuperadas", "weight": 12, "direction": "positive", "importance": "medium"},
                    {"metric": "Passes chave", "weight": 10, "direction": "positive", "importance": "medium"},
                    {"metric": "Faltas", "weight": 10, "direction": "negative", "importance": "low"}
                ]
            }
        }

    def apply_ranking_template(self, template_name: str, position: str) -> bool:
        """Apply a ranking template"""

        templates = self.get_ranking_templates()

        if template_name not in templates:
            return False

        template = templates[template_name].copy()
        template['position'] = position
        template['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Adjust template for specific position if needed
        if template.get('positions') == ['all'] or position in template.get('positions', []):
            # Save as custom ranking
            ranking_id = f"{position}_{template['name'].replace(' ', '_').lower()}"
            existing_rankings = self.load_custom_rankings()
            existing_rankings[ranking_id] = template

            try:
                with open(self.rankings_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_rankings, f, ensure_ascii=False, indent=2)
                return True
            except:
                return False

        return False

    def export_rankings_config(self) -> Optional[str]:
        """Export all custom rankings as JSON"""

        rankings = self.load_custom_rankings()
        if not rankings:
            return None

        try:
            export_data = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'rankings_count': len(rankings),
                'rankings': rankings
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting rankings: {str(e)}")
            return None

    def import_rankings_config(self, import_data: str) -> bool:
        """Import custom rankings from JSON"""

        try:
            data = json.loads(import_data)

            if 'rankings' not in data:
                st.error("Invalid import format - missing rankings data")
                return False

            imported_rankings = data['rankings']
            existing_rankings = self.load_custom_rankings()

            # Count new vs existing
            new_count = 0
            updated_count = 0

            for ranking_id, ranking_config in imported_rankings.items():
                if ranking_id in existing_rankings:
                    updated_count += 1
                else:
                    new_count += 1

                existing_rankings[ranking_id] = ranking_config

            # Save updated rankings
            with open(self.rankings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_rankings, f, ensure_ascii=False, indent=2)

            st.success(f"Import successful: {new_count} new rankings, {updated_count} updated")
            return True

        except json.JSONDecodeError:
            st.error("Invalid JSON format")
            return False
        except Exception as e:
            st.error(f"Error importing rankings: {str(e)}")
            return False