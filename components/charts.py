import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional


class ScoutingCharts:
    """Component for scouting-related charts and visualizations"""

    @staticmethod
    def show_radar_comparison(players_data: List[Dict], metrics: List[str],
                              position: str, title: str = "Player Comparison") -> None:
        """Show radar chart comparing multiple players"""

        if not players_data or not metrics:
            st.warning("No data available for radar chart")
            return

        # Create radar chart
        fig = go.Figure()

        # Color palette for players
        colors = ['rgb(79, 70, 229)', 'rgb(239, 68, 68)', 'rgb(34, 197, 94)', 'rgb(251, 191, 36)', 'rgb(168, 85, 247)']

        for i, player_data in enumerate(players_data[:5]):  # Max 5 players
            player_name = player_data.get('Player', 'Unknown')

            # Extract percentile values for radar
            percentile_values = []
            metric_labels = []

            for metric in metrics:
                percentile_key = f'{metric}_percentile'
                if percentile_key in player_data:
                    percentile_values.append(player_data[percentile_key])
                    # Shorten metric names for better display
                    short_name = ScoutingCharts._shorten_metric_name(metric)
                    metric_labels.append(short_name)

            if percentile_values:
                # Close the polygon
                percentile_values.append(percentile_values[0])
                metric_labels.append(metric_labels[0])

                # Add trace
                fig.add_trace(go.Scatterpolar(
                    r=percentile_values,
                    theta=metric_labels,
                    fill='toself',
                    name=player_name,
                    line_color=colors[i % len(colors)],
                    fillcolor=colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)')
                ))

        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickmode='linear',
                    tick0=0,
                    dtick=20,
                    showline=True,
                    linewidth=1,
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=10)
                )
            ),
            showlegend=True,
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16)
            ),
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show radar explanation
        with st.expander("📖 How to Read This Chart"):
            st.markdown(f"""
            **Radar Chart Explanation:**

            - Each axis represents a key performance metric for {position} players
            - Values are shown as **percentiles** (0-100) compared to all {position} players
            - **Higher values = better performance** for that metric
            - The colored area shows each player's overall profile
            - **Larger area = better overall performance**

            **Percentile Scale:**
            - **90-100**: Elite performance (top 10%)
            - **75-89**: Very good performance (top 25%)
            - **50-74**: Above average performance 
            - **25-49**: Below average performance
            - **0-24**: Poor performance (bottom 25%)
            """)

    @staticmethod
    def show_percentile_bars(player_data: Dict, metrics: List[str], player_name: str) -> None:
        """Show horizontal bar chart of percentiles for a single player"""

        percentiles = []
        metric_names = []

        for metric in metrics:
            percentile_key = f'{metric}_percentile'
            if percentile_key in player_data:
                percentiles.append(player_data[percentile_key])
                metric_names.append(ScoutingCharts._shorten_metric_name(metric))

        if not percentiles:
            st.warning("No percentile data available")
            return

        # Create horizontal bar chart
        fig = go.Figure()

        # Color bars based on percentile value
        colors = []
        for p in percentiles:
            if p >= 90:
                colors.append('#22c55e')  # Green - Elite
            elif p >= 75:
                colors.append('#3b82f6')  # Blue - Very Good
            elif p >= 50:
                colors.append('#f59e0b')  # Orange - Above Average
            elif p >= 25:
                colors.append('#ef4444')  # Red - Below Average
            else:
                colors.append('#6b7280')  # Gray - Poor

        fig.add_trace(go.Bar(
            y=metric_names,
            x=percentiles,
            orientation='h',
            marker=dict(color=colors),
            text=[f"{p:.0f}" for p in percentiles],
            textposition='outside'
        ))

        fig.update_layout(
            title=f"{player_name} - Performance Percentiles",
            xaxis_title="Percentile (0-100)",
            yaxis_title="Metrics",
            height=400,
            showlegend=False,
            xaxis=dict(range=[0, 105])
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def show_scatter_plot(df: pd.DataFrame, x_metric: str, y_metric: str,
                          color_by: str = None, size_by: str = None,
                          highlight_players: List[str] = None) -> None:
        """Show scatter plot of two metrics"""

        if df.empty or x_metric not in df.columns or y_metric not in df.columns:
            st.warning(f"Cannot create scatter plot - missing data for {x_metric} or {y_metric}")
            return

        # Prepare data
        plot_df = df.copy()

        # Convert metrics to numeric
        plot_df[x_metric] = pd.to_numeric(plot_df[x_metric], errors='coerce')
        plot_df[y_metric] = pd.to_numeric(plot_df[y_metric], errors='coerce')

        # Remove NaN values
        plot_df = plot_df.dropna(subset=[x_metric, y_metric])

        if plot_df.empty:
            st.warning("No valid data points for scatter plot")
            return

        # Create scatter plot
        fig = px.scatter(
            plot_df,
            x=x_metric,
            y=y_metric,
            color=color_by if color_by and color_by in plot_df.columns else None,
            size=size_by if size_by and size_by in plot_df.columns else None,
            hover_data=['Jogador', 'Time', 'Idade'] if 'Jogador' in plot_df.columns else None,
            title=f"{ScoutingCharts._shorten_metric_name(y_metric)} vs {ScoutingCharts._shorten_metric_name(x_metric)}"
        )

        # Highlight specific players if provided
        if highlight_players and 'Jogador' in plot_df.columns:
            highlight_df = plot_df[plot_df['Jogador'].isin(highlight_players)]
            if not highlight_df.empty:
                fig.add_trace(go.Scatter(
                    x=highlight_df[x_metric],
                    y=highlight_df[y_metric],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color='red',
                        symbol='star',
                        line=dict(width=2, color='white')
                    ),
                    name='Highlighted Players',
                    text=highlight_df['Jogador'],
                    hovertemplate='<b>%{text}</b><br>%{xaxis.title.text}: %{x}<br>%{yaxis.title.text}: %{y}<extra></extra>'
                ))

        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def show_distribution_plot(df: pd.DataFrame, metric: str, highlight_value: float = None,
                               highlight_label: str = None) -> None:
        """Show distribution histogram for a metric"""

        if df.empty or metric not in df.columns:
            st.warning(f"Cannot create distribution plot - missing data for {metric}")
            return

        # Convert to numeric and remove NaN
        values = pd.to_numeric(df[metric], errors='coerce').dropna()

        if values.empty:
            st.warning("No valid data for distribution plot")
            return

        # Create histogram
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=values,
            nbinsx=20,
            name='Distribution',
            opacity=0.7,
            marker=dict(color='skyblue', line=dict(color='black', width=1))
        ))

        # Add vertical line for highlight value
        if highlight_value is not None:
            fig.add_vline(
                x=highlight_value,
                line_dash="dash",
                line_color="red",
                annotation_text=highlight_label or "Selected Player",
                annotation_position="top"
            )

        fig.update_layout(
            title=f"Distribution of {ScoutingCharts._shorten_metric_name(metric)}",
            xaxis_title=ScoutingCharts._shorten_metric_name(metric),
            yaxis_title="Number of Players",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def show_rankings_table(df: pd.DataFrame, ranking_metrics: List[str],
                            show_percentiles: bool = True, max_rows: int = 20) -> None:
        """Show rankings table with formatting"""

        if df.empty:
            st.warning("No data available for rankings table")
            return

        # Prepare display dataframe
        display_df = df.copy()

        # Select columns to display
        base_columns = ['Jogador', 'Time', 'Idade', 'Minutos jogados']

        # Add ranking metrics
        metric_columns = []
        for metric in ranking_metrics:
            if metric in display_df.columns:
                metric_columns.append(metric)

            # Add percentile column if requested
            if show_percentiles:
                percentile_col = f'{metric}_percentile'
                if percentile_col in display_df.columns:
                    metric_columns.append(percentile_col)

        # Add overall score if available
        if 'Overall_Score' in display_df.columns:
            metric_columns.insert(0, 'Overall_Score')

        # Select final columns
        final_columns = base_columns + metric_columns
        display_columns = [col for col in final_columns if col in display_df.columns]

        display_df = display_df[display_columns].head(max_rows)

        # Format column names for display
        column_renames = {}
        for col in display_df.columns:
            if col.endswith('_percentile'):
                base_name = col.replace('_percentile', '')
                short_name = ScoutingCharts._shorten_metric_name(base_name)
                column_renames[col] = f"{short_name} %ile"
            else:
                column_renames[col] = ScoutingCharts._format_column_name(col)

        display_df = display_df.rename(columns=column_renames)

        # Add ranking numbers
        display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

        # Format numeric columns
        for col in display_df.columns:
            if col in ['Overall Score', 'Minutes Played', 'Age']:
                display_df[col] = display_df[col].astype(int)
            elif col.endswith('%ile') or col.endswith('Score'):
                display_df[col] = display_df[col].round(1)
            elif display_df[col].dtype in ['float64', 'float32']:
                display_df[col] = display_df[col].round(2)

        # Display table with styling
        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(600, len(display_df) * 35 + 100),
            column_config={
                'Rank': st.column_config.NumberColumn('Rank', width="small"),
                'Player': st.column_config.TextColumn('Player', width="medium"),
                'Team': st.column_config.TextColumn('Team', width="medium"),
            }
        )

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
            'Overall_Score': 'Overall Score',
            'Defesas': 'Saves',
            'Defesas, %': 'Save %',
            'Gols sofridos': 'Goals Conceded',
            'Desarmes': 'Tackles',
            'Interceptações': 'Interceptions',
            'Dribles': 'Dribbles',
            'Cruzamentos': 'Crosses',
            'xG': 'Expected Goals',
            'xA': 'Expected Assists',
            'Gols': 'Goals',
            'Assistências': 'Assists',
            'Chutes': 'Shots',
            'Faltas': 'Fouls'
        }

        return shortenings.get(metric, metric)

    @staticmethod
    def _format_column_name(column: str) -> str:
        """Format column names for display"""

        formatting = {
            'Jogador': 'Player',
            'Time': 'Team',
            'Idade': 'Age',
            'Nacionalidade': 'Nationality',
            'Minutos jogados': 'Minutes',
            'Partidas jogadas': 'Matches',
            'Overall_Score': 'Overall Score'
        }

        return formatting.get(column, column)

    @staticmethod
    def show_metric_trends(df: pd.DataFrame, metric: str, group_by: str = 'Idade') -> None:
        """Show trend of metric by age or other grouping"""

        if df.empty or metric not in df.columns or group_by not in df.columns:
            st.warning(f"Cannot create trend plot - missing data")
            return

        # Prepare data
        plot_df = df.copy()
        plot_df[metric] = pd.to_numeric(plot_df[metric], errors='coerce')
        plot_df[group_by] = pd.to_numeric(plot_df[group_by], errors='coerce')

        # Remove NaN values
        plot_df = plot_df.dropna(subset=[metric, group_by])

        if plot_df.empty:
            st.warning("No valid data for trend plot")
            return

        # Group and calculate averages
        grouped = plot_df.groupby(group_by)[metric].agg(['mean', 'count']).reset_index()
        grouped = grouped[grouped['count'] >= 3]  # Only show groups with at least 3 players

        if grouped.empty:
            st.warning("Not enough data points for trend plot")
            return

        # Create line plot
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=grouped[group_by],
            y=grouped['mean'],
            mode='lines+markers',
            name=f'Average {ScoutingCharts._shorten_metric_name(metric)}',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title=f"{ScoutingCharts._shorten_metric_name(metric)} by {group_by}",
            xaxis_title=group_by,
            yaxis_title=f"Average {ScoutingCharts._shorten_metric_name(metric)}",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def show_comparison_summary(comparison_players: List[Dict]) -> None:
        """Show summary cards for comparison players"""

        if not comparison_players:
            return

        st.markdown("### 👥 Players in Comparison")

        # Create columns for each player
        cols = st.columns(len(comparison_players))

        for i, (col, player) in enumerate(zip(cols, comparison_players)):
            with col:
                # Player card
                st.markdown(f"""
                <div style="
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    padding: 10px;
                    text-align: center;
                    background-color: rgba(59, 130, 246, 0.1);
                ">
                    <h4>{player['name']}</h4>
                    <p><strong>{player['team']}</strong></p>
                    <p>Age: {player['age']} | {player['position']}</p>
                    <p>Minutes: {player['minutes']}</p>
                    <p>Score: {player['overall_score']:.1f}</p>
                </div>
                """, unsafe_allow_html=True)