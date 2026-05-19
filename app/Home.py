"""
MacroDash NBB : page d'accueil Streamlit.
Lancer avec : streamlit run app/Home.py
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import BCE_EVENTS, DATASETS
from src.fetch_eurostat import EurostatClient
from src.transform import build_macro_df

st.set_page_config(
    page_title="MacroDash NBB",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏦 MacroDash : indicateurs macroéconomiques belges")
st.caption("Source : Eurostat | Auteur : Tahar Guenfoud | 2026")


@st.cache_data(ttl=86_400)
def load_data() -> pd.DataFrame:
    client = EurostatClient()
    cached = EurostatClient.load_cached()
    if len(cached) == len(DATASETS):
        series = cached
    else:
        series = client.fetch_all(start="2010", cache=True)
    return build_macro_df(series)


with st.spinner("Chargement des données Eurostat..."):
    macro = load_data()

if macro.empty:
    st.error("Impossible de charger les données. Vérifie ta connexion réseau.")
    st.stop()


# Filtres dans la sidebar
st.sidebar.header("Filtres")
available_keys = [k for k in DATASETS if k in macro.columns]
selected = st.sidebar.multiselect(
    "Séries à afficher",
    options=available_keys,
    default=[k for k in ("olo_10y", "inflation", "chomage", "prix_immo") if k in available_keys],
    format_func=lambda k: DATASETS[k]["label"],
)

year_min = int(macro.index.year.min())
year_max = int(macro.index.year.max())
year_range = st.sidebar.slider("Période", year_min, year_max, (2019, year_max))
df_view = macro[str(year_range[0]):str(year_range[1])]

show_events = st.sidebar.checkbox("Afficher événements BCE", value=True)


# KPIs : dernière valeur disponible pour chaque série principale
kpi_keys = [k for k in ("olo_10y", "euribor_3m", "inflation", "chomage") if k in macro.columns]
cols = st.columns(len(kpi_keys))
for col, key in zip(cols, kpi_keys):
    s = macro[key].dropna()
    if s.empty:
        continue
    last_val = s.iloc[-1]
    prev_val = s.iloc[-2] if len(s) > 1 else last_val
    delta = last_val - prev_val
    col.metric(
        label=DATASETS[key]["label"],
        value=f"{last_val:.2f} {DATASETS[key]['unit']}",
        delta=f"{delta:+.2f}",
    )

st.divider()

if not selected:
    st.info("Sélectionne au moins une série dans le panneau de gauche.")
    st.stop()


# Graphique principal : une courbe par série sélectionnée
fig = make_subplots(
    rows=len(selected),
    cols=1,
    shared_xaxes=True,
    subplot_titles=[DATASETS[k]["label"] for k in selected],
    vertical_spacing=0.06,
)

for i, key in enumerate(selected, start=1):
    cfg = DATASETS[key]
    s = df_view[key].dropna()
    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=s.values,
            mode="lines",
            name=cfg["label"],
            line=dict(color=cfg["color"], width=2),
            hovertemplate="%{x|%Y-%m}: %{y:.2f} " + cfg["unit"] + "<extra></extra>",
        ),
        row=i,
        col=1,
    )

if show_events:
    # Les annotations sur le premier subplot seulement, pour éviter l'empilement
    for date_str, label, color in BCE_EVENTS:
        x_ms = pd.Timestamp(date_str).value // 10**6
        fig.add_vline(
            x=x_ms,
            row=1,
            line_dash="dot",
            line_color=color,
            opacity=0.5,
            annotation_text=label,
            annotation_position="top right",
            annotation_font_size=9,
            annotation_font_color=color,
        )
        # Lignes sans annotation sur les autres subplots
        for row_idx in range(2, len(selected) + 1):
            fig.add_vline(
                x=x_ms,
                row=row_idx,
                line_dash="dot",
                line_color=color,
                opacity=0.3,
            )

# Zone COVID en grisé
fig.add_vrect(
    x0="2020-03",
    x1="2021-06",
    fillcolor="gray",
    opacity=0.07,
    layer="below",
    line_width=0,
    annotation_text="COVID",
    annotation_position="top left",
    annotation_font_size=9,
)

fig.update_layout(
    height=260 * len(selected),
    showlegend=False,
    template="plotly_white",
    margin=dict(t=40, b=20),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)


# Matrice de corrélation en section repliable
with st.expander("Matrice de corrélation", expanded=False):
    corr_keys = [k for k in DATASETS if k in macro.columns]
    corr = macro[corr_keys].corr(method="pearson").round(3)
    labels_display = [DATASETS[k]["label"] for k in corr.columns]

    fig_corr = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels_display,
        y=labels_display,
        colorscale="RdYlGn",
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont_size=11,
        hovertemplate="%{y} x %{x} : %{z:.3f}<extra></extra>",
    ))
    fig_corr.update_layout(
        template="plotly_white",
        height=400,
        xaxis=dict(tickangle=-30),
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig_corr, use_container_width=True)
