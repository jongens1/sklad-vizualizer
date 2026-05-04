import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Nastavenie šírky stránky
st.set_page_config(layout="wide", page_title="Sklad - Zóna A")

st.title("📍 Warehouse Visualizer: Zóna A")

# Sidebar pre nahranie súboru
uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor (.xlsx)", type=["xlsx"])

def parse_location(loc_name):
    """Rozbije formát 2A-01-1-2 na uličku, pozíciu a úroveň"""
    try:
        parts = str(loc_name).split('-')
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return ulicka, pozicia, uroven
    except:
        return None, None, None

if uploaded_file:
    # Načítanie dát
    df = pd.read_excel(uploaded_file)
    
    # 1. Spracovanie dát
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # Prevod percent na číslo
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. Sidebar - Hlavné ovládanie
    st.sidebar.header("Nastavenia zobrazenia")
    
    # NOVÉ: Výber typu zobrazenia
    view_type = st.sidebar.radio(
        "Typ zobrazenia:",
        ["Pohľad na celú plochu (Pôdorys)", "Detail jednej uličky (Profil)"]
    )

    viz_mode = st.sidebar.radio(
        "Zobraziť farbu podľa:",
        ["Využitie kapacity (%)", "Počet rôznych produktov"]
    )

    # Dynamické filtre podľa typu zobrazenia
    if view_type == "Pohľad na celú plochu (Pôdorys)":
        available_levels = sorted(df['ur_num'].unique().astype(int))
        selected_level = st.sidebar.selectbox("Vyber poschodie (úroveň):", available_levels)
        plot_df = df[df['ur_num'] == selected_level].copy()
        x_axis_col, y_axis_col = 'ul_num', 'poz_num'
        x_label, y_label = "Ulička", "Pozícia"
    else:
        available_aisles = sorted(df['ul_num'].unique().astype(int))
        selected_aisle = st.sidebar.selectbox("Vyber uličku:", available_aisles)
        plot_df = df[df['ul_num'] == selected_aisle].copy()
        x_axis_col, y_axis_col = 'poz_num', 'ur_num'
        x_label, y_label = "Pozícia v uličke", "Poschodie (Úroveň)"

    # Nastavenie farieb
    if viz_mode == "Využitie kapacity (%)":
        color_col, color_scale, c_min, c_max, bar_title = 'util_num', 'RdYlGn_r', 0, 100, "% Využitia"
    else:
        color_col, color_scale, c_min, c_max, bar_title = 'Počet produktov', 'Viridis_r', 0, plot_df['Počet produktov'].max(), "Počet SKU"

    # 3. Vykreslenie mapy
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df[x_axis_col],
        y=plot_df[y_axis_col],
        mode='markers',
        marker=dict(
            size=18 if view_type == "Detail jednej uličky (Profil)" else 13,
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
            "<b>Lokácia: %{text}</b><br>" +
            "Využitie: %{customdata[0]}%<br>" +
            "Počet produktov: %{customdata[1]}<br>" +
            "Celkom kusov: %{customdata[2]}<extra></extra>"
        ),
        customdata=plot_df[['util_num', 'Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        title=f"{view_type} - Merané cez: {viz_mode}",
        xaxis=dict(title=x_label, tickmode='linear', dtick=1 if view_type == "Detail jednej uličky (Profil)" else 5),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1),
        width=1100,
        height=600,
        plot_bgcolor='#f8f9fb'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 4. Štatistiky a tabuľka
    col1, col2, col3 = st.columns(3)
    col1.metric("Počet lokácií v náhľade", len(plot_df))
    col2.metric("Priemerné zaplnenie", f"{round(plot_df['util_num'].mean(), 1)}%")
    col3.metric("Max. mix produktov", int(plot_df['Počet produktov'].max()) if len(plot_df) > 0 else 0)

    st.write("### Zoznam lokácií v aktuálnom výbere")
    st.dataframe(plot_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']].sort_values(['ur_num', 'poz_num']), use_container_width=True)

else:
    st.info("👋 Prosím, nahraj Excel súbor pre vizualizáciu.")
