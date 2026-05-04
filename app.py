import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Alza Warehouse Map")

st.title("📊 Warehouse Visualizer Pro")

uploaded_file = st.sidebar.file_uploader("Nahraj Excel súbor (.xlsx)", type=["xlsx"])

def parse_location(loc_name):
    try:
        parts = str(loc_name).split('-')
        zona = parts[0][1] # Písmeno A, B, C...
        ulicka = int(parts[1])
        pozicia = int(parts[2])
        uroven = int(parts[3])
        return zona, ulicka, pozicia, uroven
    except:
        return None, None, None, None

def get_coordinates(row):
    zona, ulicka, pozicia, uroven = parse_location(row['Názov lokácie'])
    if not zona: return 0, 0
    
    # Škálovanie X súradnice pre lepšiu viditeľnosť uličiek
    # Každá zóna dostane väčší priestor (offset * 10)
    x_map = {'E': 0, 'A': 10, 'B': 25, 'C': 40, 'D': 55, 'F': 75}
    
    # Vertikálne zóny A,B,C,D
    if zona in ['A', 'B', 'C', 'D']:
        x = x_map[zona] + (ulicka * 1.5) # Rozostup medzi uličkami
        y = pozicia
    # Horizontálne zóny na krajoch
    elif zona == 'E':
        x = pozicia * 0.5
        y = ulicka + 50 # Posunieme ich vyššie/nižšie aby nezavadzali
    elif zona == 'F':
        x = x_map['F'] + (pozicia * 0.5)
        y = ulicka + 50
    else:
        x, y = 0, 0
    return x, y

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Extrakcia zóny a úrovne pre filtre
    df[['tmp_zona', 'tmp_ulicka', 'tmp_pozicia', 'tmp_uroven']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    
    # Prevod percent na číslo (ošetrenie 240.67...)
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # --- FILTRE V SIDEBARE ---
    st.sidebar.header("Filtre")
    selected_uroven = st.sidebar.multiselect(
        "Vyber poschodie (úroveň):", 
        options=sorted(df['tmp_uroven'].dropna().unique()),
        default=[sorted(df['tmp_uroven'].dropna().unique())[0]] # Predvolene prvé poschodie
    )
    
    max_util = st.sidebar.slider("Maximálne využitie pre farebnú škálu", 0, 200, 100)

    # Filtrovanie dát
    plot_df = df[df['tmp_uroven'].isin(selected_uroven)].copy()
    
    # Výpočet X, Y pre filtrované dáta
    coords = plot_df.apply(lambda r: pd.Series(get_coordinates(r)), axis=1)
    plot_df['x'], plot_df['y'] = coords[0], coords[1]

    # --- VYKRESLENIE ---
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df['x'], y=plot_df['y'],
        mode='markers',
        marker=dict(
            size=8,
            symbol='square',
            color=plot_df['util_num'],
            colorscale='RdYlGn_r',
            cmin=0, cmax=max_util, # Orezanie škály pre lepšie farby
            showscale=True,
            colorbar=dict(title="% Využitia")
        ),
        text=plot_df['Názov lokácie'],
        hovertemplate="<b>%{text}</b><br>Využitie: %{marker.color}%<br>Produkty: %{customdata[0]}<extra></extra>",
        customdata=plot_df[['Počet produktov']]
    ))

    fig.update_layout(
        title=f"Mapa skladu - Poschodie {selected_uroven}",
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        plot_bgcolor='white',
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Štatistiky
    col1, col2, col3 = st.columns(3)
    col1.metric("Počet lokácií", len(plot_df))
    col2.metric("Priemerné využitie", f"{round(plot_df['util_num'].mean(), 2)} %")
    col3.metric("Lokácie nad 100%", len(plot_df[plot_df['util_num'] > 100]))

    st.dataframe(plot_df[['Názov lokácie', 'Stanice', '% Využité kapacity', 'Množstvo produktov']])
