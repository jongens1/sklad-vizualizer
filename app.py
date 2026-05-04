import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Nastavenie šírky stránky
st.set_page_config(layout="wide", page_title="Warehouse Map - Pro")

st.title("📊 Warehouse Visualizer")

# Sidebar pre nahranie súboru
st.sidebar.header("📁 Dáta")
uploaded_file = st.sidebar.file_uploader("Nahraj vlastný Excel súbor (.xlsx)", type=["xlsx"])

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

# LOGIKA NAČÍTANIA DÁT
df = None
if uploaded_file:
    df = pd.read_excel(uploaded_file)
elif os.path.exists("data.xlsx"):
    df = pd.read_excel("data.xlsx")

if df is not None:
    # 1. Spracovanie dát
    coords_data = df.apply(lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1)
    df[['tmp_zone', 'ul_num', 'poz_num', 'ur_num']] = coords_data
    df = df.dropna(subset=['tmp_zone', 'ul_num', 'poz_num', 'ur_num'])
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. SIDEBAR - FILTRE A SCALING
    st.sidebar.header("📍 Nastavenia")
    
    available_zones = sorted(df['tmp_zone'].unique())
    selected_zone = st.sidebar.selectbox("Vyber Zónu:", available_zones)
    zone_df = df[df['tmp_zone'] == selected_zone].copy()

    # --- NOVÝ VIZUÁLNY SCALING ---
    st.sidebar.subheader("Vizuálne prispôsobenie")
    point_size = st.sidebar.slider("Veľkosť štvorčekov:", 5, 40, 15)
    chart_height = st.sidebar.slider("Výška grafu:", 400, 1000, 650)

    view_type = st.sidebar.radio("Typ zobrazenia:", ["Pohľad na celú plochu (Pôdorys)", "Detail jednej uličky (Profil)"])
    viz_mode = st.sidebar.radio("Zobraziť farbu podľa:", ["Využitie kapacity (%)", "Počet rôznych produktov"])

    # 3. FILTROVANIE DÁT
    if view_type == "Pohľad na celú plochu (Pôdorys)":
        levels = sorted(zone_df['ur_num'].unique().astype(int))
        level_options = ["Všetky úrovne (Priemer)"] + [str(l) for l in levels]
        selected_level = st.sidebar.selectbox("Vyber poschodie:", level_options)
        
        if selected_level == "Všetky úrovne (Priemer)":
            plot_df = zone_df.groupby(['ul_num', 'poz_num']).agg({'util_num': 'mean', 'Počet produktov': 'mean', 'Množstvo produktov': 'sum'}).reset_index()
            plot_df['Názov lokácie'] = plot_df.apply(lambda r: f"Zóna {selected_zone}, Ul. {int(r['ul_num'])}, Poz. {int(r['poz_num'])}", axis=1)
            plot_df['ur_num'] = 0 
        else:
            plot_df = zone_df[zone_df['ur_num'] == int(selected_level)].copy()
        
        x_axis_col, y_axis_col = 'ul_num', 'poz_num'
        x_label, y_label = "Ulička (Rada)", "Pozícia v uličke"
    
    else: # Detail uličky
        available_aisles = sorted(zone_df['ul_num'].unique().astype(int))
        selected_aisle = st.sidebar.selectbox("Vyber uličku:", available_aisles)
        plot_df = zone_df[zone_df['ul_num'] == selected_aisle].copy()
        x_axis_col, y_axis_col = 'poz_num', 'ur_num'
        x_label, y_label = "Pozícia v uličke", "Poschodie (Úroveň)"

    # Farby
    if viz_mode == "Využitie kapacity (%)":
        color_col, color_scale, c_min, c_max, bar_title = 'util_num', 'RdYlGn_r', 0, 100, "% Využitia"
    else:
        max_sku = plot_df['Počet produktov'].max() if len(plot_df) > 0 else 10
        color_col, color_scale, c_min, c_max, bar_title = 'Počet produktov', 'Viridis_r', 0, max_sku, "Počet SKU"

    # 4. VYKRESLENIE S AUTOMATICKÝM ZOOMOM
    st.subheader(f"Zobrazenie: Zóna {selected_zone} | {view_type}")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df[x_axis_col],
        y=plot_df[y_axis_col],
        mode='markers',
        marker=dict(
            size=point_size, # Použitie hodnoty zo slidera
            symbol='square',
            color=plot_df[color_col],
            colorscale=color_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            colorbar=dict(title=bar_title),
            line=dict(width=0.5, color='DarkSlateGrey')
        ),
        text=plot_df['Názov lokácie'],
        hovertemplate="<b>%{text}</b><br>Využitie: %{customdata[0]:.1f}%<br>Produkty: %{customdata[1]:.1f}<extra></extra>",
        customdata=plot_df[['util_num', 'Počet produktov']]
    ))

    # Dynamické nastavenie rozsahu osí (aby tam nebolo biele miesto)
    if not plot_df.empty:
        margin_x = 1
        margin_y = 1
        fig.update_xaxes(range=[plot_df[x_axis_col].min() - margin_x, plot_df[x_axis_col].max() + margin_x])
        fig.update_yaxes(range=[plot_df[y_axis_col].min() - margin_y, plot_df[y_axis_col].max() + margin_y])

    fig.update_layout(
        xaxis=dict(title=x_label, tickmode='linear', dtick=1 if len(plot_df[x_axis_col].unique()) < 40 else 5),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1),
        width=None, # Necháme nech sa prispôsobí šírke kontajnera
        height=chart_height, # Použitie hodnoty zo slidera
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5. TABUĽKA
    st.write("### Detailný zoznam lokácií")
    st.dataframe(plot_df.sort_values(['ul_num', 'poz_num'])[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', 'util_num']], use_container_width=True)

else:
    st.info("👋 Prosím, nahraj Excel súbor.")
