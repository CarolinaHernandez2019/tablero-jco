# -*- coding: utf-8 -*-
"""
Tablero JCO - Explorador de Priorizacion Territorial
Jovenes con Oportunidades - SDIS

Version 2.0 - Con ranking dinamico por grupos SISBEN
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# Configuracion de pagina
st.set_page_config(
    page_title="Tablero JCO - Priorizacion",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Obtener directorio del script
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    SCRIPT_DIR = "."

# Archivos de datos
DATA_FILE = os.path.join(SCRIPT_DIR, 'Tabla_Completa_Priorizacion_JCO.xlsx')
SHAPEFILE_PATH = os.path.join(SCRIPT_DIR, 'UPZ06_22', 'pensionadosupz_0622.shp')
GEO_EXCEL = os.path.join(SCRIPT_DIR, 'upz-bogota-para-shape-con-resultad.xlsx')

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .filter-info {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .grupo-a { background-color: #d73027; color: white; padding: 0.2rem 0.5rem; border-radius: 5px; }
    .grupo-b { background-color: #fc8d59; color: white; padding: 0.2rem 0.5rem; border-radius: 5px; }
    .grupo-c { background-color: #fee08b; color: black; padding: 0.2rem 0.5rem; border-radius: 5px; }
    .grupo-d { background-color: #91cf60; color: black; padding: 0.2rem 0.5rem; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Mapeo de localidades
LOCALIDADES_MAP = {
    1: 'Usaquen', 2: 'Chapinero', 3: 'Santa Fe', 4: 'San Cristobal',
    5: 'Usme', 6: 'Tunjuelito', 7: 'Bosa', 8: 'Kennedy',
    9: 'Fontibon', 10: 'Engativa', 11: 'Suba', 12: 'Barrios Unidos',
    13: 'Teusaquillo', 14: 'Los Martires', 15: 'Antonio Narino',
    16: 'Puente Aranda', 17: 'La Candelaria', 18: 'Rafael Uribe Uribe',
    19: 'Ciudad Bolivar', 20: 'Sumapaz'
}

# Cargar datos
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel(DATA_FILE)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

@st.cache_data
def cargar_shapefile():
    """Cargar shapefile con geometrias de UPZ"""
    try:
        if os.path.exists(SHAPEFILE_PATH):
            gdf = gpd.read_file(SHAPEFILE_PATH)
            # Filtrar solo UPZ (excluir UPR rurales)
            gdf = gdf[gdf['UPLCODIGO'].str.startswith('UPZ', na=False)].copy()
            gdf['CODIGO_UPZ'] = gdf['UPLCODIGO'].str.replace('UPZ', '').astype(int)
            # Reproyectar a WGS84
            gdf = gdf.to_crs(epsg=4326)
            return gdf
        else:
            return None
    except Exception as e:
        st.warning(f"No se pudo cargar shapefile: {e}")
        return None

@st.cache_data
def cargar_geodatos_excel():
    """Cargar geodatos desde Excel (fallback)"""
    try:
        geo = pd.read_excel(GEO_EXCEL)
        return geo
    except:
        return None

def calcular_ranking_dinamico(df, grupos_seleccionados):
    """
    Recalcula el ranking basado en los grupos SISBEN seleccionados

    Args:
        df: DataFrame con datos completos
        grupos_seleccionados: Lista de grupos a incluir ('A', 'B', 'C', 'D')

    Returns:
        DataFrame con nuevo ranking y poblacion calculada
    """
    df_calc = df.copy()

    # Calcular poblacion segun grupos seleccionados
    col_grupos = [f'GRUPO_{g}' for g in grupos_seleccionados]
    col_hombres = [f'HOMBRES_{g}' for g in grupos_seleccionados]
    col_mujeres = [f'MUJERES_{g}' for g in grupos_seleccionados]

    df_calc['POB_SELECCIONADA'] = df_calc[col_grupos].sum(axis=1)
    df_calc['HOMBRES_SEL'] = df_calc[col_hombres].sum(axis=1)
    df_calc['MUJERES_SEL'] = df_calc[col_mujeres].sum(axis=1)

    # Ordenar por poblacion seleccionada y asignar nuevo ranking
    df_calc = df_calc.sort_values('POB_SELECCIONADA', ascending=False).reset_index(drop=True)
    df_calc['RANKING_DINAMICO'] = range(1, len(df_calc) + 1)

    return df_calc

def crear_geojson_desde_shapefile(gdf, df_datos):
    """Crear GeoJSON combinando shapefile con datos"""
    features = []

    merged = gdf.merge(df_datos, on='CODIGO_UPZ', how='inner')

    for idx, row in merged.iterrows():
        try:
            geom = row.geometry.__geo_interface__
            feature = {
                "type": "Feature",
                "id": str(row['CODIGO_UPZ']),
                "properties": {
                    "CODIGO_UPZ": int(row['CODIGO_UPZ']),
                    "UPZ": row.get('UPZ', row.get('NOMBRE', '')),
                    "LOCALIDAD": row.get('LOCALIDAD', 'Sin datos'),
                    "RANKING": int(row.get('RANKING_DINAMICO', row.get('RANKING', 0))),
                    "POB_SELECCIONADA": int(row.get('POB_SELECCIONADA', 0)),
                    "JOVENES_TOTAL": int(row.get('JOVENES_TOTAL', 0)),
                    "GRUPO_A": int(row.get('GRUPO_A', 0)),
                    "GRUPO_B": int(row.get('GRUPO_B', 0)),
                    "GRUPO_C": int(row.get('GRUPO_C', 0)),
                    "GRUPO_D": int(row.get('GRUPO_D', 0)),
                },
                "geometry": geom
            }
            features.append(feature)
        except Exception as e:
            continue

    return {"type": "FeatureCollection", "features": features}

def crear_geojson_desde_excel(geo_df, df_datos):
    """Crear GeoJSON desde Excel (fallback)"""
    features = []

    merged = geo_df.merge(df_datos, on='CODIGO_UPZ', how='inner')

    for _, row in merged.iterrows():
        try:
            geo_shape = json.loads(row['geo_shape'])
            feature = {
                "type": "Feature",
                "id": str(row['CODIGO_UPZ']),
                "properties": {
                    "CODIGO_UPZ": int(row['CODIGO_UPZ']),
                    "UPZ": row.get('UPZ', ''),
                    "LOCALIDAD": row.get('LOCALIDAD', 'Sin datos'),
                    "RANKING": int(row.get('RANKING_DINAMICO', row.get('RANKING', 0))),
                    "POB_SELECCIONADA": int(row.get('POB_SELECCIONADA', 0)),
                    "JOVENES_TOTAL": int(row.get('JOVENES_TOTAL', 0)),
                    "GRUPO_A": int(row.get('GRUPO_A', 0)),
                    "GRUPO_B": int(row.get('GRUPO_B', 0)),
                    "GRUPO_C": int(row.get('GRUPO_C', 0)),
                    "GRUPO_D": int(row.get('GRUPO_D', 0)),
                },
                "geometry": geo_shape
            }
            features.append(feature)
        except:
            continue

    return {"type": "FeatureCollection", "features": features}

# Cargar datos
df = cargar_datos()
gdf = cargar_shapefile()
geo_excel = cargar_geodatos_excel()

# Header principal
st.markdown('<h1 class="main-header">Tablero de Priorizacion JCO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Secretaria de Integracion Social | Datos SISBEN IV</p>', unsafe_allow_html=True)

# ============================================
# SIDEBAR - FILTROS DINAMICOS
# ============================================
st.sidebar.markdown("### Grupos SISBEN")
st.sidebar.markdown("""
<small>Selecciona los grupos SISBEN a sumar.</small>
""", unsafe_allow_html=True)

col_a, col_b = st.sidebar.columns(2)
with col_a:
    incluir_a = st.checkbox("Grupo A", value=True, help="Pobreza Extrema")
    incluir_c = st.checkbox("Grupo C", value=True, help="Vulnerable")
with col_b:
    incluir_b = st.checkbox("Grupo B", value=True, help="Pobreza Moderada")
    incluir_d = st.checkbox("Grupo D", value=False, help="No Vulnerable")

grupos_seleccionados = []
if incluir_a: grupos_seleccionados.append('A')
if incluir_b: grupos_seleccionados.append('B')
if incluir_c: grupos_seleccionados.append('C')
if incluir_d: grupos_seleccionados.append('D')

if not grupos_seleccionados:
    st.sidebar.error("Selecciona al menos un grupo")
    grupos_seleccionados = ['A', 'B', 'C']

# Mostrar configuracion actual
grupos_texto = ' + '.join([f"Grupo {g}" for g in grupos_seleccionados])
st.sidebar.markdown(f"""
<div class="filter-info">
<strong>Ranking basado en:</strong><br>
{grupos_texto}
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros adicionales")

