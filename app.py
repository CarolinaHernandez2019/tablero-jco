# -*- coding: utf-8 -*-
"""
Tablero JCO - Explorador de Priorizacion Territorial
Jovenes con Oportunidades - SDIS

Version 3.0 - Con ranking dinamico por grupos SISBEN + analisis de brechas
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
BRECHAS_FILE = os.path.join(SCRIPT_DIR, 'brechas_por_upz.csv')

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
    /* Fondo claro + texto oscuro forzado para que se lea en modo oscuro (celular) */
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .stMetric label,
    .stMetric [data-testid="stMetricLabel"],
    .stMetric [data-testid="stMetricValue"],
    .stMetric [data-testid="stMetricDelta"] {
        color: #1a1a2e !important;
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

@st.cache_data
def cargar_brechas():
    """Carga los datos pre-calculados de brechas por UPZ (beneficiarios ruta corta vs vulnerables SISBEN)"""
    try:
        df = pd.read_csv(BRECHAS_FILE)
        return df
    except Exception as e:
        st.warning(f"No se pudo cargar datos de brechas: {e}")
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

@st.cache_data
def crear_limites_localidades(_gdf, df_datos):
    """Crear GeoJSON con los contornos de localidades, agrupando UPZ por localidad"""
    try:
        # Se cruza el shapefile de UPZ con los datos para obtener la localidad de cada UPZ
        merged = _gdf.merge(
            df_datos[['CODIGO_UPZ', 'LOCALIDAD']].drop_duplicates(),
            on='CODIGO_UPZ', how='inner'
        )
        # Se disuelven (unen) las geometrias de UPZ que pertenecen a la misma localidad
        localidades = merged.dissolve(by='LOCALIDAD').reset_index()
        # Se convierte a GeoJSON para usarlo como capa en el mapa
        return json.loads(localidades[['LOCALIDAD', 'geometry']].to_json())
    except Exception:
        return None

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
df_brechas = cargar_brechas()

# Header principal
st.markdown('<h1 class="main-header">Tablero de priorizacion con datos del SISBEN</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Secretaria Distrital de Integracion Social - SDIS | Datos SISBEN IV</p>', unsafe_allow_html=True)

# ============================================
# SIDEBAR - FILTROS DINAMICOS
# ============================================
st.sidebar.markdown("### Grupos SISBEN")
with st.sidebar.expander("Que es el SISBEN?"):
    st.markdown("""
El Sistema de Identificacion de Potenciales Beneficiarios
de Programas Sociales es conocido por su sigla **SISBEN**.
Existen cuatro grupos de clasificacion: **A, B, C y D**.
Cada uno ubica a las personas segun su capacidad para
generar ingresos y sus condiciones de vida:

