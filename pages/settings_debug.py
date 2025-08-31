import streamlit as st
import pandas as pd
from typing import Dict, List


def show_settings():
    """Display simplified settings page for debugging"""

    st.title("⚙️ Settings & Personalization - DEBUG MODE")
    st.warning("🔧 Esta é a versão debug. Se vês isto, os imports básicos funcionam!")

    if not st.session_state.get('data_processor') or not st.session_state.get('selected_team'):
        st.warning("Please upload data and select a team first!")
        return

    # Test basic functionality first
    st.success("✅ Streamlit imports working")
    st.success("✅ Session state accessible")
    st.success(f"✅ Selected team: {st.session_state.selected_team}")

    # Test manager imports one by one
    st.markdown("---")
    st.subheader("🧪 Testing Manager Imports")

    # Test 1: Custom Metrics Manager
    try:
        from src.custom_metrics_manager import CustomMetricsManager
        st.success("✅ CustomMetricsManager import successful")

        # Try to initialize it
        try:
            custom_metrics_manager = CustomMetricsManager(st.session_state.data_processor)
            st.success("✅ CustomMetricsManager initialization successful")
        except Exception as e:
            st.error(f"❌ CustomMetricsManager init error: {str(e)}")

    except ImportError as e:
        st.error(f"❌ CustomMetricsManager import error: {str(e)}")
    except SyntaxError as e:
        st.error(f"💥 CustomMetricsManager syntax error: {str(e)}")
        st.code(f"Line {e.lineno}: {e.text if e.text else 'Unknown'}")
    except Exception as e:
        st.error(f"⚠️ CustomMetricsManager other error: {str(e)}")

    # Test 2: Favorites Manager
    try:
        from src.favorites_manager import FavoritesManager
        st.success("✅ FavoritesManager import successful")

        try:
            favorites_manager = FavoritesManager(st.session_state.data_processor)
            st.success("✅ FavoritesManager initialization successful")
        except Exception as e:
            st.error(f"❌ FavoritesManager init error: {str(e)}")

    except ImportError as e:
        st.error(f"❌ FavoritesManager import error: {str(e)}")
    except SyntaxError as e:
        st.error(f"💥 FavoritesManager syntax error: {str(e)}")
        st.code(f"Line {e.lineno}: {e.text if e.text else 'Unknown'}")
    except Exception as e:
        st.error(f"⚠️ FavoritesManager other error: {str(e)}")

    # Test 3: Custom Rankings Manager
    try:
        from src.custom_rankings_manager import CustomRankingsManager
        st.success("✅ CustomRankingsManager import successful")

        try:
            custom_rankings_manager = CustomRankingsManager(
                st.session_state.data_processor,
                st.session_state.ranking_system
            )
            st.success("✅ CustomRankingsManager initialization successful")
        except Exception as e:
            st.error(f"❌ CustomRankingsManager init error: {str(e)}")

    except ImportError as e:
        st.error(f"❌ CustomRankingsManager import error: {str(e)}")
    except SyntaxError as e:
        st.error(f"💥 CustomRankingsManager syntax error: {str(e)}")
        st.code(f"Line {e.lineno}: {e.text if e.text else 'Unknown'}")
    except Exception as e:
        st.error(f"⚠️ CustomRankingsManager other error: {str(e)}")

    # If all tests pass, show success message
    st.markdown("---")
    st.subheader("🎯 Next Steps")

    if st.button("🚀 Try Full Settings Page"):
        st.info("Se todos os testes acima passaram ✅, podes substituir settings_debug.py por settings.py")

    # Show some basic info
    st.markdown("---")
    st.subheader("📊 System Info")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_players = sum(len(df) for df in
                            st.session_state.data_processor.dataframes.values()) if st.session_state.data_processor else 0
        st.metric("Total Players", total_players)

    with col2:
        positions = len(st.session_state.data_processor.dataframes) if st.session_state.data_processor else 0
        st.metric("Positions Loaded", positions)

    with col3:
        st.metric("Current Page", "Settings Debug")

    # Basic Phase 5 preview
    st.markdown("---")
    st.subheader("🔮 Phase 5 Preview")

    preview_tabs = st.tabs(["Custom Metrics", "Favorite Players", "Custom Rankings"])

    with preview_tabs[0]:
        st.info("🎨 Custom Metrics: Create personalized performance indicators")
        st.markdown("- Combine existing stats with custom weights")
        st.markdown("- Templates for quick setup")
        st.markdown("- Test metrics with live data")

    with preview_tabs[1]:
        st.info("⭐ Favorite Players: Advanced player tracking")
        st.markdown("- Collections, tags, and priorities")
        st.markdown("- Status tracking (scouting → signed)")
        st.markdown("- Player suggestions based on favorites")

    with preview_tabs[2]:
        st.info("🏆 Custom Rankings: Sophisticated ranking systems")
        st.markdown("- Multi-criteria scoring")
        st.markdown("- Age weighting and market value")
        st.markdown("- Template-based quick setup")

    # Debug information
    with st.expander("🔍 Debug Information"):
        st.json({
            "data_processor_loaded": st.session_state.get('data_processor') is not None,
            "ranking_system_loaded": st.session_state.get('ranking_system') is not None,
            "selected_team": st.session_state.get('selected_team'),
            "session_keys": list(st.session_state.keys())[:10]  # First 10 keys
        })