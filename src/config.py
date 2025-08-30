#Page configuration
PAGE_CONFIG = {
    "page_title": "Football Analytics",
    "page_icon": "⚽",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

#Position order for display
POSITIONS_ORDER = ["GR", "DCE", "DCD", "DE", "DD", "EE", "ED", "MCD", "MC", "PL"]

#Position groups
POSITION_GROUPS = {
    "Goalkeepers": ["GR"],
    "Defenders": ["DCE", "DCD", "DE", "DD"],
    "Midfielders": ["EE", "ED", "MCD", "MC"],
    "Forwards": ["PL"]
}

#Metrics to calculate per 90 minutes
METRICS_PER_90 = [
    "Gols", "Assistências", "Chutes", "Desarmes", "Interceptações",
    "Passes", "Passes progressivos", "Dribles", "Disputas na defesa",
    "Disputas no ataque", "Bolas recuperadas", "Faltas", "Cruzamentos"
]