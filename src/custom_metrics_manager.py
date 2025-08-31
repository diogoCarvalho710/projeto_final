import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np


class CustomMetricsManager:
    """Manager for creating and managing custom metrics"""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.metrics_file = Path("data/temp/custom_metrics.json")
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """Ensure data directory exists"""
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def load_custom_metrics(self) -> Dict:
        """Load custom metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading custom metrics: {str(e)}")
        return {}

    def save_custom_metrics(self, metrics: Dict):
        """Save custom metrics to file"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving custom metrics: {str(e)}")
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

    def create_metric_ui(self, position: str):
        """UI for creating custom metrics"""
        st.subheader(f"🎨 Create Custom Metric for {position}")

        # Metric name
        metric_name = st.text_input(
            "Metric Name",
            placeholder="e.g., Attacking Effectiveness",
            key=f"metric_name_{position}"
        )

        if not metric_name:
            st.info("👆 Enter a metric name to continue")
            return

        # Description
        description = st.text_area(
            "Description",
            placeholder="Describe what this metric measures...",
            key=f"metric_desc_{position}"
        )

        # Get available metrics
        available_metrics = self.get_available_metrics(position)

        if not available_metrics:
            st.error(f"No numeric metrics available for {position}")
            return

        # Number of components
        num_components = st.slider(
            "Number of Components",
            min_value=2,
            max_value=8,
            value=3,
            key=f"num_components_{position}"
        )

        # Components selection
        components = []
        weights_sum = 0

        st.markdown("### 🔧 Metric Components")

        for i in range(num_components):
            st.markdown(f"**Component {i + 1}**")

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                metric = st.selectbox(
                    f"Variable {i + 1}",
                    available_metrics,
                    key=f"metric_{position}_{i}",
                    index=i if i < len(available_metrics) else 0
                )

            with col2:
                weight = st.number_input(
                    "Weight %",
                    min_value=1,
                    max_value=100,
                    value=25,
                    key=f"weight_{position}_{i}"
                )

            with col3:
                direction = st.selectbox(
                    "Direction",
                    ["Higher is better", "Lower is better"],
                    key=f"direction_{position}_{i}"
                )

            components.append({
                'metric': metric,
                'weight': weight,
                'direction': 'positive' if direction == "Higher is better" else 'negative'
            })

            weights_sum += weight

        # Weight validation
        if weights_sum != 100:
            st.warning(f"⚠️ Weights sum to {weights_sum}%. Should sum to 100%.")

        # Preview calculation
        if weights_sum == 100 and st.button(f"Create Metric", key=f"create_metric_{position}"):
            self.create_custom_metric(metric_name, description, position, components)

    def create_custom_metric(self, name: str, description: str, position: str, components: List[Dict]):
        """Create and save custom metric"""
        try:
            # Load existing metrics
            custom_metrics = self.load_custom_metrics()

            # Create metric ID
            metric_id = f"{position}_{name.lower().replace(' ', '_')}"

            # Create metric definition
            metric_def = {
                'name': name,
                'description': description,
                'position': position,
                'components': components,
                'created_at': pd.Timestamp.now().isoformat()
            }

            # Save metric
            custom_metrics[metric_id] = metric_def

            if self.save_custom_metrics(custom_metrics):
                st.success(f"✅ Custom metric '{name}' created successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save custom metric")

        except Exception as e:
            st.error(f"Error creating metric: {str(e)}")

    def show_manage_metrics_ui_updated(self):
        """Show manage metrics UI (without Test/Copy options)"""
        st.subheader("📊 Manage Custom Metrics")

        custom_metrics = self.load_custom_metrics()

        if not custom_metrics:
            st.info("📭 No custom metrics created yet. Create one in the 'Create Metric' tab.")
            return

        # Group by position
        metrics_by_position = {}
        for metric_id, metric_def in custom_metrics.items():
            position = metric_def['position']
            if position not in metrics_by_position:
                metrics_by_position[position] = {}
            metrics_by_position[position][metric_id] = metric_def

        # Show metrics by position
        for position, position_metrics in metrics_by_position.items():
            st.markdown(f"### 📍 {position} Metrics")

            for metric_id, metric_def in position_metrics.items():
                with st.expander(f"🎯 {metric_def['name']}", expanded=False):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Description:** {metric_def.get('description', 'No description')}")

                        st.markdown("**Components:**")
                        for comp in metric_def['components']:
                            direction_icon = "📈" if comp['direction'] == 'positive' else "📉"
                            st.markdown(f"• {comp['metric']}: {comp['weight']}% {direction_icon}")

                        st.caption(f"Created: {metric_def.get('created_at', 'Unknown')}")

                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{metric_id}"):
                            if self.delete_metric(metric_id):
                                st.success(f"Deleted {metric_def['name']}")
                                st.rerun()

                st.markdown("---")

    def delete_metric(self, metric_id: str) -> bool:
        """Delete a custom metric"""
        try:
            custom_metrics = self.load_custom_metrics()
            if metric_id in custom_metrics:
                del custom_metrics[metric_id]
                return self.save_custom_metrics(custom_metrics)
            return False
        except Exception as e:
            st.error(f"Error deleting metric: {str(e)}")
            return False

    def calculate_custom_metric(self, df: pd.DataFrame, metric_def: Dict) -> pd.Series:
        """Calculate custom metric for a dataframe"""
        try:
            scores = pd.Series(0.0, index=df.index)

            for component in metric_def['components']:
                metric_name = component['metric']
                weight = component['weight'] / 100
                direction = component['direction']

                if metric_name in df.columns:
                    values = pd.to_numeric(df[metric_name], errors='coerce').fillna(0)

                    # Normalize to 0-100 scale
                    if values.max() != values.min():
                        normalized = ((values - values.min()) / (values.max() - values.min())) * 100
                    else:
                        normalized = pd.Series(50.0, index=values.index)

                    # Apply direction
                    if direction == 'negative':
                        normalized = 100 - normalized

                    # Apply weight
                    scores += normalized * weight

            return scores.round(2)

        except Exception as e:
            st.error(f"Error calculating custom metric: {str(e)}")
            return pd.Series(0.0, index=df.index)

    def get_custom_metrics_for_position(self, position: str) -> Dict:
        """Get custom metrics for a specific position"""
        custom_metrics = self.load_custom_metrics()
        position_metrics = {}

        for metric_id, metric_def in custom_metrics.items():
            if metric_def['position'] == position:
                position_metrics[metric_id] = metric_def

        return position_metrics

    def apply_custom_metrics_to_df(self, df: pd.DataFrame, position: str) -> pd.DataFrame:
        """Apply all custom metrics to a dataframe"""
        result_df = df.copy()
        position_metrics = self.get_custom_metrics_for_position(position)

        for metric_id, metric_def in position_metrics.items():
            metric_name = f"Custom_{metric_def['name']}"
            result_df[metric_name] = self.calculate_custom_metric(df, metric_def)

        return result_df

    def get_metric_templates(self) -> Dict:
        """Get predefined metric templates"""
        return {
            'attacking_efficiency': {
                'name': 'Attacking Efficiency',
                'category': 'Offensive',
                'description': 'Measures overall attacking contribution',
                'components': [
                    {'metric': 'Gols', 'weight': 40, 'direction': 'positive'},
                    {'metric': 'Assistências', 'weight': 30, 'direction': 'positive'},
                    {'metric': 'Passes chave', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Chutes no gol', 'weight': 10, 'direction': 'positive'}
                ]
            },
            'defensive_solidity': {
                'name': 'Defensive Solidity',
                'category': 'Defensive',
                'description': 'Measures defensive reliability',
                'components': [
                    {'metric': 'Desarmes', 'weight': 35, 'direction': 'positive'},
                    {'metric': 'Tentativas bem-sucedidas de interceptação de cruzamento e passe', 'weight': 30, 'direction': 'positive'},
                    {'metric': 'Disputas na defesa ganhas', 'weight': 25, 'direction': 'positive'},
                    {'metric': 'Faltas', 'weight': 10, 'direction': 'negative'}
                ]
            },
            'passing_mastery': {
                'name': 'Passing Mastery',
                'category': 'Playmaking',
                'description': 'Measures passing quality and effectiveness',
                'components': [
                    {'metric': 'Passes precisos', 'weight': 40, 'direction': 'positive'},
                    {'metric': 'Passes progressivos', 'weight': 30, 'direction': 'positive'},
                    {'metric': 'Passes chave', 'weight': 20, 'direction': 'positive'},
                    {'metric': 'Passes longos precisos', 'weight': 10, 'direction': 'positive'}
                ]
            }
        }

    def apply_template(self, template_id: str, position: str) -> bool:
        """Apply a metric template"""
        templates = self.get_metric_templates()

        if template_id not in templates:
            return False

        template = templates[template_id]
        available_metrics = self.get_available_metrics(position)

        # Check if all required metrics are available
        valid_components = []
        for comp in template['components']:
            if comp['metric'] in available_metrics:
                valid_components.append(comp)

        if not valid_components:
            st.error(f"No compatible metrics found for {template['name']} in {position}")
            return False

        # Adjust weights if some components are missing
        if len(valid_components) < len(template['components']):
            total_weight = sum(comp['weight'] for comp in valid_components)
            for comp in valid_components:
                comp['weight'] = int((comp['weight'] / total_weight) * 100)

        # Create the metric
        metric_name = f"{template['name']} ({position})"
        self.create_custom_metric(metric_name, template['description'], position, valid_components)
        return True

    def export_metrics_config(self) -> Optional[str]:
        """Export metrics configuration as JSON"""
        try:
            custom_metrics = self.load_custom_metrics()
            if custom_metrics:
                export_data = {
                    'export_type': 'custom_metrics',
                    'version': '1.0',
                    'metrics': custom_metrics
                }
                return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"Error exporting metrics: {str(e)}")
        return None

    def import_metrics_config(self, json_data: str) -> bool:
        """Import metrics configuration from JSON"""
        try:
            import_data = json.loads(json_data)

            if 'metrics' not in import_data:
                st.error("Invalid metrics file format")
                return False

            # Load existing metrics
            existing_metrics = self.load_custom_metrics()

            # Merge imported metrics
            imported_count = 0
            for metric_id, metric_def in import_data['metrics'].items():
                existing_metrics[metric_id] = metric_def
                imported_count += 1

            # Save merged metrics
            if self.save_custom_metrics(existing_metrics):
                st.success(f"Imported {imported_count} custom metrics")
                return True
            else:
                st.error("Failed to save imported metrics")
                return False

        except Exception as e:
            st.error(f"Error importing metrics: {str(e)}")
            return False