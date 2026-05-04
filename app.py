import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Sklad - Zóna A")

st.title("📍 Vizualizácia: Zóna A")

uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor", type=["xlsx"])

def parse_location(loc_name):
    """Rozbije 2A-01-1-2 na komponenty ako čísla pre správne radenie a pozíciu"""
    try:
        parts = str(loc_name).split('-')
        # parts[0] = 2A, parts[1] = ulička, parts[2] = pozícia, parts[3] = úroveň
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return ulicka, pozicia, uroven
    except:
        return None, None, None

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 1. Extrakcia číselných hodnôt
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    
    # Odstránime riadky, ktoré sa nepodarilo naparsovať (napr. prázdne)
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # 2. Očista percent (prevod na číslo)
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 3. Sidebar filtre
    st.sidebar.header("Nastavenia zobrazenia")
    
    # Filter na úroveň (poschodie)
    available_levels = sorted(df['ur_num'].unique().astype(int))
    selected_level = st.sidebar.selectbox("Vyber poschodie (úroveň):", available_levels)
    
    # Filter na rozsah uličiek (ak by si chcel zoomovať)
    min_ul, max_ul = int(df['ul_num'].min()), int(df['ul_num'].max())
    ulicka_range = st.sidebar.slider("Rozsah uličiek:", min_ul, max_ul, (min_ul, max_ul))

    # 4. Filtrovanie dát pre graf
    mask = (df['ur_num'] == selected_level) & (df['ul_num'].between(ulicka_range[0], ulicka_range[1]))
    plot_df = df[mask].copy()

    # Zoradenie pre tabuľku (aby 1 bolo pred 10)
    plot_df = plot_df.sort_values(['ul_num', 'poz_num'])

    # 5. Vykreslenie mapy (X = Ulička, Y = Pozícia)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df['ul_num'],
        y=plot_df['poz_num'],
        mode='markers',
        marker=dict(
            size=12,
            symbol='square',
            color=plot_df['util_num'],
            colorscale='RdYlGn_r', # Červená (plné) -> Zelená (prázdne)
            cmin=0, cmax=100,      # Pevná škála 0-100%
            showscale=True,
            colorbar=dict(title="% Využitia")
        ),
        text=plot_df['Názov lokácie'],
        hovertemplate="<b>Lokácia: %{text}</b><br>Využitie: %{marker.color}%<br>Kusov: %{customdata}<extra></extra>",
        customdata=plot_df['Množstvo produktov']
    ))

    # Úprava vzhľadu - osi zodpovedajú uličkám a pozíciám
    fig.update_layout(
        title=f"Mapa Zóny A - Úroveň {selected_level}",
        xaxis=dict(title="Ulička", tickmode='linear', dtick=5, gridcolor='lightgrey'),
        yaxis=dict(title="Pozícia v uličke", tickmode='linear', dtick=5, gridcolor='lightgrey'),
        width=1200,
        height=600,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 6. Štatistiky a tabuľka
    st.subheader(f"Detailné dáta pre Úroveň {selected_level}")
    st.dataframe(plot_df[['Názov lokácie', 'Stanice', 'Množstvo produktov', '% Využité kapacity']], use_container_width=True)

else:
    st.info("Nahraj Excel súbor pre analýzu Zóny A.")
