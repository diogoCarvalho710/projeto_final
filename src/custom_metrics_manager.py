import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime


class CustomMetricsManager:
    """Manages custom metrics creation and calculation"""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.config_dir = Path("data/configs")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.config_dir / "custom_metrics.json"

    def create_metric_ui(self, position: str) -> Optional[Dict]:
        """Show UI for creating custom metrics"""

        st.subheader("🎨 Create Custom Metric")

        if not position or position not in self.data_processor.dataframes:
            # Show template options first
            self._show_template_options(position)
            st.warning("Please select a position first")
            return None

        position_df = self.data_processor.dataframes[position]

        # Get available numeric metrics
        available_metrics = self._get_available_metrics(position_df)

        if not available_metrics:
            st.error("No numeric metrics available for this position")
            return None

        # Template options at the top
        self._show_template_options(position)

        st.markdown("---")

        # Metric basic info
        col1, col2 = st.columns(2)

        with col1:
            metric_name = st.text_input(
                "📊 Metric Name",
                placeholder="e.g., Defensive Impact",
                help="Give your metric a descriptive name",
                key=f"custom_metric_name_{position}"
            )

        with col2:
            metric_category = st.selectbox(
                "🏷️ Category",
                ["Offensive", "Defensive", "Passing", "Physical", "Technical", "Overall"],
                help="Choose the category that best fits your metric",
                key=f"custom_metric_category_{position}"
            )

        metric_description = st.text_area(
            "📝 Description",
            placeholder="Explain what this metric measures...",
            help="Describe what your custom metric represents",
            key=f"custom_metric_description_{position}"
        )

        st.markdown("---")
        st.markdown("### 🔧 **Metric Components**")
        st.markdown("Select metrics and their weights (must total 100%)")

        # Initialize session state for components
        components_key = f'custom_metric_components_{position}'
        if components_key not in st.session_state:
            st.session_state[components_key] = [
                {'metric': '', 'weight': 0, 'direction': 'positive'}
            ]

        components_state = st.session_state[components_key]
        total_weight = 0

        # Show current components
        for i, component in enumerate(components_state):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                selected_metric = st.selectbox(
                    f"Metric {i + 1}",
                    [''] + available_metrics,
                    index=available_metrics.index(component['metric']) + 1 if component[
                                                                                  'metric'] in available_metrics else 0,
                    key=f"metric_{i}_{position}"
                )
                component['metric'] = selected_metric

            with col2:
                weight = st.number_input(
                    "Weight %",
                    min_value=0,
                    max_value=100,
                    value=component['weight'],
                    key=f"weight_{i}_{position}"
                )
                component['weight'] = weight
                total_weight += weight

            with col3:
                direction = st.selectbox(
                    "Direction",
                    ["positive", "negative"],
                    index=0 if component['direction'] == 'positive' else 1,
                    key=f"direction_{i}_{position}",
                    help="Positive: higher is better, Negative: lower is better"
                )
                component['direction'] = direction

            with col4:
                if len(components_state) > 1:
                    if st.button("❌", key=f"remove_{i}_{position}", help="Remove component"):
                        components_state.pop(i)
                        st.rerun()

        # Component management buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add Component", key=f"add_component_{position}"):
                if len(components_state) < 8:
                    components_state.append({'metric': '', 'weight': 0, 'direction': 'positive'})
                    st.rerun()
                else:
                    st.warning("Maximum 8 components allowed")

        with col2:
            if st.button("⚖️ Auto Balance", key=f"auto_balance_{position}"):
                valid_components = [c for c in components_state if c['metric']]
                if valid_components:
                    weight_per_component = 100 / len(valid_components)
                    for component in components_state:
                        if component['metric']:
                            component['weight'] = round(weight_per_component, 1)
                    st.rerun()

        with col3:
            if st.button("🗑️ Clear All", key=f"clear_components_{position}"):
                st.session_state[components_key] = [{'metric': '', 'weight': 0, 'direction': 'positive'}]
                st.rerun()

        # Weight validation
        if total_weight != 100 and any(c['metric'] for c in components_state):
            st.error(f"⚠️ Total weight must be 100%. Current: {total_weight}%")
        elif total_weight == 100:
            st.success(f"✅ Total weight: {total_weight}%")

        # Preview calculation
        if metric_name and all(c['metric'] for c in components_state if c['weight'] > 0):
            st.markdown("---")
            st.markdown("### 👀 **Preview**")
            preview_data = self._calculate_preview(position_df, components_state, metric_name)
            if preview_data is not None:
                self._show_preview(preview_data, metric_name)

        # Save metric
        st.markdown("---")
        if st.button("💾 Save Custom Metric", key=f"save_metric_{position}"):
            if not metric_name:
                st.error("Please enter a metric name")
                return None

            valid_components = [c for c in components_state if c['metric'] and c['weight'] > 0]
            if not valid_components:
                st.error("Please select at least one metric component")
                return None

            total_weight = sum(c['weight'] for c in valid_components)
            if total_weight != 100:
                st.error(f"Total weight must be 100%. Current: {total_weight}%")
                return None

            # Create metric config
            metric_config = {
                'name': metric_name,
                'description': metric_description,
                'category': metric_category,
                'position': position,
                'components': valid_components,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Save metric
            if self.save_custom_metric(metric_config):
                st.success(f"✅ Custom metric '{metric_name}' saved successfully!")
                # Clear the form
                if components_key in st.session_state:
                    del st.session_state[components_key]
                st.rerun()
            else:
                st.error("Failed to save custom metric")

        return None

    def _show_template_options(self, position: str):
        """Show template options for quick metric creation"""

        st.markdown("**🚀 Quick Start with Templates:**")

        templates = self.get_metric_templates()
        template_names = list(templates.keys())

        if template_names:
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_template = st.selectbox(
                    "Choose a template:",
                    [""] + template_names,
                    format_func=lambda x: templates[x]['name'] if x else "Select template...",
                    key=f"template_select_{position}"
                )

            with col2:
                if selected_template and st.button("📋 Apply Template", key=f"apply_template_{position}"):
                    if position and self.apply_template(selected_template, position):
                        st.success(f"✅ Applied template: {templates[selected_template]['name']}")
                        st.rerun()
                    else:
                        st.error("Failed to apply template")

            # Show template description
            if selected_template:
                template_info = templates[selected_template]
                st.info(f"📖 **{template_info['name']}**: {template_info['description']}")

    def _get_available_metrics(self, df: pd.DataFrame) -> List[str]:
        """Get list of available numeric metrics for custom metric creation"""

        exclude_cols = [
            'Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
            'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
            'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados'
        ]

        numeric_cols = []
        for col in df.columns:
            if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col]):
                # Exclude percentile columns and overall scores
                if not col.endswith('_percentile') and col != 'Overall_Score':
                    numeric_cols.append(col)

        return sorted(numeric_cols)

    def _calculate_preview(self, df: pd.DataFrame, components: List[Dict], metric_name: str) -> Optional[pd.DataFrame]:
        """Calculate preview of custom metric"""

        try:
            custom_values = pd.Series(0.0, index=df.index)

            for component in components:
                if not component['metric'] or component['weight'] == 0:
                    continue

                metric_col = component['metric']
                weight = component['weight'] / 100
                direction = component['direction']

                if metric_col in df.columns:
                    values = pd.to_numeric(df[metric_col], errors='coerce').fillna(0)

                    # Apply direction (negative means lower is better)
                    if direction == 'negative':
                        max_val = values.max()
                        if max_val > 0:
                            values = max_val - values

                    custom_values += values * weight

            # Create preview dataframe
            preview_df = df[['Jogador', 'Time', 'Idade', 'Minutos jogados']].copy()
            preview_df[metric_name] = custom_values.round(2)
            preview_df = preview_df.sort_values(metric_name, ascending=False)

            return preview_df.head(10)

        except Exception as e:
            st.error(f"Error calculating preview: {str(e)}")
            return None

    def _show_preview(self, preview_df: pd.DataFrame, metric_name: str):
        """Show preview of the custom metric"""

        st.markdown(f"**🎯 Top 10 players by {metric_name}:**")

        display_df = preview_df.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df = display_df[['Rank', 'Jogador', 'Time', 'Idade', metric_name]]
        display_df.columns = ['Rank', 'Player', 'Team', 'Age', metric_name]

        st.dataframe(display_df, use_container_width=True)

        # Show distribution info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Top Score", f"{preview_df[metric_name].max():.2f}")
        with col2:
            st.metric("Average", f"{preview_df[metric_name].mean():.2f}")
        with col3:
            st.metric("Range", f"{preview_df[metric_name].max() - preview_df[metric_name].min():.2f}")

    def save_custom_metric(self, metric_config: Dict) -> bool:
        """Save custom metric to JSON file"""

        try:
            existing_metrics = self.load_custom_metrics()

            metric_id = f"{metric_config['position']}_{metric_config['name'].replace(' ', '_').lower()}"
            existing_metrics[metric_id] = metric_config

            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metrics, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            st.error(f"Error saving custom metric: {str(e)}")
            return False

    def load_custom_metrics(self) -> Dict:
        """Load custom metrics from JSON file"""

        if not self.metrics_file.exists():
            return {}

        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading custom metrics: {str(e)}")
            return {}

    def get_custom_metrics_by_position(self, position: str) -> Dict:
        """Get custom metrics for a specific position"""

        all_metrics = self.load_custom_metrics()
        return {k: v for k, v in all_metrics.items() if v.get('position') == position}

    def calculate_custom_metric(self, df: pd.DataFrame, metric_config: Dict) -> pd.Series:
        """Calculate custom metric values for a dataframe"""

        custom_values = pd.Series(0.0, index=df.index)

        for component in metric_config['components']:
            if component['weight'] == 0:
                continue

            metric_col = component['metric']
            weight = component['weight'] / 100
            direction = component['direction']

            if metric_col in df.columns:
                values = pd.to_numeric(df[metric_col], errors='coerce').fillna(0)

                if direction == 'negative':
                    max_val = values.max()
                    if max_val > 0:
                        values = max_val - values

                custom_values += values * weight

        return custom_values.round(2)

    def show_manage_metrics_ui(self):
        """Show UI for managing existing custom metrics"""

        st.subheader("📋 Manage Custom Metrics")

        custom_metrics = self.load_custom_metrics()

        if not custom_metrics:
            st.info("No custom metrics created yet. Create your first metric above!")
            return

        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Metrics", len(custom_metrics))
        with col2:
            positions = set(m.get('position', 'Unknown') for m in custom_metrics.values())
            st.metric("Positions", len(positions))
        with col3:
            categories = set(m.get('category', 'Unknown') for m in custom_metrics.values())
            st.metric("Categories", len(categories))

        # Filter options
        col1, col2 = st.columns(2)

        with col1:
            position_filter = st.selectbox(
                "Filter by Position",
                ["All"] + sorted(positions),
                key="metrics_position_filter"
            )

        with col2:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(categories),
                key="metrics_category_filter"
            )

        # Apply filters
        filtered_metrics = custom_metrics.copy()
        if position_filter != "All":
            filtered_metrics = {k: v for k, v in filtered_metrics.items() if v.get('position') == position_filter}
        if category_filter != "All":
            filtered_metrics = {k: v for k, v in filtered_metrics.items() if v.get('category') == category_filter}

        if not filtered_metrics:
            st.info("No metrics match the current filters")
            return

        st.markdown("---")

        # Group by position for better organization
        metrics_by_position = {}
        for metric_id, metric_config in filtered_metrics.items():
            position = metric_config['position']
            if position not in metrics_by_position:
                metrics_by_position[position] = []
            metrics_by_position[position].append((metric_id, metric_config))

        for position, metrics in metrics_by_position.items():
            with st.expander(f"📍 {position} Metrics ({len(metrics)})", expanded=True):

                for metric_id, metric_config in metrics:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{metric_config['name']}**")
                        st.caption(
                            f"📂 {metric_config.get('category', 'N/A')} | 🕐 {metric_config.get('created_date', 'Unknown')[:10]}")

                        if metric_config.get('description'):
                            st.caption(f"📝 {metric_config['description']}")

                        # Show components summary
                        components_text = ", ".join([
                            f"{comp['metric']} ({comp['weight']}%)"
                            for comp in metric_config['components']
                        ])
                        st.caption(f"📊 Components: {components_text}")

                    with col2:
                        if st.button("🧪 Test", key=f"test_{metric_id}", help="Test metric on current data"):
                            self._test_custom_metric(metric_config)

                    with col3:
                        if st.button("📋 Copy", key=f"copy_{metric_id}", help="Copy metric for editing"):
                            self._copy_metric_to_creator(metric_config)

                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{metric_id}", help="Delete metric"):
                            if self.delete_custom_metric(metric_id):
                                st.success(f"Deleted {metric_config['name']}")
                                st.rerun()

                    st.markdown("---")

    def _test_custom_metric(self, metric_config: Dict):
        """Test a custom metric and show results"""

        position = metric_config['position']
        if position not in self.data_processor.dataframes:
            st.error(f"Position {position} data not available")
            return

        df = self.data_processor.dataframes[position]
        custom_values = self.calculate_custom_metric(df, metric_config)

        # Create test results
        test_df = df[['Jogador', 'Time', 'Idade']].copy()
        test_df[metric_config['name']] = custom_values
        test_df = test_df.sort_values(metric_config['name'], ascending=False)

        st.markdown(f"**🧪 Test Results for '{metric_config['name']}':**")

        # Show top 10 with ranking
        display_df = test_df.head(10).copy()
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
        st.dataframe(display_df, use_container_width=True)

        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Top Score", f"{custom_values.max():.2f}")
        with col2:
            st.metric("Average", f"{custom_values.mean():.2f}")
        with col3:
            st.metric("Median", f"{custom_values.median():.2f}")
        with col4:
            st.metric("Std Dev", f"{custom_values.std():.2f}")

    def _copy_metric_to_creator(self, metric_config: Dict):
        """Copy metric configuration to the creator form"""

        position = metric_config['position']
        components_key = f'custom_metric_components_{position}'

        # Copy components to session state
        st.session_state[components_key] = metric_config['components'].copy()

        st.success(f"📋 Copied '{metric_config['name']}' components to creator. Switch to Create tab to modify.")

    def delete_custom_metric(self, metric_id: str) -> bool:
        """Delete a custom metric"""

        try:
            existing_metrics = self.load_custom_metrics()

            if metric_id in existing_metrics:
                del existing_metrics[metric_id]

                with open(self.metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_metrics, f, ensure_ascii=False, indent=2)

                return True

            return False

        except Exception as e:
            st.error(f"Error deleting custom metric: {str(e)}")
            return False

    def get_metric_templates(self) -> Dict:
        """Get predefined metric templates"""

        return {
            "defensive_impact": {
                "name": "Defensive Impact",
                "description": "Overall defensive contribution combining tackles, interceptions and aerial duels",
                "category": "Defensive",
                "components": [
                    {"metric": "Desarmes", "weight": 35, "direction": "positive"},
                    {"metric": "Interceptações", "weight": 35, "direction": "positive"},
                    {"metric": "Disputas aéreas", "weight": 20, "direction": "positive"},
                    {"metric": "Faltas", "weight": 10, "direction": "negative"}
                ]
            },
            "creative_output": {
                "name": "Creative Output",
                "description": "Measures player's creativity through passes and assists",
                "category": "Offensive",
                "components": [
                    {"metric": "Passes chave", "weight": 40, "direction": "positive"},
                    {"metric": "xA", "weight": 30, "direction": "positive"},
                    {"metric": "Assistências", "weight": 20, "direction": "positive"},
                    {"metric": "Passes progressivos", "weight": 10, "direction": "positive"}
                ]
            },
            "goal_threat": {
                "name": "Goal Threat",
                "description": "Player's ability to score and threaten the goal",
                "category": "Offensive",
                "components": [
                    {"metric": "xG", "weight": 35, "direction": "positive"},
                    {"metric": "Chutes no gol", "weight": 25, "direction": "positive"},
                    {"metric": "Gols", "weight": 25, "direction": "positive"},
                    {"metric": "Dribles", "weight": 15, "direction": "positive"}
                ]
            },
            "passing_maestro": {
                "name": "Passing Maestro",
                "description": "Complete passing ability and distribution",
                "category": "Passing",
                "components": [
                    {"metric": "Passes", "weight": 30, "direction": "positive"},
                    {"metric": "Passes precisos %", "weight": 25, "direction": "positive"},
                    {"metric": "Passes progressivos", "weight": 25, "direction": "positive"},
                    {"metric": "Passes longos", "weight": 20, "direction": "positive"}
                ]
            },
            "aerial_dominance": {
                "name": "Aerial Dominance",
                "description": "Dominance in aerial situations",
                "category": "Physical",
                "components": [
                    {"metric": "Disputas aéreas", "weight": 60, "direction": "positive"},
                    {"metric": "Desafios aéreos vencidos, %", "weight": 40, "direction": "positive"}
                ]
            },
            "box_to_box": {
                "name": "Box-to-Box Impact",
                "description": "Complete midfielder contributing in both boxes",
                "category": "Overall",
                "components": [
                    {"metric": "Passes", "weight": 25, "direction": "positive"},
                    {"metric": "Bolas recuperadas", "weight": 20, "direction": "positive"},
                    {"metric": "Passes chave", "weight": 20, "direction": "positive"},
                    {"metric": "Chutes", "weight": 15, "direction": "positive"},
                    {"metric": "Desarmes", "weight": 15, "direction": "positive"},
                    {"metric": "Faltas", "weight": 5, "direction": "negative"}
                ]
            }
        }

    def apply_template(self, template_name: str, position: str) -> bool:
        """Apply a metric template"""

        templates = self.get_metric_templates()

        if template_name not in templates:
            return False

        template = templates[template_name].copy()
        template['position'] = position
        template['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save as custom metric
        metric_id = f"{position}_{template['name'].replace(' ', '_').lower()}"
        existing_metrics = self.load_custom_metrics()
        existing_metrics[metric_id] = template

        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metrics, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def export_metrics_config(self) -> Optional[str]:
        """Export all custom metrics as JSON"""

        metrics = self.load_custom_metrics()
        if not metrics:
            return None

        try:
            export_data = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'metrics_count': len(metrics),
                'metrics': metrics
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting metrics: {str(e)}")
            return None

    def import_metrics_config(self, import_data: str) -> bool:
        """Import custom metrics from JSON"""

        try:
            data = json.loads(import_data)

            if 'metrics' not in data:
                st.error("Invalid import format - missing metrics data")
                return False

            imported_metrics = data['metrics']
            existing_metrics = self.load_custom_metrics()

            # Count new vs existing
            new_count = 0
            updated_count = 0

            for metric_id, metric_config in imported_metrics.items():
                if metric_id in existing_metrics:
                    updated_count += 1
                else:
                    new_count += 1

                existing_metrics[metric_id] = metric_config

            # Save updated metrics
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metrics, f, ensure_ascii=False, indent=2)

            st.success(f"✅ Import successful: {new_count} new metrics, {updated_count} updated")
            return True

        except json.JSONDecodeError:
            st.error("Invalid JSON format")
            return False
        except Exception as e:
            st.error(f"Error importing metrics: {str(e)}")
            return False