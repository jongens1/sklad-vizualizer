import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Nastavenie stránky
st.set_page_config(layout="wide", page_title="Warehouse Map Pro")

st.title("📊 Warehouse Visualizer (Zone & Section Filter)")

# --- FUNKCIA NA NAČÍTANIE DÁT S CACHINGOM ---
@st.cache_data
def load_and_parse_data(file_source):
    """Načíta Excel a pripraví dáta."""
    df = pd.read_excel(file_source)
    
    # Ošetrenie prázdnych hodnôt
    df['% Využité kapacity'] = df['% Využité kapacity'].fillna(0)
    df['Počet produktov'] = df['Počet produktov'].fillna(0)
    df['Množstvo produktov'] = df['Množstvo produktov'].fillna(0)
    df['Sekcia'] = df['Sekcia'].fillna("Nezaradené")

    def parse_location(loc_name):
        try:
            parts = str(loc_name).split('-')
            zone = parts[0]
            ulicka = int(parts[1])
            pozicia = int(parts[2])
            uroven = int(parts[3]) if len(parts) >= 4 else 1
            return zone, ulicka, pozicia, uroven
        except:
            return None, None, None, None

    # Parsovanie lokácií
    coords_data = df.apply(lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1)
    df[['tmp_zone', 'ul_num', 'poz_num', 'ur_num']] = coords_data
    df = df.dropna(subset=['tmp_zone', 'ul_num', 'poz_num', 'ur_num'])
    
    # Vyčistenie percent
    def clean_percent(val):
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '.')
        try:
            return float(val)
        except:
            return 0.0

    df['util_num'] = df['% Využité kapacity'].apply(clean_percent)
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
    st.sidebar.header("📍 Základné filtre")
    
    # FILTER 1: ZÓNA
    available_zones = sorted(df_raw['tmp_zone'].unique())
    selected_zone = st.sidebar.selectbox("1. Vyber Zónu:", available_zones)
    zone_df = df_raw[df_raw['tmp_zone'] == selected_zone].copy()

    # FILTER 2: SEKCIÁ (Multiselect - môžeš vybrať viac naraz)
    available_sections = sorted(zone_df['Sekcia'].unique())
    selected_sections = st.sidebar.multiselect(
        "2. Vyber Sekciu (nepovinné):", 
        options=available_sections,
        default=available_sections,
        help="Ak vymažeš všetky sekcie, mapa bude prázdna. Predvolene sú vybrané všetky."
    )
    
    # Aplikácia filtra sekcií
    filtered_df = zone_df[zone_df['Sekcia'].isin(selected_sections)]

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Nastavenia zobrazenia")
    
    view_type = st.sidebar.radio("Typ zobrazenia:", ["Pohľad na celú plochu (Pôdorys)", "Detail jednej uličky (Profil)"])
    viz_mode = st.sidebar.radio("Farba podľa:", ["Využitie kapacity (%)", "Počet rôznych produktov"])

    # 2. LOGIKA FILTROVANIA PRE GRAF
    if view_type == "Pohľad na celú plochu (Pôdorys)":
        levels = sorted(filtered_df['ur_num'].unique().astype(int))
        level_options = ["Všetky úrovne (Priemer)"] + [str(l) for l in levels]
        selected_level = st.sidebar.selectbox("Vyber poschodie:", level_options)
        
        if selected_level == "Všetky úrovne (Priemer)":
            plot_df = filtered_df.groupby(['ul_num', 'poz_num']).agg({
                'util_num': 'mean', 'Počet produktov': 'mean', 'Množstvo produktov': 'sum'
            }).reset_index()
            plot_df['display_name'] = plot_df.apply(lambda r: f"{selected_zone}-{int(r['ul_num']):02d}-{int(r['poz_num']):02d}", axis=1)
        else:
            plot_df = filtered_df[filtered_df['ur_num'] == int(selected_level)].copy()
            plot_df['display_name'] = plot_df['Názov lokácie']
        
        x_col, y_col = 'ul_num', 'poz_num'
        x_label, y_label = "Ulička", "Pozícia"
    else:
        available_aisles = sorted(filtered_df['ul_num'].unique().astype(int))
        if not available_aisles:
            st.warning("V tejto sekcii/zóne sa nenachádzajú žiadne uličky.")
            st.stop()
        selected_aisle = st.sidebar.selectbox("Vyber uličku:", available_aisles)
        plot_df = filtered_df[filtered_df['ul_num'] == selected_aisle].copy()
        plot_df['display_name'] = plot_df['Názov lokácie']
        x_col, y_col = 'poz_num', 'ur_num'
        x_label, y_label = "Pozícia", "Úroveň"

    # --- AUTOMATICKÝ SCALING ---
    if not plot_df.empty:
        range_x = plot_df[x_col].max() - plot_df[x_col].min()
        range_y = plot_df[y_col].max() - plot_df[y_col].min()
        max_dim = max(range_x, range_y)

        if max_dim < 15: auto_size = 45
        elif max_dim < 40: auto_size = 28
        elif max_dim < 80: auto_size = 18
        else: auto_size = 13
    else:
        auto_size = 15

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
            color=plot_df[c_col] if not plot_df.empty else [],
            colorscale=c_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            line=dict(width=0.4, color='black')
        ),
        text=plot_df['display_name'] if not plot_df.empty else [],
        # Hover s pridanou sekciou (ak nie je v režime priemeru)
        customdata=plot_df[['ul_num', 'poz_num', 'util_num', 'Počet produktov', 'Množstvo produktov']] if not plot_df.empty else [],
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
        title=f"Zóna {selected_zone} | Aktívny výber sekcií: {len(selected_sections)}",
        xaxis=dict(title=x_label, tickmode='linear', dtick=1 if range_x < 40 else 5, gridcolor='#f8f8f8'),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1, gridcolor='#f8f8f8'),
        height=750,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # 4. TABUĽKA
    st.write("### Zoznam lokácií (podľa výberu)")
    st.dataframe(plot_df.sort_values([x_col, y_col]), use_container_width=True)

else:
    st.info("👋 Prosím, nahraj Excel alebo pridaj 'data.xlsx' na GitHub.")