- **Grupo A**: poblacion con pobreza extrema
- **Grupo B**: poblacion con pobreza moderada
- **Grupo C**: poblacion vulnerable
- **Grupo D**: poblacion no pobre, no vulnerable
""")
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
tab1, tab2, tab3, tab4 = st.tabs(["Mapa interactivo", "Localidades", "Brechas por UPZ", "Zonas calientes"])

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

        # Agregar contornos de localidades como capa sobre el mapa
        capas_localidades = []
        if gdf is not None:
            limites_loc = crear_limites_localidades(gdf, df)
            if limites_loc:
                capas_localidades = [{
                    "source": limites_loc,
                    "type": "line",
                    "color": "rgba(0, 0, 0, 0.6)",
                    "line": {"width": 2}
                }]

        fig_map.update_layout(
            height=650,
            margin=dict(l=0, r=0, t=0, b=0),
            mapbox=dict(layers=capas_localidades),
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
        st.markdown(f"#### Ranking UPZ (Grupos {'+'.join(grupos_seleccionados)})")
        tabla_upz = df_filtrado[['RANKING_DINAMICO', 'UPZ', 'LOCALIDAD', 'POB_SELECCIONADA', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D']].copy()
        tabla_upz.columns = ['Rank', 'UPZ', 'Localidad', 'Poblacion', 'A', 'B', 'C', 'D']
        st.dataframe(
            tabla_upz.style.format({
                'Poblacion': '{:,.0f}', 'A': '{:,.0f}', 'B': '{:,.0f}', 'C': '{:,.0f}', 'D': '{:,.0f}'
            }).background_gradient(subset=['Poblacion'], cmap='YlOrRd'),
            width='stretch',
            hide_index=True,
            height=500
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
# TAB 3: BRECHAS POR UPZ
# ============================================
with tab3:
    st.markdown("### Analisis de brechas de cobertura")
    st.markdown("""
    Compara el total de jovenes vulnerables (SISBEN) contra los beneficiarios
    de la ruta corta JCO en cada UPZ. La brecha indica cuantos jovenes vulnerables
    aun no estan siendo atendidos.
    """)

    if df_brechas is not None:
        # Recalcular brechas segun grupos seleccionados
        df_brecha_dinamica = df_brechas.copy()

        # Sumar solo los grupos seleccionados como referencia de vulnerables
        col_grupos_brecha = [f'GRUPO_{g}' for g in grupos_seleccionados]
        cols_disponibles_brecha = [c for c in col_grupos_brecha if c in df_brecha_dinamica.columns]

        if cols_disponibles_brecha:
            df_brecha_dinamica['VULNERABLES_SEL'] = df_brecha_dinamica[cols_disponibles_brecha].sum(axis=1)
        else:
            df_brecha_dinamica['VULNERABLES_SEL'] = df_brecha_dinamica['JOVENES_TOTAL']

        # Recalcular cobertura y brecha con los grupos seleccionados
        df_brecha_dinamica['TASA_COB_DIN'] = (
            df_brecha_dinamica['BENEFICIARIOS_RUTA_CORTA'] / df_brecha_dinamica['VULNERABLES_SEL'] * 100
        ).round(1)
        # Evitar division por cero
        df_brecha_dinamica.loc[df_brecha_dinamica['VULNERABLES_SEL'] == 0, 'TASA_COB_DIN'] = 0

        df_brecha_dinamica['BRECHA_DIN'] = (
            df_brecha_dinamica['VULNERABLES_SEL'] - df_brecha_dinamica['BENEFICIARIOS_RUTA_CORTA']
        )

        # Clasificar prioridad
        def clasificar(tasa):
            if tasa >= 100:
                return 'Cobertura completa'
            elif tasa >= 75:
                return 'Baja'
            elif tasa >= 50:
                return 'Media'
            elif tasa >= 25:
                return 'Alta'
            else:
                return 'Critica'

        df_brecha_dinamica['PRIORIDAD'] = df_brecha_dinamica['TASA_COB_DIN'].apply(clasificar)

        # Aplicar filtro de localidad
        df_brecha_vista = df_brecha_dinamica.copy()
        if localidad_sel != 'Todas las localidades':
            df_brecha_vista = df_brecha_vista[df_brecha_vista['LOCALIDAD'] == localidad_sel]

        df_brecha_vista = df_brecha_vista.sort_values('BRECHA_DIN', ascending=False)

        # Metricas de brechas
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        total_vuln = df_brecha_vista['VULNERABLES_SEL'].sum()
        total_benef = df_brecha_vista['BENEFICIARIOS_RUTA_CORTA'].sum()
        total_brecha = df_brecha_vista['BRECHA_DIN'].sum()
        cobertura_gral = (total_benef / total_vuln * 100) if total_vuln > 0 else 0

        with col_b1:
            st.metric(f"Vulnerables ({'+'.join(grupos_seleccionados)})", f"{total_vuln:,}")
        with col_b2:
            st.metric("Beneficiarios ruta corta", f"{total_benef:,}")
        with col_b3:
            st.metric("Cobertura", f"{cobertura_gral:.1f}%")
        with col_b4:
            st.metric("Brecha", f"{total_brecha:,}")

        st.markdown("---")

        # Distribucion por prioridad
        col_p1, col_p2 = st.columns([1, 2])

        with col_p1:
            st.markdown("#### UPZ por nivel de prioridad")
            prioridad_conteo = df_brecha_vista['PRIORIDAD'].value_counts()
            # Colores por prioridad
            colores_prioridad = {
                'Critica': '#d73027',
                'Alta': '#fc8d59',
                'Media': '#fee08b',
                'Baja': '#91cf60',
                'Cobertura completa': '#1a9850'
            }
            orden_prioridad = ['Critica', 'Alta', 'Media', 'Baja', 'Cobertura completa']
            for p in orden_prioridad:
                if p in prioridad_conteo.index:
                    color = colores_prioridad[p]
                    n = prioridad_conteo[p]
                    st.markdown(
                        f'<span style="background-color:{color}; color:{"white" if p in ["Critica","Alta"] else "black"}; '
                        f'padding:0.3rem 0.6rem; border-radius:5px; font-weight:bold;">'
                        f'{p}: {n} UPZ</span>', unsafe_allow_html=True
                    )
                    st.markdown("")

        with col_p2:
            # Grafico de barras: brecha por UPZ (top 20)
            top_brechas = df_brecha_vista.head(20)
            fig_brecha = px.bar(
                top_brechas,
                y='UPZ',
                x='BRECHA_DIN',
                orientation='h',
                color='PRIORIDAD',
                color_discrete_map=colores_prioridad,
                category_orders={'PRIORIDAD': orden_prioridad},
                title='Top 20 UPZ con mayor brecha absoluta',
                text='BRECHA_DIN',
                hover_data={'LOCALIDAD': True, 'VULNERABLES_SEL': ':,', 'BENEFICIARIOS_RUTA_CORTA': ':,', 'TASA_COB_DIN': True}
            )
            fig_brecha.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_brecha.update_layout(
                height=550,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='Brecha absoluta (jovenes sin atender)',
                yaxis_title='',
                legend_title='Prioridad'
            )
            st.plotly_chart(fig_brecha, use_container_width=True)

        # Tabla completa de brechas
        st.markdown("#### Tabla completa de brechas")
        tabla_brechas = df_brecha_vista[[
            'UPZ', 'LOCALIDAD', 'VULNERABLES_SEL', 'BENEFICIARIOS_RUTA_CORTA',
            'TASA_COB_DIN', 'BRECHA_DIN', 'PRIORIDAD'
        ]].copy()
        tabla_brechas.columns = [
            'UPZ', 'Localidad', f'Vulnerables ({"+".join(grupos_seleccionados)})',
            'Beneficiarios', 'Cobertura %', 'Brecha', 'Prioridad'
        ]

        # Aplicar colores de prioridad
        def color_prioridad(val):
            colores = {
                'Critica': 'background-color: #d73027; color: white',
                'Alta': 'background-color: #fc8d59; color: white',
                'Media': 'background-color: #fee08b; color: black',
                'Baja': 'background-color: #91cf60; color: black',
                'Cobertura completa': 'background-color: #1a9850; color: white'
            }
            return colores.get(val, '')

        st.dataframe(
            tabla_brechas.style.format({
                f'Vulnerables ({"+".join(grupos_seleccionados)})': '{:,.0f}',
                'Beneficiarios': '{:,.0f}',
                'Cobertura %': '{:.1f}%',
                'Brecha': '{:,.0f}'
            }).map(color_prioridad, subset=['Prioridad']),
            use_container_width=True,
            hide_index=True,
            height=500
        )
    else:
        st.warning("No se encontro el archivo de brechas (brechas_por_upz.csv)")

# ============================================
# TAB 4: ZONAS CALIENTES
# ============================================
with tab4:
    st.markdown("### Mapa de zonas calientes")
    st.markdown("""
    Mapa que combina dos dimensiones: el **color** muestra la brecha absoluta
    (jovenes vulnerables sin atender) y los **contornos** delimitan las localidades.
    Las zonas mas oscuras son las que requieren mayor atencion.
    """)

    if df_brechas is not None and (gdf is not None or geo_excel is not None):
        # Recalcular con grupos seleccionados (misma logica que tab3)
        df_calor = df_brechas.copy()
        col_grupos_calor = [f'GRUPO_{g}' for g in grupos_seleccionados]
        cols_disp_calor = [c for c in col_grupos_calor if c in df_calor.columns]

        if cols_disp_calor:
            df_calor['VULNERABLES_SEL'] = df_calor[cols_disp_calor].sum(axis=1)
        else:
            df_calor['VULNERABLES_SEL'] = df_calor['JOVENES_TOTAL']

        df_calor['TASA_COB_DIN'] = (
            df_calor['BENEFICIARIOS_RUTA_CORTA'] / df_calor['VULNERABLES_SEL'] * 100
        ).round(1)
        df_calor.loc[df_calor['VULNERABLES_SEL'] == 0, 'TASA_COB_DIN'] = 0
        df_calor['BRECHA_DIN'] = df_calor['VULNERABLES_SEL'] - df_calor['BENEFICIARIOS_RUTA_CORTA']

        # Filtro de localidad
        if localidad_sel != 'Todas las localidades':
            df_calor = df_calor[df_calor['LOCALIDAD'] == localidad_sel]

        # Selector de variable para el mapa
        variable_mapa = st.radio(
            "Colorear el mapa por:",
            ["Brecha absoluta", "Tasa de cobertura (%)"],
            horizontal=True
        )

        if variable_mapa == "Brecha absoluta":
            color_col = 'BRECHA_DIN'
            color_label = 'Brecha'
            # Escala de rojos: mas rojo = mayor brecha
            escala_colores = [
                [0, '#ffffb2'], [0.2, '#fecc5c'], [0.4, '#fd8d3c'],
                [0.6, '#f03b20'], [0.8, '#bd0026'], [1, '#67000d']
            ]
            rango = [0, df_calor['BRECHA_DIN'].max()]
        else:
            color_col = 'TASA_COB_DIN'
            color_label = 'Cobertura %'
            # Escala invertida: rojo = baja cobertura, verde = alta cobertura
            escala_colores = [
                [0, '#d73027'], [0.25, '#fc8d59'], [0.5, '#fee08b'],
                [0.75, '#91cf60'], [1, '#1a9850']
            ]
            rango = [0, min(100, df_calor['TASA_COB_DIN'].max())]

        # Crear GeoJSON con datos de brechas
        if gdf is not None:
            geojson_calor = crear_geojson_desde_shapefile(gdf, df_calor)
        else:
            geojson_calor = crear_geojson_desde_excel(geo_excel, df_calor)

        if geojson_calor and len(geojson_calor['features']) > 0:
            # Preparar datos para mapa
            map_calor = df_calor[['CODIGO_UPZ', 'UPZ', 'LOCALIDAD', 'VULNERABLES_SEL',
                                   'BENEFICIARIOS_RUTA_CORTA', 'TASA_COB_DIN', 'BRECHA_DIN']].copy()
            map_calor['CODIGO_UPZ'] = map_calor['CODIGO_UPZ'].astype(str)

            zoom_calor = 11.5 if localidad_sel != 'Todas las localidades' else 10

            fig_calor = px.choropleth_mapbox(
                map_calor,
                geojson=geojson_calor,
                locations='CODIGO_UPZ',
                featureidkey="id",
                color=color_col,
                color_continuous_scale=escala_colores,
                range_color=rango,
                hover_name='UPZ',
                hover_data={
                    'CODIGO_UPZ': False,
                    'LOCALIDAD': True,
                    'VULNERABLES_SEL': ':,',
                    'BENEFICIARIOS_RUTA_CORTA': ':,',
                    'TASA_COB_DIN': True,
                    'BRECHA_DIN': ':,'
                },
                labels={
                    'VULNERABLES_SEL': f'Vulnerables ({"+".join(grupos_seleccionados)})',
                    'BENEFICIARIOS_RUTA_CORTA': 'Beneficiarios',
                    'TASA_COB_DIN': 'Cobertura %',
                    'BRECHA_DIN': 'Brecha',
                    'LOCALIDAD': 'Localidad'
                },
                mapbox_style="carto-positron",
                center={"lat": 4.65, "lon": -74.1},
                zoom=zoom_calor,
                opacity=0.8
            )

            fig_calor.update_traces(marker_line_width=1.5, marker_line_color='white')

            # Contornos de localidades
            capas_loc_calor = []
            if gdf is not None:
                limites_calor = crear_limites_localidades(gdf, df)
                if limites_calor:
                    capas_loc_calor = [{
                        "source": limites_calor,
                        "type": "line",
                        "color": "rgba(0, 0, 0, 0.7)",
                        "line": {"width": 2.5}
                    }]

            fig_calor.update_layout(
                height=700,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(layers=capas_loc_calor),
                coloraxis_colorbar=dict(
                    title=color_label,
                    tickformat="," if variable_mapa == "Brecha absoluta" else "",
                    len=0.7,
                    thickness=15,
                    x=0.98
                )
            )

            st.plotly_chart(fig_calor, use_container_width=True)

        # Resumen por localidad en zonas calientes
        st.markdown("#### Brechas agregadas por localidad")
        loc_calor = df_calor.groupby('LOCALIDAD').agg({
            'VULNERABLES_SEL': 'sum',
            'BENEFICIARIOS_RUTA_CORTA': 'sum',
            'BRECHA_DIN': 'sum'
        }).reset_index()
        loc_calor['COBERTURA'] = (loc_calor['BENEFICIARIOS_RUTA_CORTA'] / loc_calor['VULNERABLES_SEL'] * 100).round(1)
        loc_calor = loc_calor.sort_values('BRECHA_DIN', ascending=False)

        col_z1, col_z2 = st.columns(2)

        with col_z1:
            fig_loc_brecha = px.bar(
                loc_calor,
                y='LOCALIDAD',
                x='BRECHA_DIN',
                orientation='h',
                color='COBERTURA',
                color_continuous_scale=[[0, '#d73027'], [0.5, '#fee08b'], [1, '#1a9850']],
                title='Brecha por localidad (color = cobertura %)',
                text='BRECHA_DIN'
            )
            fig_loc_brecha.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_loc_brecha.update_layout(
                height=550,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='Brecha absoluta',
                yaxis_title=''
            )
            st.plotly_chart(fig_loc_brecha, use_container_width=True)

        with col_z2:
            loc_calor_tabla = loc_calor.copy()
            loc_calor_tabla.columns = ['Localidad', f'Vulnerables ({"+".join(grupos_seleccionados)})',
                                        'Beneficiarios', 'Brecha', 'Cobertura %']
            st.markdown("#### Resumen por localidad")
            st.dataframe(
                loc_calor_tabla.style.format({
                    f'Vulnerables ({"+".join(grupos_seleccionados)})': '{:,.0f}',
                    'Beneficiarios': '{:,.0f}',
                    'Brecha': '{:,.0f}',
                    'Cobertura %': '{:.1f}%'
                }).background_gradient(subset=['Brecha'], cmap='YlOrRd'),
                use_container_width=True,
                hide_index=True,
                height=550
            )
    else:
        st.warning("Se necesitan los datos de brechas y geodatos para este mapa")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>Fuente:</strong> Base de datos SISBEN IV |
    <strong>Elaborado por:</strong> Subdireccion para la Juventud - Secretaria Distrital de Integracion Social - SDIS<br>

</div>
""", unsafe_allow_html=True)
