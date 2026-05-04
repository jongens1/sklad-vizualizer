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
    
    # 1. Spracovanie dát a extrakcia číselných hodnôt
    df[['ul_num', 'poz_num', 'ur_num']] = df.apply(
        lambda r: pd.Series(parse_location(r['Názov lokácie'])), axis=1
    )
    df = df.dropna(subset=['ul_num', 'poz_num', 'ur_num'])

    # Prevod percent na číslo
    df['util_num'] = df['% Využité kapacity'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)

    # 2. Sidebar - Hlavné ovládanie
    st.sidebar.header("Nastavenia zobrazenia")
    
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
        # Pridanie možnosti "Všetky úrovne" do zoznamu
        levels = sorted(df['ur_num'].unique().astype(int))
        level_options = ["Všetky úrovne (Priemer)"] + [str(l) for l in levels]
        selected_level = st.sidebar.selectbox("Vyber poschodie:", level_options)
        
        if selected_level == "Všetky úrovne (Priemer)":
            # Agregácia - spriemerovanie hodnôt pre každú súradnicu [ulička, pozícia]
            plot_df = df.groupby(['ul_num', 'poz_num']).agg({
                'util_num': 'mean',
                'Počet produktov': 'mean',
                'Množstvo produktov': 'sum' # Tu dávame sumu, aby sme videli celkový počet kusov v stĺpci
            }).reset_index()
            plot_df['Názov lokácie'] = plot_df.apply(lambda r: f"Ulička {int(r['ul_num'])}, Poz. {int(r['poz_num'])} (Celý stĺpec)", axis=1)
            plot_df['ur_num'] = 0 # Dummy hodnota pre zoradenie
        else:
            plot_df = df[df['ur_num'] == int(selected_level)].copy()
        
        x_axis_col, y_axis_col = 'ul_num', 'poz_num'
        x_label, y_label = "Ulička (Rada)", "Pozícia v uličke"
    
    else: # Detail jednej uličky
        available_aisles = sorted(df['ul_num'].unique().astype(int))
        selected_aisle = st.sidebar.selectbox("Vyber uličku:", available_aisles)
        plot_df = df[df['ul_num'] == selected_aisle].copy()
        x_axis_col, y_axis_col = 'poz_num', 'ur_num'
        x_label, y_label = "Pozícia v uličke", "Poschodie (Úroveň)"

    # Nastavenie farieb
    if viz_mode == "Využitie kapacity (%)":
        color_col, color_scale, c_min, c_max, bar_title = 'util_num', 'RdYlGn_r', 0, 100, "% Využitia"
    else:
        color_col, color_scale, c_min, c_max, bar_title = 'Počet produktov', 'Viridis_r', 0, plot_df['Počet produktov'].max() if len(plot_df) > 0 else 10, "Počet SKU"

    # 3. Vykreslenie mapy
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
            "Priem. využitie: %{customdata[0]:.1f}%<br>" +
            "Priem. SKU: %{customdata[1]:.1f}<br>" +
            "Celkom kusov v stĺpci: %{customdata[2]}<extra></extra>"
        ),
        customdata=plot_df[['util_num', 'Počet produktov', 'Množstvo produktov']]
    ))

    fig.update_layout(
        title=f"{view_type} - {viz_mode}",
        xaxis=dict(title=x_label, tickmode='linear', dtick=5, gridcolor='#eee'),
        yaxis=dict(title=y_label, tickmode='linear', dtick=1 if view_type == "Detail jednej uličky (Profil)" else 5, gridcolor='#eee'),
        width=1100,
        height=650,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 4. Metriky
    col1, col2, col3 = st.columns(3)
    col1.metric("Zobrazené body (stĺpce/lokácie)", len(plot_df))
    col2.metric("Priemerné zaplnenie (výber)", f"{round(plot_df['util_num'].mean(), 1)}%" if len(plot_df) > 0 else "0%")
    col3.metric("Max. počet produktov", round(plot_df['Počet produktov'].max(), 1) if len(plot_df) > 0 else 0)

    # 5. Detailná tabuľka
    st.write("### Detailný zoznam zobrazených dát")
    sorted_df = plot_df.sort_values(['ul_num', 'poz_num'])
    # Ak sme v režime priemeru, stĺpce premenujeme pre jasnosť
    if view_type == "Pohľad na celú plochu (Pôdorys)" and selected_level == "Všetky úrovne (Priemer)":
        display_df = sorted_df[['Názov lokácie', 'Počet produktov', 'Množstvo produktov', 'util_num']].copy()
        display_df.columns = ['Pozícia', 'Priemerný počet SKU', 'Celkom kusov', 'Priemerné využitie %']
        st.dataframe(display_df, use_container_width=True)
    else:
        display_columns = ['Názov lokácie', 'Počet produktov', 'Množstvo produktov', '% Využité kapacity']
        st.dataframe(sorted_df[display_columns], use_container_width=True)

else:
    st.info("👋 Nahraj Excel pre vizualizáciu.")
