import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide", page_title="Warehouse Map")

st.title("📦 Vizualizácia skladu (Loop Layout)")

# 1. Upload súboru
uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor (.xlsx)", type=["xlsx"])

def parse_location(loc_name):
    """
    Rozoberie názov lokácie (napr. 2A-05-26-6) na časti.
    Predpokladáme: [2][Zóna]-[Ulička]-[Pozícia]-[Úroveň]
    """
    try:
        # Extrahujeme písmeno zóny (druhý znak, napr. z '2A' vezme 'A')
        parts = loc_name.split('-')
        zona = parts[0][1] # 'A'
        ulicka = int(parts[1]) # 5
        pozicia = int(parts[2]) # 26
        uroven = int(parts[3]) # 6
        return zona, ulicka, pozicia, uroven
    except:
        return None, None, None, None

def get_coordinates(row):
    """
    Určí X a Y súradnice pre mapu na základe zóny a uličky.
    """
    zona, ulicka, pozicia, uroven = parse_location(str(row['Názov lokácie']))
    
    if not zona:
        return 0, 0

    # Nastavenie X súradnice podľa tvojho nákresu (E vľavo, ABCD v strede, F vpravo)
    # Čím vyššie číslo X, tým viac vpravo na mape
    x_offset = {'E': 1, 'A': 5, 'B': 10, 'C': 15, 'D': 20, 'F': 25}
    base_x = x_offset.get(zona, 0)
    
    # K základnej pozícii zóny pripočítame uličku, aby regály neboli na sebe
    x = base_x + (ulicka * 0.2)
    # Y bude pozícia v uličke (ako hlboko do skladu to je)
    y = pozicia
    
    return x, y

if uploaded_file:
    # Načítanie Excelu
    df = pd.read_excel(uploaded_file)
    
    # Očista dát - premeníme percentá (napr. "2,21%") na čísla
    if '% Využité kapacity' in df.columns:
        df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)
    else:
        st.error("V Exceli chýba stĺpec '% Využité kapacity'!")
        st.stop()

    # Výpočet súradníc pre mapu
    coords = df.apply(lambda r: pd.Series(get_coordinates(r)), axis=1)
    df['x'], df['y'] = coords[0], coords[1]

    # Vykreslenie mapy
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['x'], 
        y=df['y'],
        mode='markers',
        marker=dict(
            size=10,
            symbol='square',
            color=df['util_num'],
            colorscale='RdYlGn_r', # Červená (plné) -> Zelená (voľné)
            showscale=True,
            colorbar=dict(title="% Využitia")
        ),
        text=df['Názov lokácie'],
        hovertemplate="<b>%{text}</b><br>Produkty: %{customdata[0]}<br>Kusy: %{customdata[1]}<br>Využitie: %{customdata[2]}%<extra></extra>",
        customdata=df[['Počet produktov', 'Množstvo produktov', 'util_num']]
    ))

    fig.update_layout(
        title="Mapa obsadenosti regálov",
        plot_bgcolor='white',
        xaxis=dict(title="Zóny (E -> A -> B -> C -> D -> F)", showgrid=False),
        yaxis=dict(title="Hĺbka uličky (Pozícia)", showgrid=True),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Tabuľka s filtrami
    st.subheader("Prehľad dát")
    zona_filter = st.multiselect("Filtruj podľa zóny", options=['A', 'B', 'C', 'D', 'E', 'F'], default=['A', 'B'])
    
    # Pomocný stĺpec pre filtrovanie
    df['zona_tmp'] = df['Názov lokácie'].apply(lambda x: str(x)[1] if len(str(x)) > 1 else '')
    filtered_df = df[df['zona_tmp'].isin(zona_filter)]
    
    st.dataframe(filtered_df[['Názov lokácie', 'Stanice', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']])

else:
    st.info("Nahraj svoj Excel súbor. Očakávam stĺpce: Názov lokácie, Stanice, Sekcia, Počet produktov, Množstvo produktov, % Využité kapacity")
