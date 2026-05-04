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
    
    # 1. Spracovanie a parsovanie lokácií
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    # Odstránenie neplatných riadkov
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # Prevod percent na číslo
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. Sidebar - Ovládacie prvky
    st.sidebar.header("Nastavenia zobrazenia")
    
    viz_mode = st.sidebar.radio(
        "Zobraziť farbu podľa:",
        ["Využitie kapacity (%)", "Počet rôznych produktov"]
    )

    available_levels = sorted(df['ur_num'].unique().astype(int))
    selected_level = st.sidebar.selectbox("Vyber poschodie (úroveň):", available_levels)
    
    # 3. Filtrovanie dát pre mapu
    plot_df = df[df['ur_num'] == selected_level].copy()
    plot_df = plot_df.sort_values(['ul_num', 'poz_num'])

    # Nastavenie parametrov podľa režimu
    if viz_mode == "Využitie kapacity (%)":
        color_col = 'util_num'
        color_scale = 'RdYlGn_r' 
        c_min, c_max = 0, 100
        bar_title = "% Využitia"
    else:
        color_col = 'Počet produktov'
        # Viridis_r: Fialová = MAX, Žltá = MIN
        color_scale = 'Viridis_r' 
        c_min, c_max = 0, plot_df['Počet produktov'].max()
        bar_title = "Počet SKU"

    # 4. Vykreslenie mapy
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df['ul_num'],
        y=plot_df['poz_num'],
        mode='markers',
        marker=dict(
            size=15,
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
        title=f"Mapa Zóny A (Úroveň {selected_level}) - Režim: {viz_mode}",
        xaxis=dict(title="Ulička", tickmode='linear', dtick=5, gridcolor='#eee'),
        yaxis=dict(title="Pozícia v uličke", tickmode='linear', dtick=5, gridcolor='#eee'),
        width=1100,
        height=750,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5. Štatistiky pod mapou
    col1, col2, col3 = st.columns(3)
    col1.metric("Počet lokácií", len(plot_df))
    col2.metric("Priemerné zaplnenie", f"{round(plot_df['util_num'].mean(), 1)}%")
    col3.metric("Max. mix produktov", int(plot_df['Počet produktov'].max()))

    # 6. Tabuľka
    st.write("### Detailný zoznam lokácií")
    st.dataframe(plot_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']], use_container_width=True)

else:
    st.info("👋 Prosím, nahraj Excel súbor pre vizualizáciu.")
