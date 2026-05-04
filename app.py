import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Warehouse Map")

st.title("📦 Vizualizácia skladu (Loop Layout)")

# 1. Upload súboru
uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor (.xlsx)", type=["xlsx"])

def get_coordinates(row):
    """Logika pre umiestnenie regálov na mapu podľa tvojho obrázku"""
    zona = str(row['Zóna']).upper()
    sekcia = str(row['Sekcia']).upper()
    
    # Mapovanie sekcií A-F na číselnú os Y (vertikálne v rámci regálu)
    y_map = {'A': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1}
    y_val = y_map.get(sekcia, 0)

    # X súradnice podľa zón
    if zona == 'E': x = 1   # Vľavo
    elif zona == 'A': x = 5  # Stred - blok 1
    elif zona == 'B': x = 8  # Stred - blok 2
    elif zona == 'C': x = 11 # Stred - blok 3
    elif zona == 'D': x = 14 # Stred - blok 4
    elif zona == 'F': x = 18 # Vpravo
    else: x = 0
    
    return x, y_val

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Výpočet súradníc
    df[['x', 'y']] = df.apply(lambda r: pd.Series(get_coordinates(r)), axis=1)

    # Vykreslenie mapy
    fig = go.Figure()

    # Pridanie bodov (regálov)
    fig.add_trace(go.Scatter(
        x=df['x'], y=df['y'],
        mode='markers+text',
        marker=dict(
            size=25,
            symbol='square',
            color=df['% využitia kapacity'],
            colorscale='RdYlGn_r', # Červená (plné) -> Zelená (voľné)
            showscale=True,
            colorbar=dict(title="% Využitia")
        ),
        text=df['Názov lokácie'],
        textposition="top center",
        hovertemplate="<b>%{text}</b><br>Produkty: %{customdata[0]}<br>Kusy: %{customdata[1]}<extra></extra>",
        customdata=df[['Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        plot_bgcolor='rgba(240,240,240,0.5)',
        xaxis=dict(showgrid=False, zeroline=False, range=[0, 20]),
        yaxis=dict(showgrid=False, zeroline=False, range=[0, 7]),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df) # Zobrazenie tabuľky pod tým
else:
    st.info("👋 Ahoj! Nahraj Excel, ktorý obsahuje stĺpce: Názov lokácie, Zóna, Sekcia, Počet produktov, Množstvo produktov, % využitia kapacity")
