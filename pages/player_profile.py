import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List


def show_player_profile():
    """Display detailed player profile page"""

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("⚠️ Please upload data and select a team first!")
        return

    # Check if player is selected
    if not st.session_state.get('selected_player'):
        st.title("👤 Player Profile")
        st.info("👆 Select a player from the Team Dashboard or Scouting page to view their profile!")

        # Back button
        if st.button("🏠 Back to Team Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        return

    player_name = st.session_state.selected_player['name']
    position = st.session_state.selected_player['position']

    # Get player data
    player_data = st.session_state.data_processor.get_player_data(player_name, position)

    if player_data is None:
        st.error(f"Player {player_name} not found in {position} data!")
        return

    # Page header
    st.title(f"👤 Player Profile")
    st.subheader(f"{player_name} ({position})")

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()

    with col2:
        if st.button("🔍 Back to Scouting"):
            st.session_state.current_page = 'scouting'
            st.rerun()

    with col3:
        # Add to favorites button
        if st.button("⭐ Add to Favorites", key="add_to_favorites"):
            try:
                if 'favorites_manager' not in st.session_state:
                    from src.favorites_manager import FavoritesManager
                    st.session_state.favorites_manager = FavoritesManager(st.session_state.data_processor)

                favorites_manager = st.session_state.favorites_manager

                if favorites_manager.add_to_favorites(
                        player_name,
                        position,
                        reason="Added from player profile",
                        collection="Player Profiles"
                ):
                    st.success(f"✅ {player_name} added to favorites!")
                else:
                    st.warning(f"⚠️ {player_name} is already in favorites or could not be added")
            except Exception as e:
                st.error(f"Error adding to favorites: {str(e)}")

    st.divider()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "📊 Statistics", "📈 Performance", "🎯 Radar Chart"])

    with tab1:
        show_player_overview(player_data, position)

    with tab2:
        show_player_statistics_updated(player_data, position)

    with tab3:
        show_performance_analysis_updated(player_data, position)

    with tab4:
        show_customizable_radar_chart_fixed(player_data, position)


def show_player_overview(player_data: pd.Series, position: str):
    """Show player overview with basic info and key metrics"""

    # Personal Information
    st.subheader("ℹ️ Personal Information")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Age", f"{player_data.get('Idade', 'N/A')} years")

    with col2:
        st.metric("Height", player_data.get('Altura', 'N/A'))

    with col3:
        st.metric("Nationality", player_data.get('Nacionalidade', 'N/A'))

    with col4:
        st.metric("Preferred Foot", player_data.get('Pé', 'N/A'))

    with col5:
        st.metric("Market Value", player_data.get('Valor de mercado', 'N/A'))

    st.markdown("---")

    # Playing Time
    st.subheader("⏱️ Playing Time")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        minutes = int(player_data.get('Minutos jogados', 0))
        st.metric("Minutes Played", f"{minutes:,}")

    with col2:
        matches = int(player_data.get('Partidas jogadas', 0))
        st.metric("Matches Played", matches)

    with col3:
        avg_minutes = round(minutes / matches, 1) if matches > 0 else 0
        st.metric("Minutes per Match", avg_minutes)

    with col4:
        # Playing time consistency
        if matches > 0:
            consistency = min(100, (minutes / (matches * 90)) * 100)
            st.metric("Playing Time %", f"{consistency:.1f}%")
        else:
            st.metric("Playing Time %", "0.0%")

    st.markdown("---")

    # Key Performance Metrics
    st.subheader("⚽ Key Performance Metrics")

    show_key_metrics_by_position_updated(player_data, position)


