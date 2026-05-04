import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Nastavenie šírky stránky
st.set_page_config(layout="wide", page_title="Warehouse Map - Pro")

st.title("📊 Warehouse Multi-Zone Visualizer")

# Sidebar pre nahranie súboru
st.sidebar.header("📁 Dáta")
uploaded_file = st.sidebar.file_uploader("Nahraj vlastný Excel súbor (.xlsx)", type=["xlsx"])

def parse_location(loc_name):
    """
    Rozbije formát napr. 1A-01-1-2 alebo 2SW-01-1-2 na komponenty.
    Zóna je teraz celá prvá časť pred prvou pomlčkou (napr. 1A, 2A, 2SW).
    """
    try:
        parts = str(loc_name).split('-')
        # Zóna je celá prvá časť (napr. 1A, 2A, 2SW)
        zone = parts[0]
        
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return zone, ulicka, pozicia, uroven
    except:
        return None, None, None, None

# LOGIKA NAČÍTANIA DÁT
df = None
data_source = ""

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    data_source = "Nahraný súbor"
elif os.path.exists("data.xlsx"):
    df = pd.read_excel("data.xlsx")
    data_source = "Predvolené dáta (data.xlsx)"

if df is not None:
    # 1. Prvotné spracovanie
    coords_data = df.apply(lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1)
    df[['tmp_zone', 'ul_num', 'poz_num', 'ur_num']] = coords_data
    
    # Vyčistenie a prevod percent
    df = df.dropna(subset=['tmp_zone', 'ul_num', 'poz_num', 'ur_num'])
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. SIDEBAR - FILTRE
    st.sidebar.info(f"Aktuálny zdroj: {data_source}")
    st.sidebar.markdown("---")
    st.sidebar.header("📍 Nastavenia zobrazenia")
    
    # FILTER 1: ZÓNA (teraz obsahuje aj číslo, napr. 1A, 2A)
    available_zones = sorted(df['tmp_zone'].unique())
    selected_zone = st.sidebar.selectbox("Vyber Zónu (napr. 1A, 2A):", available_zones)
    zone_df = df[df['tmp_zone'] == selected_zone].copy()

    # FILTER 2: TYP ZOBRAZENIA
    view_type = st.sidebar.radio(
        "Typ zobrazenia:",
        ["Pohľad na celú plochu (Pôdorys)", "Detail jednej uličky (Profil)"]
    )

    # FILTER 3: METRIKA FARBY
    viz_mode = st.sidebar.radio(
        "Zobraziť farbu podľa:",
        ["Využitie kapacity (%)", "Počet rôznych produktov"]
    )

    # 3. FILTROVANIE DÁT (Pôdorys vs Profil)
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

    # Nastavenie farebnej škály
    if viz_mode == "Využitie kapacity (%)":
        color_col, color_scale, c_min, c_max, bar_title = 'util_num', 'RdYlGn_r', 0, 100, "% Využitia"
    else:
        max_sku = plot_df['Počet produktov'].max() if len(plot_df) > 0 else 10
        color_col, color_scale, c_min, c_max, bar_title = 'Počet produktov', 'Viridis_r', 0, max_sku, "Počet SKU"

    # 4. VYKRESLENIE
    st.subheader(f"Zobrazenie: Zóna {selected_zone} | {view_type}")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df[x_axis_col],
        y=plot_df[y_axis_col],
        mode='markers',
        marker=dict(
            size=15 if view_type == "Detail jednej uličky (Profil)" else 12,
            symbol='square',
            color=plot_df[color_col],
            colorscale=color_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            colorbar=dict(title=bar_title),
            line=dict(width=0.5, color='DarkSlateGrey')
        ),
        text=plot_df['Názov lokácie'],
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Využitie: %{customdata[0]:.1f}%<br>" +
            "Počet produktov: %{customdata[1]:.1f}<br>" +
            "Celkom kusov: %{customdata[2]}<extra></extra>"
        ),
        customdata=plot_df[['util_num', 'Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        xaxis=dict(title=x_label, tickmode='linear', dtick=5 if view_type != "Detail jednej uličky (Profil)" else 1, gridcolor='#eee'),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1 if view_type == "Detail jednej uličky (Profil)" else 5, gridcolor='#eee'),
        width=1100,
        height=650,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5. KPI METRIKY
    m1, m2, m3 = st.columns(3)
    m1.metric("Počet zobrazených bodov", len(plot_df))
    m2.metric("Priemerné zaplnenie", f"{round(plot_df['util_num'].mean(), 1)}%" if len(plot_df) > 0 else "0%")
    m3.metric("Max. počet produktov", round(plot_df['Počet produktov'].max(), 1) if len(plot_df) > 0 else 0)

    # 6. TABUĽKA
    st.write("### Detailný zoznam lokácií")
    sorted_df = plot_df.sort_values(['ul_num', 'poz_num'])
    
    if 'selected_level' in locals() and selected_level == "Všetky úrovne (Priemer)":
        display_df = sorted_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', 'util_num']].copy()
        display_df.columns = ['Pozícia', 'Priemerný počet SKU', 'Celkom kusov', 'Priemerné využitie %']
        st.dataframe(display_df, use_container_width=True)
    else:
        display_cols = ['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']
        st.dataframe(sorted_df[display_cols], use_container_width=True)

else:
    st.warning("⚠️ Žiadne dáta nenájdené.")
    st.info("Nahraj Excel súbor cez sidebar alebo pridaj súbor s názvom 'data.xlsx' do GitHub repozitára.")