# Filtro por localidad
localidades = ['Todas las localidades'] + sorted(df['LOCALIDAD'].dropna().unique().tolist())
localidad_sel = st.sidebar.selectbox("Localidad", localidades)

# Calcular ranking dinamico
df_dinamico = calcular_ranking_dinamico(df, grupos_seleccionados)

# Filtro por rango de ranking
st.sidebar.markdown("### Rango de Priorizacion")
ranking_min, ranking_max = st.sidebar.slider(
    "Seleccionar rango",
    min_value=1,
    max_value=len(df_dinamico),
    value=(1, min(50, len(df_dinamico))),
    label_visibility="collapsed"
)

# Aplicar filtros
df_filtrado = df_dinamico.copy()

if localidad_sel != 'Todas las localidades':
    df_filtrado = df_filtrado[df_filtrado['LOCALIDAD'] == localidad_sel]

df_filtrado = df_filtrado[
    (df_filtrado['RANKING_DINAMICO'] >= ranking_min) &
    (df_filtrado['RANKING_DINAMICO'] <= ranking_max)
]

# Calcular totales
total_seleccionado = df_filtrado['POB_SELECCIONADA'].sum()
total_jovenes = df_filtrado['JOVENES_TOTAL'].sum()
total_hombres_sel = df_filtrado['HOMBRES_SEL'].sum()
total_mujeres_sel = df_filtrado['MUJERES_SEL'].sum()

