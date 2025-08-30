import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class TacticalField:
    """Component for displaying tactical formations on a football field"""

    def __init__(self, width=400, height=600):
        self.width = width
        self.height = height

    def create_field_layout(self):
        """Create basic football field layout"""
        fig = go.Figure()

        # Field dimensions (normalized 0-100 scale)
        field_width = 100
        field_height = 100

        # Field outline
        fig.add_shape(
            type="rect",
            x0=0, y0=0, x1=field_width, y1=field_height,
            line=dict(color="white", width=2),
            fillcolor="rgba(34, 139, 34, 0.1)"
        )

        # Center circle
        fig.add_shape(
            type="circle",
            x0=40, y0=40, x1=60, y1=60,
            line=dict(color="white", width=2),
            fillcolor="rgba(0,0,0,0)"
        )

        # Center line
        fig.add_shape(
            type="line",
            x0=0, y0=50, x1=field_width, y1=50,
            line=dict(color="white", width=2)
        )

        # Penalty areas
        # Top penalty area
        fig.add_shape(
            type="rect",
            x0=20, y0=85, x1=80, y1=100,
            line=dict(color="white", width=2),
            fillcolor="rgba(0,0,0,0)"
        )

        # Bottom penalty area
        fig.add_shape(
            type="rect",
            x0=20, y0=0, x1=80, y1=15,
            line=dict(color="white", width=2),
            fillcolor="rgba(0,0,0,0)"
        )

        # Goal areas
        # Top goal area
        fig.add_shape(
            type="rect",
            x0=40, y0=92, x1=60, y1=100,
            line=dict(color="white", width=2),
            fillcolor="rgba(0,0,0,0)"
        )

        # Bottom goal area
        fig.add_shape(
            type="rect",
            x0=40, y0=0, x1=60, y1=8,
            line=dict(color="white", width=2),
            fillcolor="rgba(0,0,0,0)"
        )

        # Configure layout
        fig.update_layout(
            width=self.width,
            height=self.height,
            showlegend=False,
            xaxis=dict(
                range=[0, field_width],
                showgrid=False,
                showticklabels=False,
                zeroline=False
            ),
            yaxis=dict(
                range=[0, field_height],
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                scaleanchor="x",
                scaleratio=1
            ),
            plot_bgcolor='rgba(34, 139, 34, 0.8)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )

        return fig

    def add_player_positions(self, fig, formation_data: dict):
        """Add player positions to the field"""

        # Position coordinates for different formations
        position_coords = self._get_formation_coordinates()

        colors = {
            'GK': '#FFD700',  # Gold
            'DEF': '#FF6B6B',  # Red
            'MID': '#4ECDC4',  # Teal
            'ATT': '#45B7D1'  # Blue
        }

        for line, players in formation_data.items():
            if players and line in position_coords:
                coords = position_coords[line]
                player_count = len(players)

                # Distribute players across the line
                if player_count == 1:
                    positions = [coords['center']]
                else:
                    # Spread players evenly across the line
                    start_x = coords['left']
                    end_x = coords['right']
                    x_positions = [start_x + (end_x - start_x) * i / (player_count - 1)
                                   for i in range(player_count)]
                    positions = [(x, coords['y']) for x in x_positions]

                # Add players to field
                for i, (player, pos) in enumerate(zip(players, positions)):
                    self._add_player_marker(
                        fig,
                        pos[0], pos[1],
                        player['name'],
                        colors.get(line, '#FFFFFF')
                    )

        return fig

    def _get_formation_coordinates(self):
        """Get default coordinates for each line of the formation"""
        return {
            'GK': {
                'center': (50, 10),
                'left': 50,
                'right': 50,
                'y': 10
            },
            'DEF': {
                'center': (50, 25),
                'left': 20,
                'right': 80,
                'y': 25
            },
            'MID': {
                'center': (50, 45),
                'left': 15,
                'right': 85,
                'y': 45
            },
            'ATT': {
                'center': (50, 70),
                'left': 25,
                'right': 75,
                'y': 70
            }
        }

    def _add_player_marker(self, fig, x, y, name, color):
        """Add a player marker to the field"""

        # Add player circle
        fig.add_scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=30,
                color=color,
                line=dict(color='white', width=2)
            ),
            text=[name],
            textposition="bottom center",
            textfont=dict(color='white', size=10),
            showlegend=False,
            hovertemplate=f"<b>{name}</b><extra></extra>"
        )

    def show_formation(self, formation_data: dict, title: str = "Starting Formation"):
        """Display formation on field"""

        st.subheader(title)

        # Create field
        fig = self.create_field_layout()

        # Add players
        fig = self.add_player_positions(fig, formation_data)

        # Show field
        st.plotly_chart(fig, use_container_width=True)

        # Show formation summary
        self._show_formation_summary(formation_data)

    def _show_formation_summary(self, formation_data: dict):
        """Show formation summary below the field"""

        formation_str = []

        for line in ['DEF', 'MID', 'ATT']:
            if line in formation_data and formation_data[line]:
                formation_str.append(str(len(formation_data[line])))

        if formation_str:
            st.info(f"🏟️ Formation: {'-'.join(formation_str)}")

        # Player counts by line
        col1, col2, col3, col4 = st.columns(4)

        lines = [
            ('🥅 GK', 'GK'),
            ('🛡️ DEF', 'DEF'),
            ('⚽ MID', 'MID'),
            ('🎯 ATT', 'ATT')
        ]

        for col, (label, line) in zip([col1, col2, col3, col4], lines):
            with col:
                count = len(formation_data.get(line, []))
                st.metric(label, count)


class FormationBuilder:
    """Helper class for building formations"""

    @staticmethod
    def build_formation(squad_data: dict, formation_type: str = "4-4-2"):
        """Build formation from squad data"""

        formation_configs = {
            "4-4-2": {
                'DEF': 4,
                'MID': 4,
                'ATT': 2
            },
            "4-3-3": {
                'DEF': 4,
                'MID': 3,
                'ATT': 3
            },
            "3-5-2": {
                'DEF': 3,
                'MID': 5,
                'ATT': 2
            },
            "4-2-3-1": {
                'DEF': 4,
                'MID': 5,  # 2 DM + 3 AM
                'ATT': 1
            }
        }

        config = formation_configs.get(formation_type, formation_configs["4-4-2"])
        formation = {'GK': [], 'DEF': [], 'MID': [], 'ATT': []}

        # Add goalkeeper
        if 'GK' in squad_data:
            formation['GK'] = squad_data['GK'][:1]

        # Add outfield players
        for line, count in config.items():
            if line in squad_data:
                formation[line] = squad_data[line][:count]

        return formation

    @staticmethod
    def get_available_formations():
        """Get list of available formations"""
        return ["4-4-2", "4-3-3", "3-5-2", "4-2-3-1"]