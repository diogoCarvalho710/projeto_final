import streamlit as st
import os
from pathlib import Path


def ensure_data_directories():
    """Ensure data directories exist"""
    directories = [
        "data",
        "data/temp",
        "data/configs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def get_data_size():
    """Get size of saved data"""
    data_dir = Path("data/temp")
    if not data_dir.exists():
        return "No data"

    total_size = sum(f.stat().st_size for f in data_dir.glob('*') if f.is_file())

    if total_size < 1024:
        return f"{total_size} bytes"
    elif total_size < 1024 * 1024:
        return f"{total_size / 1024:.1f} KB"
    else:
        return f"{total_size / (1024 * 1024):.1f} MB"


@st.cache_data
def load_cached_data():
    """Cache data loading for better performance"""
    pass