# ============================================
# METRICAS PRINCIPALES
# ============================================
st.markdown("### Resumen General")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("UPZ", len(df_filtrado))
with col2:
    st.metric("Total Jovenes", f"{total_jovenes:,}")
with col3:
    st.metric(f"Grupos {'+'.join(grupos_seleccionados)}", f"{total_seleccionado:,}")
with col4:
    pct = (total_seleccionado / total_jovenes * 100) if total_jovenes > 0 else 0
    st.metric("% Seleccionado", f"{pct:.1f}%")
with col5:
    st.metric("Hombres", f"{total_hombres_sel:,}")
with col6:
    st.metric("Mujeres", f"{total_mujeres_sel:,}")

st.markdown("---")

# ============================================
# TABS PRINCIPALES
# ============================================
tab1, tab2 = st.tabs(["Mapa Interactivo", "Localidades"])

# ============================================
# TAB 1: MAPA INTERACTIVO
# ============================================
with tab1:
    st.markdown("### Mapa de Priorizacion por UPZ")
    st.markdown(f"**Coloreado por:** Poblacion de Grupos {'+'.join(grupos_seleccionados)}")

    # Crear GeoJSON
    if gdf is not None:
        geojson_data = crear_geojson_desde_shapefile(gdf, df_filtrado)
        st.success("Usando shapefile con geometrias completas")
    elif geo_excel is not None:
        geojson_data = crear_geojson_desde_excel(geo_excel, df_filtrado)
        st.info("Usando geodatos desde Excel")
    else:
        st.error("No hay datos geograficos disponibles")
        geojson_data = None

    if geojson_data and len(geojson_data['features']) > 0:
        # Preparar datos para mapa
        map_df = df_filtrado[['CODIGO_UPZ', 'UPZ', 'LOCALIDAD', 'POB_SELECCIONADA',
                              'JOVENES_TOTAL', 'RANKING_DINAMICO', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D']].copy()
        map_df['CODIGO_UPZ'] = map_df['CODIGO_UPZ'].astype(str)

        # Zoom segun filtro
        zoom_level = 11.5 if localidad_sel != 'Todas las localidades' else 10

        # Mapa coropletico
        fig_map = px.choropleth_mapbox(
            map_df,
            geojson=geojson_data,
            locations='CODIGO_UPZ',
            featureidkey="id",
            color='POB_SELECCIONADA',
            color_continuous_scale=[
                [0, '#ffffcc'], [0.2, '#ffeda0'], [0.4, '#fed976'],
                [0.5, '#feb24c'], [0.6, '#fd8d3c'], [0.7, '#fc4e2a'],
                [0.8, '#e31a1c'], [0.9, '#bd0026'], [1, '#800026']
            ],
            range_color=[0, df_filtrado['POB_SELECCIONADA'].max()],
            hover_name='UPZ',
            hover_data={
                'CODIGO_UPZ': False,
                'LOCALIDAD': True,
                'RANKING_DINAMICO': True,
                'POB_SELECCIONADA': ':,',
                'JOVENES_TOTAL': ':,',
                'GRUPO_A': ':,',
                'GRUPO_B': ':,',
                'GRUPO_C': ':,',
                'GRUPO_D': ':,'
            },
            labels={
                'POB_SELECCIONADA': f'Grupos {"+".join(grupos_seleccionados)}',
                'JOVENES_TOTAL': 'Total Jovenes',
                'LOCALIDAD': 'Localidad',
                'RANKING_DINAMICO': 'Ranking',
                'GRUPO_A': 'Grupo A',
                'GRUPO_B': 'Grupo B',
                'GRUPO_C': 'Grupo C',
                'GRUPO_D': 'Grupo D'
            },
            mapbox_style="carto-positron",
            center={"lat": 4.65, "lon": -74.1},
            zoom=zoom_level,
            opacity=0.7
        )

        fig_map.update_traces(marker_line_width=1, marker_line_color='white')
        fig_map.update_layout(
            height=650,
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title=f"Grupos<br>{'+'.join(grupos_seleccionados)}",
                tickformat=",",
                len=0.7,
                thickness=15,
                x=0.98
            )
        )

        st.plotly_chart(fig_map, width='stretch')

    # Panel informativo
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"#### Top 10 UPZ (Grupos {'+'.join(grupos_seleccionados)})")
        top10 = df_filtrado.head(10)[['RANKING_DINAMICO', 'UPZ', 'LOCALIDAD', 'POB_SELECCIONADA', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D']]
        top10.columns = ['Rank', 'UPZ', 'Localidad', 'Poblacion', 'A', 'B', 'C', 'D']
        st.dataframe(
            top10.style.format({
                'Poblacion': '{:,.0f}', 'A': '{:,.0f}', 'B': '{:,.0f}', 'C': '{:,.0f}', 'D': '{:,.0f}'
            }).background_gradient(subset=['Poblacion'], cmap='YlOrRd'),
            width='stretch',
            hide_index=True
        )

    with col2:
        st.markdown("#### Leyenda de Grupos SISBEN")
        st.markdown("""
        | Grupo | Descripcion | Incluido |
        |-------|------------|----------|
        | **A** | Pobreza Extrema | {} |
        | **B** | Pobreza Moderada | {} |
        | **C** | Vulnerable | {} |
        | **D** | No Vulnerable | {} |
        """.format(
            "Si" if 'A' in grupos_seleccionados else "No",
            "Si" if 'B' in grupos_seleccionados else "No",
            "Si" if 'C' in grupos_seleccionados else "No",
            "Si" if 'D' in grupos_seleccionados else "No"
        ))

        st.markdown("""
        **Instrucciones:**
        - Usa los checkboxes en la barra lateral para cambiar los grupos
        - El ranking se recalcula automaticamente
        - El mapa se actualiza con los nuevos valores
        """)

# ============================================
# TAB 2: LOCALIDADES
# ============================================
with tab2:
    st.markdown("### Analisis por Localidad")
    st.markdown(f"**Ranking basado en:** Grupos {'+'.join(grupos_seleccionados)}")

    # Agrupar por localidad
    por_loc = df_filtrado.groupby('LOCALIDAD').agg({
        'UPZ': 'count',
        'POB_SELECCIONADA': 'sum',
        'JOVENES_TOTAL': 'sum',
        'GRUPO_A': 'sum',
        'GRUPO_B': 'sum',
        'GRUPO_C': 'sum',
        'GRUPO_D': 'sum',
        'HOMBRES_SEL': 'sum',
        'MUJERES_SEL': 'sum'
    }).reset_index()
    por_loc = por_loc.sort_values('POB_SELECCIONADA', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_loc = px.bar(
            por_loc,
            y='LOCALIDAD',
            x='POB_SELECCIONADA',
            orientation='h',
            color='POB_SELECCIONADA',
            color_continuous_scale='YlOrRd',
            title=f'Poblacion Grupos {"+".join(grupos_seleccionados)} por Localidad',
            text='POB_SELECCIONADA'
        )
        fig_loc.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_loc.update_layout(height=600, yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_loc, width='stretch')

    with col2:
        tabla_loc = por_loc[['LOCALIDAD', 'UPZ', 'POB_SELECCIONADA', 'JOVENES_TOTAL', 'HOMBRES_SEL', 'MUJERES_SEL']].copy()
        tabla_loc.columns = ['Localidad', 'UPZ', f'Grupos {"+".join(grupos_seleccionados)}', 'Total', 'Hombres', 'Mujeres']

        st.markdown("#### Resumen por Localidad")
        st.dataframe(
            tabla_loc.style.format({
                f'Grupos {"+".join(grupos_seleccionados)}': '{:,.0f}',
                'Total': '{:,.0f}',
                'Hombres': '{:,.0f}',
                'Mujeres': '{:,.0f}'
            }).background_gradient(subset=[f'Grupos {"+".join(grupos_seleccionados)}'], cmap='YlOrRd'),
            width='stretch',
            height=550
        )

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>Fuente:</strong> Base de datos SISBEN IV |
    <strong>Elaborado por:</strong> Subdireccion para la Juventud - Secretaria de Integracion Social<br>
    <small>Tablero de exploracion - Jovenes con Oportunidades (JCO) | Version 2.0 con ranking dinamico</small>
</div>
""", unsafe_allow_html=True)
