import streamlit as st
import pandas as pd
import plotly.graph_objects as go[1][2][3][4]

st.set_page_config(layout="wide", page_title="Sklad - Zóna A")

st.title("📍 Warehouse Visualizer: Zóna A")

uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor", type=["xlsx"])

def parse_location(loc_name):
    """Rozbije 2A-01-1-2 na uličku, pozíciu a úroveň"""
    try:
        parts = str(loc_name).split('-')
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return ulicka, pozicia, uroven
    except:
        return None, None, None

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 1. Spracovanie dát
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # Prevod percent na číslo
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. Sidebar - Ovládanie
    st.sidebar.header("Nastavenia")[3]
    
    # --- NOVÝ PREPÍNAČ METRIKY ---
    viz_mode = st.sidebar.radio(
        "Zobraziť podľa:",
        ["Využitie kapacity (%)", "Počet rôznych produktov"]
    )

    available_levels = sorted(df['ur_num'].unique().astype(int))
    selected_level = st.sidebar.selectbox("Vyber poschodie (úroveň):", available_levels)
    
    # 3. Filtrovanie dát
    plot_df = df[df['ur_num'] == selected_level].copy()
    plot_df = plot_df.sort_values(['ul_num', 'poz_num'])

    # Nastavenie parametrov podľa vybraného režimu
    if viz_mode == "Využitie kapacity (%)":
        color_col = 'util_num'
        color_scale = 'RdYlGn_r' # Červená -> Zelená
        c_min, c_max = 0, 100
        bar_title = "% Využitia"
    else:
        color_col = 'Počet produktov'
        color_scale = 'Viridis'   # Iná farba pre počet produktov (fialová -> žltá)
        c_min, c_max = 0, plot_df['Počet produktov'].max()
        bar_title = "Počet SKU"

    # 4. Vykreslenie mapy
    fig = go.Figure()[5][1][2][4][3][6]

    fig.add_trace(go.Scatter(
        x=plot_df['ul_num'],
        y=plot_df['poz_num'],
        mode='markers',
        marker=dict(
            size=14, # Trochu väčšie body pre lepšiu viditeľnosť
            symbol='square',
            color=plot_df[color_col],
            colorscale=color_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            colorbar=dict(title=bar_title)
        ),
        text=plot_df['Názov lokácie'],
        # Hover zobrazuje obe informácie bez ohľadu na režim
        hovertemplate=(
            "<b>Lokácia: %{text}</b><br>" +
            "Využitie: %{customdata[0]}%<br>" +
            "Počet produktov: %{customdata[1]}<br>" +
            "Celkom kusov: %{customdata[2]}<extra></extra>"
        ),
        customdata=plot_df[['util_num', 'Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        title=f"Mapa Zóny A (Úroveň {selected_level}) - {viz_mode}",
        xaxis=dict(title="Ulička", tickmode='linear', dtick=5),
        yaxis=dict(title="Pozícia v uličke"),
        width=1100,
        height=700,
        plot_bgcolor='#f9f9f9'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5. Štatistiky pod mapou
    c1, c2, c3 = st.columns(3)
    c1.metric("Zobrazené lokácie", len(plot_df))
    c2.metric("Priemerné zaplnenie", f"{round(plot_df['util_num'].mean(), 1)}%")
    c3.metric("Max.[3] produktov na lok.", int(plot_df['Počet produktov'].max()))

    st.dataframe(plot_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']], use_container_width=True)

else:
    st.info("Nahraj Excel súbor pre analýzu Zóny A.")import streamlit as st
import pandas as pd
import plotly.graph_objects as go[1][2][3][4]

st.set_page_config(layout="wide", page_title="Sklad - Zóna A")

st.title("📍 Warehouse Visualizer: Zóna A")

uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor", type=["xlsx"])

def parse_location(loc_name):
    """Rozbije 2A-01-1-2 na uličku, pozíciu a úroveň"""
    try:
        parts = str(loc_name).split('-')
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return ulicka, pozicia, uroven
    except:
        return None, None, None

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 1. Spracovanie dát
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # Prevod percent na číslo
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. Sidebar - Ovládanie
    st.sidebar.header("Nastavenia")[3]
    
    # --- NOVÝ PREPÍNAČ METRIKY ---
    viz_mode = st.sidebar.radio(
        "Zobraziť podľa:",
        ["Využitie kapacity (%)", "Počet rôznych produktov"]
    )

    available_levels = sorted(df['ur_num'].unique().astype(int))
    selected_level = st.sidebar.selectbox("Vyber poschodie (úroveň):", available_levels)
    
    # 3. Filtrovanie dát
    plot_df = df[df['ur_num'] == selected_level].copy()
    plot_df = plot_df.sort_values(['ul_num', 'poz_num'])

    # Nastavenie parametrov podľa vybraného režimu
    if viz_mode == "Využitie kapacity (%)":
        color_col = 'util_num'
        color_scale = 'RdYlGn_r' # Červená -> Zelená
        c_min, c_max = 0, 100
        bar_title = "% Využitia"
    else:
        color_col = 'Počet produktov'
        color_scale = 'Viridis'   # Iná farba pre počet produktov (fialová -> žltá)
        c_min, c_max = 0, plot_df['Počet produktov'].max()
        bar_title = "Počet SKU"

    # 4. Vykreslenie mapy
    fig = go.Figure()[5][1][2][4][3][6]

    fig.add_trace(go.Scatter(
        x=plot_df['ul_num'],
        y=plot_df['poz_num'],
        mode='markers',
        marker=dict(
            size=14, # Trochu väčšie body pre lepšiu viditeľnosť
            symbol='square',
            color=plot_df[color_col],
            colorscale=color_scale,
            cmin=c_min, cmax=c_max,
            showscale=True,
            colorbar=dict(title=bar_title)
        ),
        text=plot_df['Názov lokácie'],
        # Hover zobrazuje obe informácie bez ohľadu na režim
        hovertemplate=(
            "<b>Lokácia: %{text}</b><br>" +
            "Využitie: %{customdata[0]}%<br>" +
            "Počet produktov: %{customdata[1]}<br>" +
            "Celkom kusov: %{customdata[2]}<extra></extra>"
        ),
        customdata=plot_df[['util_num', 'Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        title=f"Mapa Zóny A (Úroveň {selected_level}) - {viz_mode}",
        xaxis=dict(title="Ulička", tickmode='linear', dtick=5),
        yaxis=dict(title="Pozícia v uličke"),
        width=1100,
        height=700,
        plot_bgcolor='#f9f9f9'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5. Štatistiky pod mapou
    c1, c2, c3 = st.columns(3)
    c1.metric("Zobrazené lokácie", len(plot_df))
    c2.metric("Priemerné zaplnenie", f"{round(plot_df['util_num'].mean(), 1)}%")
    c3.metric("Max.[3] produktov na lok.", int(plot_df['Počet produktov'].max()))

    st.dataframe(plot_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']], use_container_width=True)

else:
    st.info("Nahraj Excel súbor pre analýzu Zóny A.")
