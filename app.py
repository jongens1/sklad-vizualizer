import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Nastavenie stránky
st.set_page_config(layout="wide", page_title="Warehouse Map Pro")

st.title("📊 Warehouse Visualizer (Enhanced Scaling)")

# --- FUNKCIA NA NAČÍTANIE DÁT S CACHINGOM ---
@st.cache_data
def load_and_parse_data(file_source):
    """Načíta Excel a pripraví dáta."""
    df = pd.read_excel(file_source)
    
    def parse_location(loc_name):
        try:
            parts = str(loc_name).split('-')
            zone = parts[0]
            ulicka = int(parts[1])
            pozicia = int(parts[2])
            uroven = int(parts[3])
            return zone, ulicka, pozicia, uroven
        except:
            return None, None, None, None

    coords_data = df.apply(lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1)
    df[['tmp_zone', 'ul_num', 'poz_num', 'ur_num']] = coords_data
    df = df.dropna(subset=['tmp_zone', 'ul_num', 'poz_num', 'ur_num'])
    
    # Očistenie percent
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)
    return df

# --- LOGIKA ZDROJA DÁT ---
uploaded_file = st.sidebar.file_uploader("Nahraj vlastný Excel (.xlsx)", type=["xlsx"])

df_raw = None
if uploaded_file:
    df_raw = load_and_parse_data(uploaded_file)
elif os.path.exists("data.xlsx"):
    df_raw = load_and_parse_data("data.xlsx")

if df_raw is not None:
    # 1. SIDEBAR FILTRE
    st.sidebar.header("📍 Nastavenia")
    
    available_zones = sorted(df_raw['tmp_zone'].unique())
    selected_zone = st.sidebar.selectbox("Vyber Zónu:", available_zones)
    zone_df = df_raw[df_raw['tmp_zone'] == selected_zone].copy()

    view_type = st.sidebar.radio("Typ zobrazenia:", ["Pohľad na celú plochu (Pôdorys)", "Detail jednej uličky (Profil)"])
    viz_mode = st.sidebar.radio("Farba podľa:", ["Využitie kapacity (%)", "Počet rôznych produktov"])

    # 2. FILTROVANIE
    if view_type == "Pohľad na celú plochu (Pôdorys)":
        levels = sorted(zone_df['ur_num'].unique().astype(int))
        level_options = ["Všetky úrovne (Priemer)"] + [str(l) for l in levels]
        selected_level = st.sidebar.selectbox("Vyber poschodie:", level_options)
        
        if selected_level == "Všetky úrovne (Priemer)":
            plot_df = zone_df.groupby(['ul_num', 'poz_num']).agg({
                'util_num': 'mean', 
                'Počet produktov': 'mean', 
                'Množstvo produktov': 'sum'
            }).reset_index()
            # V režime priemeru vytvoríme popisný názov
            plot_df['display_name'] = plot_df.apply(lambda r: f"{selected_zone}-{int(r['ul_num']):02d}-{int(r['poz_num']):02d}", axis=1)
        else:
            plot_df = zone_df[zone_df['ur_num'] == int(selected_level)].copy()
            plot_df['display_name'] = plot_df['Názov lokácie']
        
        x_col, y_col = 'ul_num', 'poz_num'
        x_label, y_label = "Ulička", "Pozícia"
    else:
        available_aisles = sorted(zone_df['ul_num'].unique().astype(int))
        selected_aisle = st.sidebar.selectbox("Vyber uličku:", available_aisles)
        plot_df = zone_df[zone_df['ul_num'] == selected_aisle].copy()
        plot_df['display_name'] = plot_df['Názov lokácie']
        x_col, y_col = 'poz_num', 'ur_num'
        x_label, y_label = "Pozícia", "Úroveň"

    # --- AUTOMATICKÝ SCALING VEĽKOSTI BODU (Zväčšený) ---
    range_x = plot_df[x_col].max() - plot_df[x_col].min() if not plot_df.empty else 0
    range_y = plot_df[y_col].max() - plot_df[y_col].min() if not plot_df.empty else 0
    max_dim = max(range_x, range_y)

    if max_dim < 10: auto_size = 48
    elif max_dim < 25: auto_size = 32
    elif max_dim < 50: auto_size = 20
    else: auto_size = 14 # Pre zónu 2A (cca 75 uličiek) zvýšené z 10 na 14

    # 3. VYKRESLENIE
    fig = go.Figure()
    
    if viz_mode == "Využitie kapacity (%)":
        c_col, c_scale, c_min, c_max = 'util_num', 'RdYlGn_r', 0, 100
    else:
        c_col, c_scale, c_min, c_max = 'Počet produktov', 'Viridis_r', 0, plot_df['Počet produktov'].max() if not plot_df.empty else 10

    fig.add_trace(go.Scatter(
        x=plot_df[x_col], y=plot_df[y_col],
        mode='markers',
        marker=dict(
            size=auto_size,
            symbol='square',
            color=plot_df[c_col],
            colorscale=c_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            line=dict(width=0.4, color='black')
        ),
        text=plot_df['display_name'],
        # VYLEPŠENÝ HOVER
        customdata=plot_df[['ul_num', 'poz_num', 'util_num', 'Počet produktov', 'Množstvo produktov']],
        hovertemplate=(
            "<b>Lokácia: %{text}</b><br>" +
            "Ulička: %{customdata[0]}<br>" +
            "Pozícia: %{customdata[1]}<br><br>" +
            "Využitie: %{customdata[2]:.1f}%<br>" +
            "SKU: %{customdata[3]:.1f}<br>" +
            "Kusy: %{customdata[4]}<extra></extra>"
        )
    ))

    # Auto-Zoom
    if not plot_df.empty:
        fig.update_xaxes(range=[plot_df[x_col].min() - 1, plot_df[x_col].max() + 1])
        fig.update_yaxes(range=[plot_df[y_col].min() - 1, plot_df[y_col].max() + 1])

    fig.update_layout(
        title=f"Mapa: Zóna {selected_zone}",
        xaxis=dict(title=x_label, tickmode='linear', dtick=1 if range_x < 40 else 5, gridcolor='#f0f0f0'),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1, gridcolor='#f0f0f0'),
        height=750,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Detailná tabuľka s peknými názvami
    st.write("### Detailný prehľad")
    st.dataframe(plot_df.sort_values([x_col, y_col]), use_container_width=True)

else:
    st.info("👋 Prosím, nahraj Excel alebo pridaj 'data.xlsx' na GitHub.")
