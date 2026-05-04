import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide", page_title="Warehouse Loop Visualizer")

st.title("🔄 Warehouse Visualizer: Celý Loop")

@st.cache_data
def load_and_parse_data(file_source):
    df = pd.read_excel(file_source)
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

    coords_data = df.apply(lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1)
    df[['tmp_zone', 'ul_num', 'poz_num', 'ur_num']] = coords_data
    df = df.dropna(subset=['tmp_zone', 'ul_num', 'poz_num', 'ur_num'])
    
    def clean_percent(val):
        if isinstance(val, str): val = val.replace('%', '').replace(',', '.')
        try: return float(val)
        except: return 0.0

    df['util_num'] = df['% Využité kapacity'].apply(clean_percent)
    return df

uploaded_file = st.sidebar.file_uploader("Nahraj vlastný Excel (.xlsx)", type=["xlsx"])

df_raw = None
if uploaded_file:
    df_raw = load_and_parse_data(uploaded_file)
elif os.path.exists("data.xlsx"):
    df_raw = load_and_parse_data("data.xlsx")

if df_raw is not None:
    # --- LOGIKA GLOBÁLNYCH SÚRADNÍC PRE LOOP ---
    def get_global_coords(row):
        z = row['tmp_zone']
        u = row['ul_num']
        p = row['poz_num']
        
        # Stredové vertikálne zóny (A, B, C, D)
        if z == '2A': return 20 + u, p
        if z == '2B': return 40 + u, p
        if z == '2C': return 60 + u, p
        if z == '2D': return 80 + u, p
        
        # Bočné horizontálne zóny (E vľavo, F vpravo)
        if z == '2E': return p * 0.3, u + 10 # E je pred uličkami
        if z == '2F': return 100 + (p * 0.3), u + 10 # F je za uličkami
        
        # Pre ostatné (1A, 3A atď.) použijeme základný grid
        return u, p

    st.sidebar.header("📍 1. Výber oblasti")
    main_options = ["CELÝ LOOP (Zóny 2A-2F)"] + sorted(df_raw['tmp_zone'].unique())
    selected_main = st.sidebar.selectbox("Vyber zobrazenie:", main_options)

    if selected_main == "CELÝ LOOP (Zóny 2A-2F)":
        zone_df = df_raw[df_raw['tmp_zone'].isin(['2A','2B','2C','2D','2E','2F'])].copy()
        is_loop = True
    else:
        zone_df = df_raw[df_raw['tmp_zone'] == selected_main].copy()
        is_loop = False

    # --- FILTROVANIE SEKCIÍ ---
    st.sidebar.header("🏢 2. Filtrovať Sekcie")
    available_sections = sorted(zone_df['Sekcia'].unique())

    def set_all(val):
        for s in available_sections: st.session_state[f"cb_{s}"] = val

    col_a, col_b = st.sidebar.columns(2)
    col_a.button("Všetky", on_click=set_all, args=(True,))
    col_b.button("Žiadna", on_click=set_all, args=(False,))

    selected_sects = []
    with st.sidebar.expander("Zoznam sekcií", expanded=not is_loop):
        for sect in available_sections:
            if f"cb_{sect}" not in st.session_state: st.session_state[f"cb_{sect}"] = True
            if st.checkbox(sect, key=f"cb_{sect}"): selected_sects.append(sect)

    st.sidebar.markdown("---")
    viz_mode = st.sidebar.radio("Farba podľa:", ["Využitie kapacity (%)", "Počet produktov"])
    
    # Pre Loop automaticky zapneme priemer všetkých úrovní, aby to bolo prehľadné
    if is_loop:
        selected_level = "Všetky úrovne (Priemer)"
        plot_df = zone_df.groupby(['ul_num', 'poz_num', 'tmp_zone', 'Sekcia']).agg({
            'util_num': 'mean', 'Počet produktov': 'mean', 'Množstvo produktov': 'sum'
        }).reset_index()
        plot_df['display_name'] = plot_df.apply(lambda r: f"{r['tmp_zone']}-{int(r['ul_num']):02d}-{int(r['poz_num']):02d}", axis=1)
    else:
        levels = sorted(zone_df['ur_num'].unique().astype(int))
        selected_level = st.sidebar.selectbox("Vyber poschodie:", ["Všetky úrovne (Priemer)"] + [str(l) for l in levels])
        if selected_level == "Všetky úrovne (Priemer)":
            plot_df = zone_df.groupby(['ul_num', 'poz_num', 'Sekcia']).agg({'util_num': 'mean', 'Počet produktov': 'mean', 'Množstvo produktov': 'sum'}).reset_index()
            plot_df['display_name'] = plot_df.apply(lambda r: f"{selected_main}-{int(r['ul_num']):02d}-{int(r['poz_num']):02d}", axis=1)
        else:
            plot_df = zone_df[zone_df['ur_num'] == int(selected_level)].copy()
            plot_df['display_name'] = plot_df['Názov lokácie']

    # Priradenie globálnych súradníc
    coords = plot_df.apply(lambda r: pd.Series(get_global_coords(r)), axis=1)
    plot_df['x_glob'], plot_df['y_glob'] = coords[0], coords[1]

    # Rozdelenie na Aktívne/Neaktívne
    active_mask = plot_df['Sekcia'].isin(selected_sects)
    active_df = plot_df[active_mask].copy()
    inactive_df = plot_df[~active_mask].copy()

    # Vykreslenie
    fig = go.Figure()

    # 1. NEAKTÍVNE (Sivé)
    fig.add_trace(go.Scatter(
        x=inactive_df['x_glob'], y=inactive_df['y_glob'],
        mode='markers',
        marker=dict(size=8 if is_loop else 14, symbol='square', color='#F0F0F0', line=dict(width=0.2, color='#CCCCCC')),
        text=inactive_df['display_name'],
        hoverinfo='text'
    ))

    # 2. AKTÍVNE
    if not active_df.empty:
        c_col, c_scale = ('util_num', 'RdYlGn_r') if viz_mode == "Využitie kapacity (%)" else ('Počet produktov', 'Viridis_r')
        fig.add_trace(go.Scatter(
            x=active_df['x_glob'], y=active_df['y_glob'],
            mode='markers',
            marker=dict(
                size=10 if is_loop else 16, symbol='square', color=active_df[c_col],
                colorscale=c_scale, cmin=0, cmax=100 if viz_mode == "Využitie kapacity (%)" else active_df[c_col].max(),
                showscale=True, line=dict(width=0.4, color='black')
            ),
            text=active_df['display_name'],
            customdata=active_df[['util_num', 'Počet produktov', 'Sekcia']],
            hovertemplate="<b>%{text}</b><br>Sekcia: %{customdata[2]}<br>Využitie: %{customdata[0]:.1f}%<extra></extra>"
        ))

    fig.update_layout(
        title=f"Vizualizácia: {selected_main}",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=800, plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Nahraj Excel pre zobrazenie Loopu.")