def show_key_metrics_by_position_updated(player_data: pd.Series, position: str):
    """Show position-specific key metrics (UPDATED VERSION with 5 metrics each)"""

    minutes = player_data.get('Minutos jogados', 0)

    if position == 'GR':
        # Goalkeeper: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            save_pct = player_data.get('Defesas, %', 0)
            if isinstance(save_pct, str) and '%' in str(save_pct):
                try:
                    pct_value = float(str(save_pct).replace('%', ''))
                    st.metric("Save %", f"{pct_value:.1f}%")
                except:
                    st.metric("Save %", str(save_pct))
            else:
                try:
                    st.metric("Save %", f"{float(save_pct):.1f}%")
                except:
                    st.metric("Save %", "0.0%")

        with col2:
            pass_pct = player_data.get('Passes precisos %', 0)
            if isinstance(pass_pct, str) and '%' in str(pass_pct):
                try:
                    pct_value = float(str(pass_pct).replace('%', ''))
                    st.metric("Pass Accuracy %", f"{pct_value:.1f}%")
                except:
                    st.metric("Pass Accuracy %", str(pass_pct))
            else:
                try:
                    st.metric("Pass Accuracy %", f"{float(pass_pct):.1f}%")
                except:
                    st.metric("Pass Accuracy %", "0.0%")

        with col3:
            acoes_sucesso = player_data.get('Ações / com sucesso', 0)
            acoes_total = player_data.get('Ações', acoes_sucesso)
            acoes_pct = (acoes_sucesso / acoes_total * 100) if acoes_total > 0 else 0
            st.metric("Actions Success %", f"{acoes_pct:.1f}%")

        with col4:
            goals_conceded = player_data.get('Gols sofridos', 0)
            goals_per90 = (goals_conceded * 90 / minutes) if minutes > 0 else 0
            st.metric("Goals Conceded /90", f"{goals_per90:.2f}")

        with col5:
            saves = player_data.get('Defesas', 0)
            saves_per90 = (saves * 90 / minutes) if minutes > 0 else 0
            st.metric("Saves /90", f"{saves_per90:.2f}")

    elif position in ['DCE', 'DCD']:
        # Centre-Back: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            tackles = player_data.get('Desarmes', 0)
            tackles_per90 = (tackles * 90 / minutes) if minutes > 0 else 0
            st.metric("Tackles /90", f"{tackles_per90:.2f}")

        with col2:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col3:
            tackles_successful = player_data.get('Desarmes bem-sucedidos', tackles)
            tackle_success_pct = (tackles_successful / tackles * 100) if tackles > 0 else 0
            st.metric("Tackle Success %", f"{tackle_success_pct:.1f}%")

        with col4:
            aerial_duels = player_data.get('Disputas aéreas', 0)
            aerial_won = player_data.get('Disputas aéreas ganhas', aerial_duels)
            aerial_pct = (aerial_won / aerial_duels * 100) if aerial_duels > 0 else 0
            st.metric("Aerial Duels Won %", f"{aerial_pct:.1f}%")

        with col5:
            ball_recoveries = player_data.get('Bolas recuperadas', 0)
            recoveries_per90 = (ball_recoveries * 90 / minutes) if minutes > 0 else 0
            st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")

    elif position in ['DE', 'DD']:
        # Full-Back: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            crosses = player_data.get('Cruzamentos', 0)
            crosses_per90 = (crosses * 90 / minutes) if minutes > 0 else 0
            st.metric("Crosses /90", f"{crosses_per90:.2f}")

        with col2:
            crosses_accurate = player_data.get('Cruzamentos precisos', 0)
            cross_accuracy = (crosses_accurate / crosses * 100) if crosses > 0 else 0
            st.metric("Cross Accuracy %", f"{cross_accuracy:.1f}%")

        with col3:
            prog_passes = player_data.get('Passes progressivos', 0)
            prog_per90 = (prog_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Progressive Passes /90", f"{prog_per90:.2f}")

        with col4:
            def_duels = player_data.get('Disputas na defesa', 0)
            def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
            def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
            st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")

        with col5:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

    elif position == 'MCD':
        # Defensive Midfielder: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            recoveries = player_data.get('Bolas recuperadas', 0)
            rec_per90 = (recoveries * 90 / minutes) if minutes > 0 else 0
            st.metric("Ball Recoveries /90", f"{rec_per90:.2f}")

        with col2:
            tackles = player_data.get('Desarmes', 0)
            tackles_per90 = (tackles * 90 / minutes) if minutes > 0 else 0
            st.metric("Tackles /90", f"{tackles_per90:.2f}")

        with col3:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col4:
            def_duels = player_data.get('Disputas na defesa', 0)
            def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
            def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
            st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")

        with col5:
            prog_passes = player_data.get('Passes progressivos', 0)
            prog_per90 = (prog_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Progressive Passes /90", f"{prog_per90:.2f}")

    elif position == 'MC':
        # Central Midfielder: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            def_duels = player_data.get('Disputas na defesa', 0)
            def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
            def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
            st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")

        with col2:
            interceptions = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
            inter_per90 = (interceptions * 90 / minutes) if minutes > 0 else 0
            st.metric("Interceptions /90", f"{inter_per90:.2f}")

        with col3:
            prog_passes = player_data.get('Passes progressivos', 0)
            prog_per90 = (prog_passes * 90 / minutes) if minutes > 0 else 0
            st.metric("Progressive Passes /90", f"{prog_per90:.2f}")

        with col4:
            ball_recoveries = player_data.get('Bolas recuperadas', 0)
            rec_per90 = (ball_recoveries * 90 / minutes) if minutes > 0 else 0
            st.metric("Ball Recoveries /90", f"{rec_per90:.2f}")

        with col5:
            pass_pct = player_data.get('Passes precisos %', 0)
            if isinstance(pass_pct, str) and '%' in str(pass_pct):
                try:
                    pct_value = float(str(pass_pct).replace('%', ''))
                    st.metric("Pass Accuracy %", f"{pct_value:.1f}%")
                except:
                    st.metric("Pass Accuracy %", str(pass_pct))
            else:
                try:
                    st.metric("Pass Accuracy %", f"{float(pass_pct):.1f}%")
                except:
                    st.metric("Pass Accuracy %", "0.0%")

    elif position in ['EE', 'ED']:
        # Winger: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            final_third_dribbles = player_data.get('Dribles no último terço do campo com sucesso', 0)
            total_final_third = player_data.get('Dribles no último terço do campo', final_third_dribbles)
            dribbles_pct = (final_third_dribbles / total_final_third * 100) if total_final_third > 0 else 0
            st.metric("Final 3rd Dribbles Success %", f"{dribbles_pct:.1f}%")

        with col2:
            crosses = player_data.get('Cruzamentos', 0)
            crosses_per90 = (crosses * 90 / minutes) if minutes > 0 else 0
            st.metric("Crosses /90", f"{crosses_per90:.2f}")

        with col3:
            xa = player_data.get('xA', 0)
            st.metric("xA", f"{xa:.2f}")

        with col4:
            key_passes = player_data.get('Passes chave', 0)
            key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
            key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
            st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")

        with col5:
            shots_on_target = player_data.get('Chutes no gol', 0)
            total_shots = player_data.get('Chutes', shots_on_target)
            shots_pct = (shots_on_target / total_shots * 100) if total_shots > 0 else 0
            st.metric("Shots on Target %", f"{shots_pct:.1f}%")

    elif position == 'PL':
        # Forward: 5 metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            goals = player_data.get('Gols', 0)
            goals_per90 = (goals * 90 / minutes) if minutes > 0 else 0
            st.metric("Goals /90", f"{goals_per90:.2f}")

        with col2:
            xg = player_data.get('xG', 0)
            st.metric("xG", f"{xg:.2f}")

        with col3:
            shots_on_target = player_data.get('Chutes no gol', 0)
            total_shots = player_data.get('Chutes', shots_on_target)
            shots_pct = (shots_on_target / total_shots * 100) if total_shots > 0 else 0
            st.metric("Shots on Target %", f"{shots_pct:.1f}%")

        with col4:
            headed_goals = player_data.get('Gols de cabeça', 0)
            st.metric("Headed Goals", f"{headed_goals}")

        with col5:
            xa = player_data.get('xA', 0)
            st.metric("xA", f"{xa:.2f}")


def show_player_statistics_updated(player_data: pd.Series, position: str):
    """Show detailed player statistics with position-specific categories (UPDATED VERSION)"""

    st.subheader("📊 Detailed Statistics")

    minutes = player_data.get('Minutos jogados', 0)

    if position == 'GR':
        show_goalkeeper_stats(player_data, minutes)
    elif position in ['DCE', 'DCD']:
        show_centreback_stats(player_data, minutes)
    elif position in ['DE', 'DD']:
        show_fullback_stats(player_data, minutes)
    elif position == 'MCD':
        show_defensive_midfielder_stats(player_data, minutes)
    elif position == 'MC':
        show_central_midfielder_stats(player_data, minutes)
    elif position in ['EE', 'ED']:
        show_winger_stats(player_data, minutes)
    elif position == 'PL':
        show_forward_stats(player_data, minutes)


def show_goalkeeper_stats(player_data: pd.Series, minutes: int):
    """Show goalkeeper-specific statistics"""

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Opponent Shots", player_data.get('Chutes do adversário', 0))
    with col2:
        st.metric("Shots on Goal Against", player_data.get('Chutes do adversário no gol', 0))
    with col3:
        st.metric("Goals Conceded", player_data.get('Gols sofridos', 0))
    with col4:
        st.metric("Saves", player_data.get('Defesas', 0))

    col1, col2, col3 = st.columns(3)
    with col1:
        save_pct = player_data.get('Defesas, %', 0)
        st.metric("Save %", f"{save_pct}%")
    with col2:
        st.metric("Difficult Saves", player_data.get('Defesas difíceis', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Passes", player_data.get('Passes', 0))
    with col2:
        st.metric("Accurate Passes", player_data.get('Passes precisos', 0))
    with col3:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col4:
        st.metric("Key Passes", player_data.get('Passes chave', 0))

    # PER 90
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        saves_per90 = (player_data.get('Defesas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Saves /90", f"{saves_per90:.2f}")
    with col2:
        difficult_saves_per90 = (player_data.get('Defesas difíceis', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Difficult Saves /90", f"{difficult_saves_per90:.2f}")
    with col3:
        goals_conceded_per90 = (player_data.get('Gols sofridos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Goals Conceded /90", f"{goals_conceded_per90:.2f}")
    with col4:
        accurate_passes_per90 = (player_data.get('Passes precisos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Accurate Passes /90", f"{accurate_passes_per90:.2f}")
    with col5:
        key_passes_per90 = (player_data.get('Passes chave', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Key Passes /90", f"{key_passes_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cross/Pass Interception Attempts",
                  player_data.get('Tentativas de interceptação de cruzamento e passe', 0))
    with col2:
        st.metric("Successful Cross/Pass Interceptions",
                  player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0))
    with col3:
        attempts = player_data.get('Tentativas de interceptação de cruzamento e passe', 0)
        successful = player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0)
        success_pct = (successful / attempts * 100) if attempts > 0 else 0
        st.metric("Cross/Pass Interception Success %", f"{success_pct:.1f}%")


def show_centreback_stats(player_data: pd.Series, minutes: int):
    """Show centre-back specific statistics"""

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        st.metric("Fouls Committed", player_data.get('Faltas cometidas', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col3:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col4:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col5:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        final_third_dribbles_per90 = (player_data.get('Dribles no último terço do campo com sucesso',
                                                      0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Final Third Dribbles Success /90", f"{final_third_dribbles_per90:.2f}")
    with col2:
        crosses_per90 = (player_data.get('Cruzamentos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Crosses /90", f"{crosses_per90:.2f}")
    with col3:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col4:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")
    with col5:
        shots_per90 = (player_data.get('Chutes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Shots /90", f"{shots_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xA", player_data.get('xA', 0))
    with col2:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col3:
        st.metric("Passes into Box", player_data.get('Passes para a área', 0))
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def show_forward_stats(player_data: pd.Series, minutes: int):
    """Show forward specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        goals_per90 = (player_data.get('Gols', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Goals /90", f"{goals_per90:.2f}")
    with col2:
        st.metric("Headed Goals", player_data.get('Gols de cabeça', 0))
    with col3:
        shots = player_data.get('Chutes', 0)
        shots_on_target = player_data.get('Chutes no gol', 0)
        shots_pct = (shots_on_target / shots * 100) if shots > 0 else 0
        st.metric("Shots on Target %", f"{shots_pct:.1f}%")
    with col4:
        chances = player_data.get('Chances criadas', 0)
        chances_successful = player_data.get('Chances bem-sucedidas', chances)
        chances_pct = (chances_successful / chances * 100) if chances > 0 else 0
        st.metric("Chances Success %", f"{chances_pct:.1f}%")
    with col5:
        st.metric("xG", player_data.get('xG', 0))

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        st.metric("Fouls Committed", player_data.get('Faltas cometidas', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col2:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        st.metric("Assists", player_data.get('Assistências', 0))
    with col5:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        goals_per90 = (player_data.get('Gols', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Goals /90", f"{goals_per90:.2f}")
    with col2:
        shots_per90 = (player_data.get('Chutes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Shots /90", f"{shots_per90:.2f}")
    with col3:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col4:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")
    with col5:
        final_third_dribbles_per90 = (player_data.get('Dribles no último terço do campo com sucesso',
                                                      0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Final Third Dribbles Success /90", f"{final_third_dribbles_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xG", player_data.get('xG', 0))
    with col2:
        st.metric("xA", player_data.get('xA', 0))
    with col3:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col4:
        st.metric("Chances Created", player_data.get('Chances criadas', 0))
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def get_key_performance_metrics_for_position(position: str) -> List[str]:
    """Get 5 key performance metrics for comparison by position (UPDATED VERSION)"""

    metrics = {
        'GR': [
            'Defesas',  # for Defesas /90
            'Defesas difíceis',  # for Defesas difíceis /90
            'Gols sofridos',  # for Gols sofridos /90
            'Passes precisos',  # for Passes precisos /90
            'Passes chave'  # for Passes chave /90
        ],
        'DCE': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Rebotes',  # for Rebotes /90
            'Dribles',  # for Dribles /90
            'Passes progressivos'  # for Passes progressivos /90
        ],
        'DCD': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Rebotes',  # for Rebotes /90
            'Dribles',  # for Dribles /90
            'Passes progressivos'  # for Passes progressivos /90
        ],
        'DE': [
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Desarmes'  # for Desarmes /90
        ],
        'DD': [
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Desarmes'  # for Desarmes /90
        ],
        'MCD': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes'  # for Passes /90
        ],
        'MC': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes'  # for Passes /90
        ],
        'EE': [
            'Dribles no último terço do campo com sucesso',  # for Dribles no último terço /90
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes',  # for Passes /90
            'Chutes'  # for Chutes /90
        ],
        'ED': [
            'Dribles no último terço do campo com sucesso',  # for Dribles no último terço /90
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes',  # for Passes /90
            'Chutes'  # for Chutes /90
        ],
        'PL': [
            'Gols',  # for Gols /90
            'Chutes',  # for Chutes /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes',  # for Passes /90
            'Dribles no último terço do campo com sucesso'  # for Dribles no último terço /90
        ]
    }

    return metrics.get(position, ['Passes', 'Passes precisos', 'Faltas', 'Ações / com sucesso'])


def show_performance_analysis_updated(player_data: pd.Series, position: str):
    """Show performance analysis with comparisons (UPDATED VERSION)"""

    # Main section header
    st.subheader("📈 Performance Analysis")
    st.markdown("---")

    # Position comparison section
    st.markdown("## 🔄 vs Position Average")

    # Get position averages for comparison
    team_players = st.session_state.data_processor.get_team_players(st.session_state.selected_team)

    if position in team_players:
        position_df = team_players[position]

        # Key metrics for comparison (5 metrics per position)
        key_metrics = get_key_performance_metrics_for_position(position)

        comparison_data = []

        for metric in key_metrics:
            if metric in player_data.index and metric in position_df.columns:
                player_value = player_data[metric]

                # Convert metric column to numeric, handling strings
                try:
                    position_series = pd.to_numeric(position_df[metric], errors='coerce')
                    position_avg = position_series.mean()

                    # Convert player value to numeric
                    player_value_numeric = pd.to_numeric(player_value, errors='coerce')

                    if pd.notna(player_value_numeric) and pd.notna(position_avg):
                        # Calculate per 90 values
                        minutes = player_data.get('Minutos jogados', 0)
                        player_per90 = (player_value_numeric * 90 / minutes) if minutes > 0 else 0

                        # Calculate average per 90 for position
                        position_minutes = pd.to_numeric(position_df['Minutos jogados'], errors='coerce')
                        position_per90_values = []
                        for idx, (val, mins) in enumerate(zip(position_series, position_minutes)):
                            if pd.notna(val) and pd.notna(mins) and mins > 0:
                                position_per90_values.append(val * 90 / mins)

                        position_avg_per90 = sum(position_per90_values) / len(
                            position_per90_values) if position_per90_values else 0

                        comparison_data.append({
                            'Metric': f'{metric} /90',
                            'Player': float(player_per90),
                            'Position Average': float(position_avg_per90),
                            'Difference': float(player_per90 - position_avg_per90)
                        })
                except Exception as e:
                    # Skip metric if conversion fails
                    continue

        if comparison_data:
            # Display comparison
            for data in comparison_data:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        data['Metric'],
                        f"{data['Player']:.2f}"
                    )

                with col2:
                    st.metric(
                        "Position Avg",
                        f"{data['Position Average']:.2f}"
                    )

                with col3:
                    diff = data['Difference']
                    delta_color = "normal"
                    if diff > 0:
                        delta_text = f"+{diff:.2f}"
                        delta_color = "normal"
                    else:
                        delta_text = f"{diff:.2f}"
                        delta_color = "inverse"

                    st.metric(
                        "Difference",
                        delta_text,
                        delta=delta_text,
                        delta_color=delta_color
                    )
        else:
            st.info("No comparable metrics found for position analysis.")

    # Section divider
    st.markdown("---")

    # Performance over time section
    st.markdown("## 📊 Season Performance")

    show_performance_trends(player_data)


def show_performance_trends(player_data: pd.Series):
    """Show performance trends if data is available"""

    # Show key season metrics
    col1, col2, col3 = st.columns(3)

    minutes = int(player_data.get('Minutos jogados', 0))
    matches = int(player_data.get('Partidas jogadas', 0))

    with col1:
        if matches > 0:
            consistency = min(100, (minutes / (matches * 90)) * 100)
            st.metric("Playing Time %", f"{consistency:.1f}%")
        else:
            st.metric("Playing Time %", "0.0%")

    with col2:
        goals = int(player_data.get('Gols', 0))
        if minutes > 0:
            goals_per_90 = (goals * 90) / minutes
            st.metric("Goals per 90min", f"{goals_per_90:.2f}")
        else:
            st.metric("Goals per 90min", "0.00")

    with col3:
        assists = int(player_data.get('Assistências', 0))
        if minutes > 0:
            assists_per_90 = (assists * 90) / minutes
            st.metric("Assists per 90min", f"{assists_per_90:.2f}")
        else:
            st.metric("Assists per 90min", "0.00")


def show_customizable_radar_chart_fixed(player_data: pd.Series, position: str):
    """Show customizable radar chart for player analysis - FIXED VERSION"""

    st.subheader("🎯 Customizable Radar Chart Analysis")

    # Get available numeric metrics
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                    'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados']

    available_metrics = []
    for col in player_data.index:
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(type(player_data[col])):
            if not col.endswith('_percentile') and col != 'Overall_Score':
                available_metrics.append(col)

    available_metrics = sorted(available_metrics)

    if not available_metrics:
        st.warning("No metrics available for radar chart.")
        return

    # Create unique keys for the radar chart components using player name and position
    player_name = player_data.get('Jogador', 'unknown')
    unique_key = f"radar_{position}_{player_name}".replace(" ", "_").replace(".", "_")

    # Initialize radar chart state if not exists
    radar_state_key = f"{unique_key}_radar_state"
    if radar_state_key not in st.session_state:
        st.session_state[radar_state_key] = {
            'num_metrics': min(6, len(available_metrics)),
            'selected_metrics': available_metrics[:min(6, len(available_metrics))],
            'compare_players': []
        }

    radar_state = st.session_state[radar_state_key]

    # Metric selection
    st.markdown("### 🔧 Select Variables for Radar Chart")

    # Number of metrics selector
    max_metrics = min(8, len(available_metrics))

    # Use session state for persistence
    num_metrics = st.slider(
        "Number of variables:",
        min_value=3,
        max_value=max_metrics,
        value=radar_state['num_metrics'],
        key=f"{unique_key}_num_metrics_slider"
    )

    # Update session state if changed
    if num_metrics != radar_state['num_metrics']:
        radar_state['num_metrics'] = num_metrics
        # Adjust selected metrics if needed
        if len(radar_state['selected_metrics']) < num_metrics:
            # Add more metrics
            current_metrics = set(radar_state['selected_metrics'])
            for metric in available_metrics:
                if metric not in current_metrics and len(radar_state['selected_metrics']) < num_metrics:
                    radar_state['selected_metrics'].append(metric)
        elif len(radar_state['selected_metrics']) > num_metrics:
            # Remove excess metrics
            radar_state['selected_metrics'] = radar_state['selected_metrics'][:num_metrics]

    # Metric selection
    selected_metrics = []
    cols = st.columns(2)

    for i in range(num_metrics):
        col_idx = i % 2
        with cols[col_idx]:
            # Get current metric or default
            current_metric = (radar_state['selected_metrics'][i]
                              if i < len(radar_state['selected_metrics'])
                              else available_metrics[min(i, len(available_metrics) - 1)])

            # Find index of current metric
            try:
                current_index = available_metrics.index(current_metric)
            except ValueError:
                current_index = min(i, len(available_metrics) - 1)

            metric = st.selectbox(
                f"Variable {i + 1}",
                available_metrics,
                index=current_index,
                key=f"{unique_key}_metric_select_{i}"
            )
            selected_metrics.append(metric)

    # Update session state
    radar_state['selected_metrics'] = selected_metrics

    # Player comparison option
    st.markdown("### 👥 Compare with Other Players")

    # Get all players from same position across all teams
    position_df = st.session_state.data_processor.dataframes[position]
    all_players = position_df['Jogador'].tolist()

    # Remove current player from options
    other_players = [p for p in all_players if p != player_data.get('Jogador')]

    compare_players = st.multiselect(
        "Select players to compare with (optional):",
        other_players,
        default=radar_state['compare_players'],
        max_selections=4,
        key=f"{unique_key}_compare_players_select"
    )

    # Update session state
    radar_state['compare_players'] = compare_players

    # Generate button
    generate_button_key = f"{unique_key}_generate_radar"
    if st.button("Generate Radar Chart", key=generate_button_key):
        if len(set(selected_metrics)) >= 3:
            # Prevent navigation by using a container
            with st.container():
                create_customizable_radar_chart_fixed(
                    player_data, position, selected_metrics, compare_players, unique_key
                )
        else:
            st.error("Please select at least 3 different variables")


def create_customizable_radar_chart_fixed(player_data: pd.Series, position: str,
                                          selected_metrics: List[str], compare_players: List[str], unique_key: str):
    """Create the actual customizable radar chart - FIXED VERSION"""

    # Get position dataframe for percentile calculations
    position_df = st.session_state.data_processor.dataframes[position]

    # Prepare players data for radar
    players_data = []

    # Add main player
    main_player_data = {'Player': player_data.get('Jogador', 'Main Player')}
    for metric in selected_metrics:
        if metric in player_data.index:
            # Calculate percentile for this metric
            values = pd.to_numeric(position_df[metric], errors='coerce').fillna(0)
            percentile = (values.rank(pct=True) * 100).fillna(0)

            # Find player's percentile
            player_row_idx = position_df[position_df['Jogador'] == player_data.get('Jogador')].index
            if len(player_row_idx) > 0:
                player_percentile = percentile.iloc[player_row_idx[0]]
            else:
                player_percentile = 50  # Default to median

            main_player_data[f'{metric}_percentile'] = player_percentile

    players_data.append(main_player_data)

    # Add comparison players
    for comp_player_name in compare_players:
        comp_player_row = position_df[position_df['Jogador'] == comp_player_name]
        if not comp_player_row.empty:
            comp_player_data = {'Player': comp_player_name}
            for metric in selected_metrics:
                if metric in position_df.columns:
                    values = pd.to_numeric(position_df[metric], errors='coerce').fillna(0)
                    percentile = (values.rank(pct=True) * 100).fillna(0)

                    comp_player_percentile = percentile.iloc[comp_player_row.index[0]]
                    comp_player_data[f'{metric}_percentile'] = comp_player_percentile

            players_data.append(comp_player_data)

    # Create radar chart - use container to prevent navigation issues
    chart_container = st.container()

    with chart_container:
        try:
            from components.charts import ScoutingCharts
            ScoutingCharts.show_radar_comparison(
                players_data,
                selected_metrics,
                position,
                f"Custom Radar Chart - {player_data.get('Jogador', 'Player')}"
            )
        except ImportError:
            # Fallback radar chart if components.charts is not available
            create_simple_radar_chart_fixed(players_data, selected_metrics, position, unique_key)

        # Show explanation
        with st.expander("📖 Chart Explanation"):
            st.markdown(f"""
            **CustomDefensive Duels Won %", f"{def_win_pct:.1f}%""")
    with col2:
        aerial_duels = player_data.get('Disputas aéreas', 0)
        aerial_won = player_data.get('Disputas aéreas ganhas', aerial_duels)
        aerial_pct = (aerial_won / aerial_duels * 100) if aerial_duels > 0 else 0
        st.metric("Aerial Duels Won %", f"{aerial_pct:.1f}%")
    with col3:
        tackles = player_data.get('Desarmes', 0)
        tackles_successful = player_data.get('Desarmes bem-sucedidos', tackles)
        tackle_success_pct = (tackles_successful / tackles * 100) if tackles > 0 else 0
        st.metric("Tackle Success %", f"{tackle_success_pct:.1f}%")
    with col4:
        st.metric("Interceptions",
                  player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe', 0))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ball Recoveries", player_data.get('Bolas recuperadas', 0))

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        off_duels = player_data.get('Disputas no ataque', 0)
        off_duels_won = player_data.get('Disputas no ataque ganhas', 0)
        off_win_pct = (off_duels_won / off_duels * 100) if off_duels > 0 else 0
        st.metric("Offensive Duels Won %", f"{off_win_pct:.1f}%")
    with col2:
        st.metric("Headed Goals", player_data.get('Gols de cabeça', 0))
    with col3:
        shots = player_data.get('Chutes', 0)
        shots_on_target = player_data.get('Chutes no gol', 0)
        shots_pct = (shots_on_target / shots * 100) if shots > 0 else 0
        st.metric("Shots on Target %", f"{shots_pct:.1f}%")
    with col4:
        total_goals = player_data.get('Gols', 0)
        total_shots = player_data.get('Chutes', 0)
        goals_per_shot_pct = (total_goals / total_shots * 100) if total_shots > 0 else 0
        st.metric("Goals per Shot %", f"{goals_per_shot_pct:.1f}%")
    with col5:
        chances = player_data.get('Chances criadas', 0)
        chances_successful = player_data.get('Chances bem-sucedidas', chances)
        chances_pct = (chances_successful / chances * 100) if chances > 0 else 0
        st.metric("Chances Success %", f"{chances_pct:.1f}%")

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        long_passes = player_data.get('Passes longos', 0)
        long_passes_accurate = player_data.get('Passes longos precisos', long_passes)
        long_pass_pct = (long_passes_accurate / long_passes * 100) if long_passes > 0 else 0
        st.metric("Long Pass Accuracy %", f"{long_pass_pct:.1f}%")
    with col3:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col2:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col3:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col4:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col5:
        aerial_per90 = (player_data.get('Disputas aéreas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Aerial Duels /90", f"{aerial_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xG", player_data.get('xG', 0))
    with col2:
        st.metric("xA", player_data.get('xA', 0))
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        st.metric("Ball Losses in Own Half", player_data.get('Bolas perdidas no próprio campo', 0))
    with col5:
        st.metric("Individual Losses", player_data.get('Perdas individuais', 0))


def show_fullback_stats(player_data: pd.Series, minutes: int):
    """Show full-back specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        crosses = player_data.get('Cruzamentos', 0)
        crosses_accurate = player_data.get('Cruzamentos precisos', 0)
        cross_accuracy = (crosses_accurate / crosses * 100) if crosses > 0 else 0
        st.metric("Cross Accuracy %", f"{cross_accuracy:.1f}%")
    with col2:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col3:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col4:
        dribbles = player_data.get('Dribles', 0)
        dribbles_successful = player_data.get('Dribles bem-sucedidos', 0)
        dribble_pct = (dribbles_successful / dribbles * 100) if dribbles > 0 else 0
        st.metric("Dribble Success %", f"{dribble_pct:.1f}%")
    with col5:
        shots = player_data.get('Chutes', 0)
        shots_on_target = player_data.get('Chutes no gol', 0)
        shots_pct = (shots_on_target / shots * 100) if shots > 0 else 0
        st.metric("Shots on Target %", f"{shots_pct:.1f}%")

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        aerial_duels = player_data.get('Disputas aéreas', 0)
        aerial_won = player_data.get('Disputas aéreas ganhas', aerial_duels)
        aerial_pct = (aerial_won / aerial_duels * 100) if aerial_duels > 0 else 0
        st.metric("Aerial Duels Won %", f"{aerial_pct:.1f}%")
    with col3:
        tackles = player_data.get('Desarmes', 0)
        tackles_successful = player_data.get('Desarmes bem-sucedidos', tackles)
        tackle_success_pct = (tackles_successful / tackles * 100) if tackles > 0 else 0
        st.metric("Tackle Success %", f"{tackle_success_pct:.1f}%")
    with col4:
        st.metric("Ball Recoveries in Opposition Half", player_data.get('Bolas recuperadas no campo do adversário', 0))
    with col5:
        st.metric("Fouls Committed", player_data.get('Faltas cometidas', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col3:
        long_passes = player_data.get('Passes longos', 0)
        long_passes_accurate = player_data.get('Passes longos precisos', long_passes)
        long_pass_pct = (long_passes_accurate / long_passes * 100) if long_passes > 0 else 0
        st.metric("Long Pass Accuracy %", f"{long_pass_pct:.1f}%")
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        crosses_per90 = (player_data.get('Cruzamentos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Crosses /90", f"{crosses_per90:.2f}")
    with col2:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xA", player_data.get('xA', 0))
    with col2:
        st.metric("xG", player_data.get('xG', 0))
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        final_third_dribbles = player_data.get('Dribles no último terço do campo com sucesso', 0)
        total_final_third_dribbles = player_data.get('Dribles no último terço do campo', final_third_dribbles)
        final_third_dribble_pct = (
                    final_third_dribbles / total_final_third_dribbles * 100) if total_final_third_dribbles > 0 else 0
        st.metric("Final Third Dribbles Success %", f"{final_third_dribble_pct:.1f}%")
    with col5:
        st.metric("Ball Losses in Own Half", player_data.get('Bolas perdidas após passes no próprio campo', 0))


def show_defensive_midfielder_stats(player_data: pd.Series, minutes: int):
    """Show defensive midfielder specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col2:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        st.metric("Assists", player_data.get('Assistências', 0))

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        aerial_duels = player_data.get('Disputas aéreas', 0)
        aerial_won = player_data.get('Disputas aéreas ganhas', aerial_duels)
        aerial_pct = (aerial_won / aerial_duels * 100) if aerial_duels > 0 else 0
        st.metric("Aerial Duels Won %", f"{aerial_pct:.1f}%")

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col3:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col4:
        long_passes = player_data.get('Passes longos', 0)
        long_passes_accurate = player_data.get('Passes longos precisos', long_passes)
        long_pass_pct = (long_passes_accurate / long_passes * 100) if long_passes > 0 else 0
        st.metric("Long Pass Accuracy %", f"{long_pass_pct:.1f}%")
    with col5:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col2:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col3:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col4:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col5:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xA", player_data.get('xA', 0))
    with col2:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col3:
        st.metric("Passes into Box", player_data.get('Passes para a área', 0))
    with col4:
        st.metric("Ball Losses in Own Half", player_data.get('Bolas perdidas após passes no próprio campo', 0))
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def show_central_midfielder_stats(player_data: pd.Series, minutes: int):
    """Show central midfielder specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col2:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        st.metric("Assists", player_data.get('Assistências', 0))

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        aerial_duels = player_data.get('Disputas aéreas', 0)
        aerial_won = player_data.get('Disputas aéreas ganhas', aerial_duels)
        aerial_pct = (aerial_won / aerial_duels * 100) if aerial_duels > 0 else 0
        st.metric("Aerial Duels Won %", f"{aerial_pct:.1f}%")

    # PASSING (same as MCD)
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col3:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col4:
        long_passes = player_data.get('Passes longos', 0)
        long_passes_accurate = player_data.get('Passes longos precisos', long_passes)
        long_pass_pct = (long_passes_accurate / long_passes * 100) if long_passes > 0 else 0
        st.metric("Long Pass Accuracy %", f"{long_pass_pct:.1f}%")
    with col5:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")

    # PER 90 MINUTES (same as MCD)
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col2:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col3:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col4:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col5:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")

    # ADVANCED (same as MCD)
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xA", player_data.get('xA', 0))
    with col2:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col3:
        st.metric("Passes into Box", player_data.get('Passes para a área', 0))
    with col4:
        st.metric("Ball Losses in Own Half", player_data.get('Bolas perdidas após passes no próprio campo', 0))
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def show_winger_stats(player_data: pd.Series, minutes: int):
    """Show winger specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        dribbles = player_data.get('Dribles', 0)
        dribbles_successful = player_data.get('Dribles bem-sucedidos', 0)
        dribble_pct = (dribbles_successful / dribbles * 100) if dribbles > 0 else 0
        st.metric("Dribble Success %", f"{dribble_pct:.1f}%")
    with col2:
        crosses_per90 = (player_data.get('Cruzamentos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Crosses /90", f"{crosses_per90:.2f}")
    with col3:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col4:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col5:
        shots = player_data.get('Chutes', 0)
        shots_on_target = player_data.get('Chutes no gol', 0)
        shots_pct = (shots_on_target / shots * 100) if shots > 0 else 0
        st.metric("Shots on Target %", f"{shots_pct:.1f}%")

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        st.metric("Fouls Committed", player_data.get('Faltas cometidas', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        pass_pct = player_data.get('Passes precisos %', 0)
        st.metric("Pass Accuracy %", f"{pass_pct}%")
    with col2:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col3:
        prog_passes = player_data.get('Passes progressivos', 0)
        prog_passes_accurate = player_data.get('Passes progressivos precisos', prog_passes)
        prog_pass_pct = (prog_passes_accurate / prog_passes * 100) if prog_passes > 0 else 0
        st.metric("Progressive Pass Accuracy %", f"{prog_pass_pct:.1f}%")
    with col4:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col5:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        final_third_dribbles_per90 = (player_data.get('Dribles no último terço do campo com sucesso',
                                                      0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Final Third Dribbles Success /90", f"{final_third_dribbles_per90:.2f}")
    with col2:
        crosses_per90 = (player_data.get('Cruzamentos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Crosses /90", f"{crosses_per90:.2f}")
    with col3:
        prog_passes_per90 = (player_data.get('Passes progressivos', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Progressive Passes /90", f"{prog_passes_per90:.2f}")
    with col4:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")
    with col5:
        shots_per90 = (player_data.get('Chutes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Shots /90", f"{shots_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xA", player_data.get('xA', 0))
    with col2:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col3:
        st.metric("Passes into Box", player_data.get('Passes para a área', 0))
    with col4:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def show_forward_stats(player_data: pd.Series, minutes: int):
    """Show forward specific statistics"""

    # OFFENSIVE
    st.markdown("## ⚽ OFFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        goals_per90 = (player_data.get('Gols', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Goals /90", f"{goals_per90:.2f}")
    with col2:
        st.metric("Headed Goals", player_data.get('Gols de cabeça', 0))
    with col3:
        shots = player_data.get('Chutes', 0)
        shots_on_target = player_data.get('Chutes no gol', 0)
        shots_pct = (shots_on_target / shots * 100) if shots > 0 else 0
        st.metric("Shots on Target %", f"{shots_pct:.1f}%")
    with col4:
        chances = player_data.get('Chances criadas', 0)
        chances_successful = player_data.get('Chances bem-sucedidas', chances)
        chances_pct = (chances_successful / chances * 100) if chances > 0 else 0
        st.metric("Chances Success %", f"{chances_pct:.1f}%")
    with col5:
        st.metric("xG", player_data.get('xG', 0))

    # DEFENSIVE
    st.markdown("## 🛡️ DEFENSIVE")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        def_duels = player_data.get('Disputas na defesa', 0)
        def_duels_won = player_data.get('Disputas na defesa ganhas', 0)
        def_win_pct = (def_duels_won / def_duels * 100) if def_duels > 0 else 0
        st.metric("Defensive Duels Won %", f"{def_win_pct:.1f}%")
    with col2:
        tackles_per90 = (player_data.get('Desarmes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Tackles /90", f"{tackles_per90:.2f}")
    with col3:
        inter_per90 = (player_data.get('Tentativas bem-sucedidas de interceptação de cruzamento e passe',
                                       0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Interceptions /90", f"{inter_per90:.2f}")
    with col4:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col5:
        st.metric("Fouls Committed", player_data.get('Faltas cometidas', 0))

    # PASSING
    st.markdown("## 🎯 PASSING")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        key_passes = player_data.get('Passes chave', 0)
        key_passes_accurate = player_data.get('Passes chave precisos', key_passes)
        key_pass_pct = (key_passes_accurate / key_passes * 100) if key_passes > 0 else 0
        st.metric("Key Pass Accuracy %", f"{key_pass_pct:.1f}%")
    with col2:
        area_passes = player_data.get('Passes para a área', 0)
        area_passes_accurate = player_data.get('Passes para a área precisos', area_passes)
        area_pass_pct = (area_passes_accurate / area_passes * 100) if area_passes > 0 else 0
        st.metric("Passes into Box Accuracy %", f"{area_pass_pct:.1f}%")
    with col3:
        st.metric("Passes to Final Third", player_data.get('Passes para o terço final', 0))
    with col4:
        st.metric("Assists", player_data.get('Assistências', 0))
    with col5:
        final_third_passes = player_data.get('Passes para o terço final', 0)
        final_third_accurate = player_data.get('Passes para frente até o terço final precisos', final_third_passes)
        final_third_pct = (final_third_accurate / final_third_passes * 100) if final_third_passes > 0 else 0
        st.metric("Forward to Final Third Pass Accuracy %", f"{final_third_pct:.1f}%")

    # PER 90 MINUTES
    st.markdown("## ⏱️ PER 90 MINUTES")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        goals_per90 = (player_data.get('Gols', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Goals /90", f"{goals_per90:.2f}")
    with col2:
        shots_per90 = (player_data.get('Chutes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Shots /90", f"{shots_per90:.2f}")
    with col3:
        recoveries_per90 = (player_data.get('Bolas recuperadas', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Ball Recoveries /90", f"{recoveries_per90:.2f}")
    with col4:
        passes_per90 = (player_data.get('Passes', 0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Passes /90", f"{passes_per90:.2f}")
    with col5:
        final_third_dribbles_per90 = (player_data.get('Dribles no último terço do campo com sucesso',
                                                      0) * 90 / minutes) if minutes > 0 else 0
        st.metric("Final Third Dribbles Success /90", f"{final_third_dribbles_per90:.2f}")

    # ADVANCED
    st.markdown("## 📊 ADVANCED")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("xG", player_data.get('xG', 0))
    with col2:
        st.metric("xA", player_data.get('xA', 0))
    with col3:
        st.metric("Key Passes", player_data.get('Passes chave', 0))
    with col4:
        st.metric("Chances Created", player_data.get('Chances criadas', 0))
    with col5:
        st.metric("Poor Ball Control", player_data.get('Controle de bola ruim', 0))


def get_key_performance_metrics_for_position(position: str) -> List[str]:
    """Get 5 key performance metrics for comparison by position (UPDATED VERSION)"""

    metrics = {
        'GR': [
            'Defesas',  # for Defesas /90
            'Defesas difíceis',  # for Defesas difíceis /90
            'Gols sofridos',  # for Gols sofridos /90
            'Passes precisos',  # for Passes precisos /90
            'Passes chave'  # for Passes chave /90
        ],
        'DCE': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Rebotes',  # for Rebotes /90
            'Dribles',  # for Dribles /90
            'Passes progressivos'  # for Passes progressivos /90
        ],
        'DCD': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Rebotes',  # for Rebotes /90
            'Dribles',  # for Dribles /90
            'Passes progressivos'  # for Passes progressivos /90
        ],
        'DE': [
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Desarmes'  # for Desarmes /90
        ],
        'DD': [
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Desarmes'  # for Desarmes /90
        ],
        'MCD': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes'  # for Passes /90
        ],
        'MC': [
            'Desarmes',  # for Desarmes /90
            'Tentativas bem-sucedidas de interceptação de cruzamento e passe',  # for Interceptações /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes'  # for Passes /90
        ],
        'EE': [
            'Dribles no último terço do campo com sucesso',  # for Dribles no último terço /90
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes',  # for Passes /90
            'Chutes'  # for Chutes /90
        ],
        'ED': [
            'Dribles no último terço do campo com sucesso',  # for Dribles no último terço /90
            'Cruzamentos',  # for Cruzamentos /90
            'Passes progressivos',  # for Passes progressivos /90
            'Passes',  # for Passes /90
            'Chutes'  # for Chutes /90
        ],
        'PL': [
            'Gols',  # for Gols /90
            'Chutes',  # for Chutes /90
            'Bolas recuperadas',  # for Bolas recuperadas /90
            'Passes',  # for Passes /90
            'Dribles no último terço do campo com sucesso'  # for Dribles no último terço /90
        ]
    }

    return metrics.get(position, ['Passes', 'Passes precisos', 'Faltas', 'Ações / com sucesso'])


def show_performance_analysis_updated(player_data: pd.Series, position: str):
    """Show performance analysis with comparisons (UPDATED VERSION)"""

    # Main section header
    st.subheader("📈 Performance Analysis")
    st.markdown("---")

    # Position comparison section
    st.markdown("## 🔄 vs Position Average")

    # Get position averages for comparison
    team_players = st.session_state.data_processor.get_team_players(st.session_state.selected_team)

    if position in team_players:
        position_df = team_players[position]

        # Key metrics for comparison (5 metrics per position)
        key_metrics = get_key_performance_metrics_for_position(position)

        comparison_data = []

        for metric in key_metrics:
            if metric in player_data.index and metric in position_df.columns:
                player_value = player_data[metric]

                # Convert metric column to numeric, handling strings
                try:
                    position_series = pd.to_numeric(position_df[metric], errors='coerce')
                    position_avg = position_series.mean()

                    # Convert player value to numeric
                    player_value_numeric = pd.to_numeric(player_value, errors='coerce')

                    if pd.notna(player_value_numeric) and pd.notna(position_avg):
                        # Calculate per 90 values
                        minutes = player_data.get('Minutos jogados', 0)
                        player_per90 = (player_value_numeric * 90 / minutes) if minutes > 0 else 0

                        # Calculate average per 90 for position
                        position_minutes = pd.to_numeric(position_df['Minutos jogados'], errors='coerce')
                        position_per90_values = []
                        for idx, (val, mins) in enumerate(zip(position_series, position_minutes)):
                            if pd.notna(val) and pd.notna(mins) and mins > 0:
                                position_per90_values.append(val * 90 / mins)

                        position_avg_per90 = sum(position_per90_values) / len(
                            position_per90_values) if position_per90_values else 0

                        comparison_data.append({
                            'Metric': f'{metric} /90',
                            'Player': float(player_per90),
                            'Position Average': float(position_avg_per90),
                            'Difference': float(player_per90 - position_avg_per90)
                        })
                except Exception as e:
                    # Skip metric if conversion fails
                    continue

        if comparison_data:
            # Display comparison
            for data in comparison_data:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        data['Metric'],
                        f"{data['Player']:.2f}"
                    )

                with col2:
                    st.metric(
                        "Position Avg",
                        f"{data['Position Average']:.2f}"
                    )

                with col3:
                    diff = data['Difference']
                    delta_color = "normal"
                    if diff > 0:
                        delta_text = f"+{diff:.2f}"
                        delta_color = "normal"
                    else:
                        delta_text = f"{diff:.2f}"
                        delta_color = "inverse"

                    st.metric(
                        "Difference",
                        delta_text,
                        delta=delta_text,
                        delta_color=delta_color
                    )
        else:
            st.info("No comparable metrics found for position analysis.")

    # Section divider
    st.markdown("---")

    # Performance over time section
    st.markdown("## 📊 Season Performance")

    show_performance_trends(player_data)


def show_performance_trends(player_data: pd.Series):
    """Show performance trends if data is available"""

    # Show key season metrics
    col1, col2, col3 = st.columns(3)

    minutes = int(player_data.get('Minutos jogados', 0))
    matches = int(player_data.get('Partidas jogadas', 0))

    with col1:
        if matches > 0:
            consistency = min(100, (minutes / (matches * 90)) * 100)
            st.metric("Playing Time %", f"{consistency:.1f}%")
        else:
            st.metric("Playing Time %", "0.0%")

    with col2:
        goals = int(player_data.get('Gols', 0))
        if minutes > 0:
            goals_per_90 = (goals * 90) / minutes
            st.metric("Goals per 90min", f"{goals_per_90:.2f}")
        else:
            st.metric("Goals per 90min", "0.00")

    with col3:
        assists = int(player_data.get('Assistências', 0))
        if minutes > 0:
            assists_per_90 = (assists * 90) / minutes
            st.metric("Assists per 90min", f"{assists_per_90:.2f}")
        else:
            st.metric("Assists per 90min", "0.00")


def show_customizable_radar_chart_fixed(player_data: pd.Series, position: str):
    """Show customizable radar chart for player analysis - FIXED VERSION"""

    st.subheader("🎯 Customizable Radar Chart Analysis")

    # Get available numeric metrics
    exclude_cols = ['Jogador', 'Time', 'Nacionalidade', 'Pé', 'Altura', 'Valor de mercado',
                    'Data de nascimento', 'Contrato expira em', 'Posição', 'Temporada',
                    'Index', 'Position_File', 'Idade', 'Partidas jogadas', 'Minutos jogados']

    available_metrics = []
    for col in player_data.index:
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(type(player_data[col])):
            if not col.endswith('_percentile') and col != 'Overall_Score':
                available_metrics.append(col)

    available_metrics = sorted(available_metrics)

    if not available_metrics:
        st.warning("No metrics available for radar chart.")
        return

    # Create unique keys for the radar chart components using player name and position
    player_name = player_data.get('Jogador', 'unknown')
    unique_key = f"radar_{position}_{player_name}".replace(" ", "_").replace(".", "_")

    # Initialize radar chart state if not exists
    radar_state_key = f"{unique_key}_radar_state"
    if radar_state_key not in st.session_state:
        st.session_state[radar_state_key] = {
            'num_metrics': min(6, len(available_metrics)),
            'selected_metrics': available_metrics[:min(6, len(available_metrics))],
            'compare_players': []
        }

    radar_state = st.session_state[radar_state_key]

    # Metric selection
    st.markdown("### 🔧 Select Variables for Radar Chart")

    # Number of metrics selector
    max_metrics = min(8, len(available_metrics))

    # Use session state for persistence
    num_metrics = st.slider(
        "Number of variables:",
        min_value=3,
        max_value=max_metrics,
        value=radar_state['num_metrics'],
        key=f"{unique_key}_num_metrics_slider"
    )

    # Update session state if changed
    if num_metrics != radar_state['num_metrics']:
        radar_state['num_metrics'] = num_metrics
        # Adjust selected metrics if needed
        if len(radar_state['selected_metrics']) < num_metrics:
            # Add more metrics
            current_metrics = set(radar_state['selected_metrics'])
            for metric in available_metrics:
                if metric not in current_metrics and len(radar_state['selected_metrics']) < num_metrics:
                    radar_state['selected_metrics'].append(metric)
        elif len(radar_state['selected_metrics']) > num_metrics:
            # Remove excess metrics
            radar_state['selected_metrics'] = radar_state['selected_metrics'][:num_metrics]

    # Metric selection
    selected_metrics = []
    cols = st.columns(2)

    for i in range(num_metrics):
        col_idx = i % 2
        with cols[col_idx]:
            # Get current metric or default
            current_metric = (radar_state['selected_metrics'][i]
                              if i < len(radar_state['selected_metrics'])
                              else available_metrics[min(i, len(available_metrics) - 1)])

            # Find index of current metric
            try:
                current_index = available_metrics.index(current_metric)
            except ValueError:
                current_index = min(i, len(available_metrics) - 1)

            metric = st.selectbox(
                f"Variable {i + 1}",
                available_metrics,
                index=current_index,
                key=f"{unique_key}_metric_select_{i}"
            )
            selected_metrics.append(metric)

    # Update session state
    radar_state['selected_metrics'] = selected_metrics

    # Player comparison option
    st.markdown("### 👥 Compare with Other Players")

    # Get all players from same position across all teams
    position_df = st.session_state.data_processor.dataframes[position]
    all_players = position_df['Jogador'].tolist()

    # Remove current player from options
    other_players = [p for p in all_players if p != player_data.get('Jogador')]

    compare_players = st.multiselect(
        "Select players to compare with (optional):",
        other_players,
        default=radar_state['compare_players'],
        max_selections=4,
        key=f"{unique_key}_compare_players_select"
    )

    # Update session state
    radar_state['compare_players'] = compare_players

    # Generate button
    generate_button_key = f"{unique_key}_generate_radar"
    if st.button("Generate Radar Chart", key=generate_button_key):
        if len(set(selected_metrics)) >= 3:
            # Prevent navigation by using a container
            with st.container():
                create_customizable_radar_chart_fixed(
                    player_data, position, selected_metrics, compare_players, unique_key
                )
        else:
            st.error("Please select at least 3 different variables")


def create_customizable_radar_chart_fixed(player_data: pd.Series, position: str,
                                          selected_metrics: List[str], compare_players: List[str], unique_key: str):
    """Create the actual customizable radar chart - FIXED VERSION"""

    # Get position dataframe for percentile calculations
    position_df = st.session_state.data_processor.dataframes[position]

    # Prepare players data for radar
    players_data = []

    # Add main player
    main_player_data = {'Player': player_data.get('Jogador', 'Main Player')}
    for metric in selected_metrics:
       if metric in player_data.index:
           # Calculate percentile for this metric
           values = pd.to_numeric(position_df[metric], errors='coerce').fillna(0)
           percentile = (values.rank(pct=True) * 100).fillna(0)

           # Find player's percentile
           player_row_idx = position_df[position_df['Jogador'] == player_data.get('Jogador')].index
           if len(player_row_idx) > 0:
               player_percentile = percentile.iloc[player_row_idx[0]]
           else:
               player_percentile = 50  # Default to median

           main_player_data[f'{metric}_percentile'] = player_percentile
    players_data.append(main_player_data)

   # Add comparison players
    for comp_player_name in compare_players:
       comp_player_row = position_df[position_df['Jogador'] == comp_player_name]
       if not comp_player_row.empty:
           comp_player_data = {'Player': comp_player_name}
           for metric in selected_metrics:
               if metric in position_df.columns:
                   values = pd.to_numeric(position_df[metric], errors='coerce').fillna(0)
                   percentile = (values.rank(pct=True) * 100).fillna(0)

                   comp_player_percentile = percentile.iloc[comp_player_row.index[0]]
                   comp_player_data[f'{metric}_percentile'] = comp_player_percentile

           players_data.append(comp_player_data)

   # Create radar chart - use container to prevent navigation issues
    chart_container = st.container()

    with chart_container:
       try:
           from components.charts import ScoutingCharts
           ScoutingCharts.show_radar_comparison(
               players_data,
               selected_metrics,
               position,
               f"Custom Radar Chart - {player_data.get('Jogador', 'Player')}"
           )
       except ImportError:
           # Fallback radar chart if components.charts is not available
           create_simple_radar_chart_fixed(players_data, selected_metrics, position, unique_key)

       # Show explanation
       with st.expander("📖 Chart Explanation"):
           st.markdown(f"""
           **Custom Radar Chart Explanation:**

           - Each axis represents one of your selected variables
           - Values are shown as **percentiles** (0-100) compared to all {position} players in the dataset
           - **Higher values = better performance** for that variable
           - The colored area shows each player's overall profile across selected variables
           - **Larger area = better overall performance** in the selected metrics

           **Selected Variables:**
           """)

           for i, metric in enumerate(selected_metrics):
               original_value = player_data.get(metric, 0)
               st.markdown(f"• **{metric}**: {original_value:.2f}")


def create_simple_radar_chart_fixed(players_data: List[Dict], selected_metrics: List[str],
                                   position: str, unique_key: str):
   """Create a simple radar chart using plotly - FIXED VERSION"""

   import plotly.graph_objects as go

   fig = go.Figure()

   colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']

   for i, player_data in enumerate(players_data):
       player_name = player_data['Player']

       # Get percentile values
       values = []
       for metric in selected_metrics:
           percentile_key = f'{metric}_percentile'
           value = player_data.get(percentile_key, 50)
           values.append(value)

       # Close the radar chart by adding first value at the end
       values.append(values[0])
       metrics_display = selected_metrics + [selected_metrics[0]]

       fig.add_trace(go.Scatterpolar(
           r=values,
           theta=metrics_display,
           fill='toself',
           name=player_name,
           line=dict(color=colors[i % len(colors)]),
           fillcolor=colors[i % len(colors)].replace('#', 'rgba(').replace('FF6B6B', '255, 107, 107').replace('4ECDC4', '78, 205, 196').replace('45B7D1', '69, 183, 209').replace('96CEB4', '150, 206, 180').replace('FECA57', '254, 202, 87') + ', 0.3)',
           opacity=0.7
       ))

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
               gridcolor='rgba(128,128,128,0.2)'
           ),
           angularaxis=dict(
               tickfont=dict(size=10)
           )
       ),
       showlegend=True,
       title=dict(
           text=f"Custom Radar Chart - {position} Players Comparison",
           x=0.5,
           font=dict(size=16)
       ),
       height=500
   )

   # Use st.plotly_chart with unique key to prevent conflicts
   st.plotly_chart(fig, use_container_width=True, key=f"{unique_key}_plotly_chart")