import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple


class ScoutingFilters:
    """Component for scouting filters"""

    @staticmethod
    def show_position_filter(positions: List[str], key: str = "position") -> Optional[str]:
        """Show position filter dropdown"""

        position_names = {
            "GR": "🥅 Goalkeeper",
            "DCE": "🛡️ Centre-Back (Left)",
            "DCD": "🛡️ Centre-Back (Right)",
            "DE": "⬅️ Left-Back",
            "DD": "➡️ Right-Back",
            "EE": "⬅️ Left Winger",
            "ED": "➡️ Right Winger",
            "MCD": "🛡️ Defensive Midfielder",
            "MC": "⚽ Central Midfielder",
            "PL": "🎯 Forward"
        }

        # Add "All Positions" option
        options = ["All Positions"] + positions
        display_options = ["🔍 All Positions"] + [position_names.get(pos, pos) for pos in positions]

        selected_idx = st.selectbox(
            "🎯 Position",
            range(len(options)),
            format_func=lambda x: display_options[x],
            key=key,
            help="Select specific position or search all"
        )

        return None if selected_idx == 0 else options[selected_idx]

    @staticmethod
    def show_age_filter(key: str = "age") -> Tuple[int, int]:
        """Show age range filter"""

        st.markdown("👶 **Age Range**")

        col1, col2 = st.columns(2)

        with col1:
            min_age = st.number_input(
                "Min Age",
                min_value=16,
                max_value=40,
                value=16,
                key=f"{key}_min",
                help="Minimum age"
            )

        with col2:
            max_age = st.number_input(
                "Max Age",
                min_value=16,
                max_value=40,
                value=35,
                key=f"{key}_max",
                help="Maximum age"
            )

        return min_age, max_age

    @staticmethod
    def show_minutes_filter(key: str = "minutes") -> int:
        """Show minimum minutes filter"""

        return st.slider(
            "⏱️ Minimum Minutes Played",
            min_value=0,
            max_value=3000,
            value=500,
            step=100,
            key=key,
            help="Filter players with at least this many minutes"
        )

    @staticmethod
    def show_nationality_filter(nationalities: List[str], key: str = "nationality") -> Optional[str]:
        """Show nationality filter"""

        # Add "All Nationalities" option
        options = ["All Nationalities"] + sorted(nationalities)

        selected = st.selectbox(
            "🌍 Nationality",
            options,
            key=key,
            help="Filter by player nationality"
        )

        return None if selected == "All Nationalities" else selected

    @staticmethod
    def show_team_filter(teams: List[str], current_team: str, key: str = "team") -> Dict[str, bool]:
        """Show team exclusion filters"""

        st.markdown("🏆 **Team Filters**")

        exclude_own_team = st.checkbox(
            f"🚫 Exclude {current_team} players",
            value=True,
            key=f"{key}_exclude_own",
            help=f"Hide players from {current_team}"
        )

        # Option to exclude specific teams
        with st.expander("🔧 Advanced Team Filters"):
            exclude_teams = st.multiselect(
                "🚫 Exclude specific teams",
                teams,
                key=f"{key}_exclude_specific",
                help="Select teams to exclude from results"
            )

        return {
            "exclude_own": exclude_own_team,
            "exclude_teams": exclude_teams
        }

    @staticmethod
    def show_performance_filters(position: str, data_processor, current_team: str, key: str = "performance") -> Dict[
        str, float]:
        """Show advanced performance filters with dynamic metrics and threshold options"""

        st.markdown("📊 **Performance Filters**")

        # Get available numeric metrics for the position
        if position not in data_processor.dataframes:
            st.info("Select a position first")
            return {}

        position_df = data_processor.dataframes[position]

        # Get numeric columns (exclude basic info columns)
        exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                        'Data de nascimento', 'Posição', 'Temporada', 'Idade', 'Partidas jogadas',
                        'Minutos jogados', 'Position_File']

        numeric_cols = []
        for col in position_df.columns:
            if col not in exclude_cols and pd.api.types.is_numeric_dtype(position_df[col]):
                numeric_cols.append(col)

        if not numeric_cols:
            st.info("No performance metrics available for this position")
            return {}

        # Sort metrics alphabetically for better UX
        numeric_cols = sorted(numeric_cols)

        # Metric selection
        st.markdown("**Select Metrics to Filter:**")
        selected_metrics = st.multiselect(
            "Choose metrics",
            numeric_cols,
            key=f"{key}_metrics_select",
            help="Select which metrics you want to filter by"
        )

        if not selected_metrics:
            st.info("👆 Select metrics above to set filters")
            return {}

        filters = {}

        # For each selected metric, show threshold options
        for metric in selected_metrics:
            st.markdown(f"---")
            st.markdown(f"**🎯 {ScoutingFilters._shorten_metric_name(metric)}**")

            # Calculate statistics for this metric
            metric_values = pd.to_numeric(position_df[metric], errors='coerce').dropna()

            if metric_values.empty:
                st.warning(f"No valid data for {metric}")
                continue

            # Overall statistics
            overall_mean = metric_values.mean()
            overall_median = metric_values.median()
            overall_max = metric_values.max()
            overall_min = metric_values.min()

            # Team-specific statistics
            team_df = position_df[position_df['Time'] == current_team]
            team_values = pd.to_numeric(team_df[metric], errors='coerce').dropna()
            team_mean = team_values.mean() if not team_values.empty else overall_mean
            team_median = team_values.median() if not team_values.empty else overall_median

            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Average", f"{overall_mean:.2f}")
            with col2:
                st.metric("Your Team Average", f"{team_mean:.2f}")
            with col3:
                st.metric("League Maximum", f"{overall_max:.2f}")

            # Threshold selection method
            threshold_method = st.radio(
                "Set minimum threshold:",
                [
                    "Custom Value",
                    "League Average",
                    "Your Team Average",
                    "Above League Average (+10%)",
                    "Top 25% (75th percentile)",
                    "Top 10% (90th percentile)"
                ],
                key=f"{key}_{metric}_method",
                horizontal=True
            )

            # Calculate threshold based on method
            if threshold_method == "Custom Value":
                threshold = st.number_input(
                    f"Minimum {ScoutingFilters._shorten_metric_name(metric)}:",
                    min_value=float(overall_min),
                    max_value=float(overall_max),
                    value=float(overall_mean),
                    step=0.1,
                    key=f"{key}_{metric}_custom",
                    help=f"Range: {overall_min:.1f} - {overall_max:.1f}"
                )
            elif threshold_method == "League Average":
                threshold = overall_mean
                st.info(f"✅ Using league average: **{threshold:.2f}**")
            elif threshold_method == "Your Team Average":
                threshold = team_mean
                st.info(f"✅ Using your team average: **{threshold:.2f}**")
            elif threshold_method == "Above League Average (+10%)":
                threshold = overall_mean * 1.1
                st.info(f"✅ Using 110% of league average: **{threshold:.2f}**")
            elif threshold_method == "Top 25% (75th percentile)":
                threshold = metric_values.quantile(0.75)
                st.info(f"✅ Using 75th percentile: **{threshold:.2f}**")
            elif threshold_method == "Top 10% (90th percentile)":
                threshold = metric_values.quantile(0.90)
                st.info(f"✅ Using 90th percentile: **{threshold:.2f}**")

            # Store the filter
            filters[f'min_{metric}'] = threshold

        return filters

    @staticmethod
    def _shorten_metric_name(metric: str) -> str:
        """Shorten metric names for better display"""

        shortenings = {
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe': 'Interceptions',
            'Participação em ataques de pontuação': 'Scoring Attacks',
            'Ações / com sucesso': 'Successful Actions',
            'Dribles bem-sucedidos': 'Successful Dribbles',
            'Cruzamentos precisos': 'Accurate Crosses',
            'Bolas recuperadas': 'Ball Recoveries',
            'Passes progressivos': 'Progressive Passes',
            'Disputas aéreas': 'Aerial Duels',
            'Chutes no gol': 'Shots on Target',
            'Toques na área': 'Touches in Box',
            'Minutos jogados': 'Minutes',
            'Partidas jogadas': 'Matches',
            'Passes chave': 'Key Passes',
            'Passes precisos': 'Accurate Passes',
            'Passes precisos %': 'Pass Accuracy %',
            'Defesas, %': 'Save %'
        }

        return shortenings.get(metric, metric)

    @staticmethod
    def show_search_filter(key: str = "search") -> str:
        """Show player name search filter"""

        return st.text_input(
            "🔍 Search Player Name",
            placeholder="Enter player name...",
            key=key,
            help="Search for specific player by name"
        )

    @staticmethod
    def show_market_value_filter(key: str = "market_value") -> Tuple[Optional[str], Optional[str]]:
        """Show market value filter"""

        st.markdown("💰 **Market Value Range**")

        # Common market value options
        value_options = [
            "Any Value",
            "Up to €100K",
            "€100K - €500K",
            "€500K - €1M",
            "€1M - €5M",
            "€5M - €10M",
            "Over €10M"
        ]

        selected = st.selectbox(
            "Market Value Range",
            value_options,
            key=key,
            help="Filter players by estimated market value"
        )

        # Convert to min/max values
        value_ranges = {
            "Any Value": (None, None),
            "Up to €100K": (None, "€100k"),
            "€100K - €500K": ("€100k", "€500k"),
            "€500K - €1M": ("€500k", "€1M"),
            "€1M - €5M": ("€1M", "€5M"),
            "€5M - €10M": ("€5M", "€10M"),
            "Over €10M": ("€10M", None)
        }

        return value_ranges.get(selected, (None, None))

    @staticmethod
    def show_filter_summary(filters: Dict, position: str = None) -> None:
        """Show summary of applied filters"""

        active_filters = []

        if position:
            active_filters.append(f"Position: {position}")

        if filters.get('min_age') and filters.get('max_age'):
            if filters['min_age'] != 16 or filters['max_age'] != 35:
                active_filters.append(f"Age: {filters['min_age']}-{filters['max_age']}")

        if filters.get('min_minutes', 0) > 0:
            active_filters.append(f"Min Minutes: {filters['min_minutes']}")

        if filters.get('nationality'):
            active_filters.append(f"Nationality: {filters['nationality']}")

        if filters.get('search'):
            active_filters.append(f"Search: '{filters['search']}'")

        if filters.get('exclude_own_team'):
            active_filters.append("Excluding own team")

        if filters.get('exclude_teams'):
            active_filters.append(f"Excluding {len(filters['exclude_teams'])} teams")

        if active_filters:
            st.markdown("**🔍 Active Filters:**")
            for filter_desc in active_filters:
                st.markdown(f"• {filter_desc}")
        else:
            st.markdown("**🔍 No filters applied** - Showing all players")

    @staticmethod
    def get_filter_state() -> Dict:
        """Get current state of all filters from session state"""

        filters = {}

        # Extract filter values from session state
        for key in st.session_state.keys():
            if key.startswith(
                    ('position', 'age', 'minutes', 'nationality', 'team', 'search', 'performance', 'market_value')):
                filters[key] = st.session_state[key]

        return filters

    @staticmethod
    def clear_filters():
        """Clear all filter values"""

        # Clear filter-related session state
        keys_to_clear = []
        for key in st.session_state.keys():
            if key.startswith(('scout_', 'position', 'age', 'minutes', 'nationality', 'team', 'search', 'performance',
                               'market_value')):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            del st.session_state[key]

        st.rerun()


class FilterValidator:
    """Utility class to validate and apply filters to dataframes"""

    @staticmethod
    def apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply all filters to a dataframe"""

        if df.empty:
            return df

        result_df = df.copy()

        # Age filters
        if 'min_age' in filters and filters['min_age'] and 'Idade' in result_df.columns:
            result_df = result_df[result_df['Idade'] >= filters['min_age']]

        if 'max_age' in filters and filters['max_age'] and 'Idade' in result_df.columns:
            result_df = result_df[result_df['Idade'] <= filters['max_age']]

        # Minutes filter
        if 'min_minutes' in filters and filters['min_minutes'] and 'Minutos jogados' in result_df.columns:
            result_df = result_df[result_df['Minutos jogados'] >= filters['min_minutes']]

        # Nationality filter
        if 'nationality' in filters and filters['nationality'] and 'Nacionalidade' in result_df.columns:
            result_df = result_df[result_df['Nacionalidade'] == filters['nationality']]

        # Team exclusion
        if 'exclude_teams' in filters and filters['exclude_teams'] and 'Time' in result_df.columns:
            result_df = result_df[~result_df['Time'].isin(filters['exclude_teams'])]

        # Search filter
        if 'search' in filters and filters['search'] and 'Jogador' in result_df.columns:
            search_term = filters['search']
            mask = result_df['Jogador'].str.contains(search_term, case=False, na=False)
            result_df = result_df[mask]

        return result_df

    @staticmethod
    def validate_performance_filters(df: pd.DataFrame, performance_filters: Dict, position: str) -> pd.DataFrame:
        """Apply dynamic performance filters"""

        if df.empty or not performance_filters:
            return df

        result_df = df.copy()

        for filter_name, filter_value in performance_filters.items():
            if filter_value <= 0:  # Skip zero/empty filters
                continue

            # Extract metric name from filter name (remove 'min_' prefix)
            if filter_name.startswith('min_'):
                metric_name = filter_name[4:]  # Remove 'min_' prefix

                if metric_name in result_df.columns:
                    # Convert to numeric and apply filter
                    numeric_values = pd.to_numeric(result_df[metric_name], errors='coerce')
                    result_df = result_df[numeric_values >= filter_value]

        return result_df