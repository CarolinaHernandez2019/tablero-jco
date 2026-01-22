# -*- coding: utf-8 -*-
"""
Tablero JCO - Explorador de Priorización Territorial
Jóvenes con Oportunidades - SDIS
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# Configuración de página
st.set_page_config(
    page_title="Tablero JCO - Priorización",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor diseño
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
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Cargar datos
@st.cache_data
def cargar_datos():
    df = pd.read_excel('Tabla_Completa_Priorizacion_JCO.xlsx')
    return df

@st.cache_data
def cargar_geodatos():
    geo = pd.read_excel('upz-bogota-para-shape-con-resultad.xlsx')
    return geo

@st.cache_data
def crear_geojson(geo_df, df_datos):
    """Crear GeoJSON con datos para el mapa coropletas"""
    features = []

    merged = geo_df.merge(
        df_datos[['CODIGO_UPZ', 'UPZ', 'JOVENES_VULNERABLES', 'JOVENES_TOTAL',
                  'RANKING', 'LOCALIDAD', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D',
                  'HOMBRES_A', 'HOMBRES_B', 'HOMBRES_C', 'HOMBRES_D',
                  'MUJERES_A', 'MUJERES_B', 'MUJERES_C', 'MUJERES_D']],
        on='CODIGO_UPZ', how='inner'
    )

    for _, row in merged.iterrows():
        try:
            geo_shape = json.loads(row['geo_shape'])
            feature = {
                "type": "Feature",
                "id": str(row['CODIGO_UPZ']),
                "properties": {
                    "CODIGO_UPZ": int(row['CODIGO_UPZ']),
                    "UPZ": row['UPZ'],
                    "LOCALIDAD": row['LOCALIDAD'] if pd.notna(row['LOCALIDAD']) else "Sin datos",
                    "RANKING": int(row['RANKING']),
                    "JOVENES_VULNERABLES": int(row['JOVENES_VULNERABLES']),
                    "JOVENES_TOTAL": int(row['JOVENES_TOTAL']),
                    "GRUPO_A": int(row['GRUPO_A']),
                    "GRUPO_B": int(row['GRUPO_B']),
                    "GRUPO_C": int(row['GRUPO_C']),
                    "GRUPO_D": int(row['GRUPO_D']),
                    "HOMBRES": int(row['HOMBRES_A'] + row['HOMBRES_B'] + row['HOMBRES_C'] + row['HOMBRES_D']),
                    "MUJERES": int(row['MUJERES_A'] + row['MUJERES_B'] + row['MUJERES_C'] + row['MUJERES_D'])
                },
                "geometry": geo_shape
            }
            features.append(feature)
        except:
            continue

    return {"type": "FeatureCollection", "features": features}

# Mapeo de códigos de localidad
LOCALIDADES_MAP = {
    1: 'Usaquen', 2: 'Chapinero', 3: 'Santa Fe', 4: 'San Cristobal',
    5: 'Usme', 6: 'Tunjuelito', 7: 'Bosa', 8: 'Kennedy',
    9: 'Fontibon', 10: 'Engativa', 11: 'Suba', 12: 'Barrios Unidos',
    13: 'Teusaquillo', 14: 'Los Martires', 15: 'Antonio Narino',
    16: 'Puente Aranda', 17: 'La Candelaria', 18: 'Rafael Uribe Uribe',
    19: 'Ciudad Bolivar', 20: 'Sumapaz'
}

@st.cache_data
def obtener_limites_localidades(geo_df):
    """Obtener los límites y centroides de cada localidad para mostrar en el mapa"""
    from shapely.geometry import shape
    from shapely.ops import unary_union

    localidades_info = []
    geo_df_copy = geo_df.copy()
    geo_df_copy['LOCALIDAD'] = geo_df_copy['CODIGO_LOCALIDAD'].map(LOCALIDADES_MAP)

    for cod_loc, nombre_loc in LOCALIDADES_MAP.items():
        upz_localidad = geo_df_copy[geo_df_copy['CODIGO_LOCALIDAD'] == cod_loc]

        if len(upz_localidad) == 0:
            continue

        polygons = []
        for _, row in upz_localidad.iterrows():
            try:
                geo_shape = json.loads(row['geo_shape'])
                polygons.append(shape(geo_shape))
            except:
                continue

        if polygons:
            try:
                merged_polygon = unary_union(polygons)
                centroid = merged_polygon.centroid

                # Extraer coordenadas del borde
                if merged_polygon.geom_type == 'Polygon':
                    coords = list(merged_polygon.exterior.coords)
                elif merged_polygon.geom_type == 'MultiPolygon':
                    # Tomar el polígono más grande
                    largest = max(merged_polygon.geoms, key=lambda p: p.area)
                    coords = list(largest.exterior.coords)
                else:
                    continue

                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]

                localidades_info.append({
                    'nombre': nombre_loc,
                    'codigo': cod_loc,
                    'centroid_lat': centroid.y,
                    'centroid_lon': centroid.x,
                    'border_lats': lats + [None],  # None para separar líneas
                    'border_lons': lons + [None]
                })
            except:
                continue

    return localidades_info

df = cargar_datos()
geo_df = cargar_geodatos()

# Header principal
st.markdown('<h1 class="main-header">🎯 Tablero de Priorización JCO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Jóvenes con Oportunidades | Secretaría de Integración Social | Datos SISBEN IV</p>', unsafe_allow_html=True)

# Sidebar - Filtros
st.sidebar.markdown("## 🔍 Filtros")

# Filtro por localidad
localidades = ['Todas las localidades'] + sorted(df['LOCALIDAD'].dropna().unique().tolist())
localidad_sel = st.sidebar.selectbox("📍 Localidad", localidades)

# Filtro por rango de ranking
st.sidebar.markdown("### 📊 Rango de Priorización")
ranking_min, ranking_max = st.sidebar.slider(
    "Seleccionar rango",
    min_value=1,
    max_value=int(df['RANKING'].max()),
    value=(1, int(df['RANKING'].max())),
    label_visibility="collapsed"
)

# Aplicar filtros
df_filtrado = df.copy()

if localidad_sel != 'Todas las localidades':
    df_filtrado = df_filtrado[df_filtrado['LOCALIDAD'] == localidad_sel]

df_filtrado = df_filtrado[
    (df_filtrado['RANKING'] >= ranking_min) &
    (df_filtrado['RANKING'] <= ranking_max)
]

# Calcular totales hombres y mujeres
total_hombres = df_filtrado[['HOMBRES_A', 'HOMBRES_B', 'HOMBRES_C', 'HOMBRES_D']].sum().sum()
total_mujeres = df_filtrado[['MUJERES_A', 'MUJERES_B', 'MUJERES_C', 'MUJERES_D']].sum().sum()
total_hombres_vuln = df_filtrado[['HOMBRES_A', 'HOMBRES_B', 'HOMBRES_C']].sum().sum()
total_mujeres_vuln = df_filtrado[['MUJERES_A', 'MUJERES_B', 'MUJERES_C']].sum().sum()

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
st.markdown("### 📈 Resumen General")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("🏘️ UPZ", len(df_filtrado))
with col2:
    st.metric("👥 Total Jóvenes", f"{df_filtrado['JOVENES_TOTAL'].sum():,}")
with col3:
    st.metric("⚠️ Vulnerables", f"{df_filtrado['JOVENES_VULNERABLES'].sum():,}")
with col4:
    pct = (df_filtrado['JOVENES_VULNERABLES'].sum() / df_filtrado['JOVENES_TOTAL'].sum() * 100) if df_filtrado['JOVENES_TOTAL'].sum() > 0 else 0
    st.metric("📊 % Vulnerable", f"{pct:.1f}%")
with col5:
    st.metric("👨 Hombres", f"{total_hombres:,}")
with col6:
    st.metric("👩 Mujeres", f"{total_mujeres:,}")

st.markdown("---")

# ============================================
# TABS PRINCIPALES
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ Mapa Interactivo", "📋 Tabla", "📊 Categorías SISBEN", "👥 Género", "🏛️ Localidades"])

# ============================================
# TAB 1: MAPA INTERACTIVO
# ============================================
with tab1:
    st.markdown("### 🗺️ Mapa Coropletas de Priorización por UPZ")
    st.markdown("**Interacción:** 🖱️ Zoom con scroll | Arrastrar para mover | Hover en UPZ para ver detalles")

    # Opción para mostrar límites de localidades
    col_opt1, col_opt2 = st.columns([1, 3])
    with col_opt1:
        mostrar_limites = st.checkbox("🗺️ Mostrar límites de localidades", value=True)
    with col_opt2:
        mostrar_nombres = st.checkbox("🏷️ Mostrar nombres de localidades", value=True)

    # Crear GeoJSON
    geojson_data = crear_geojson(geo_df, df_filtrado)

    # Crear dataframe para el mapa
    map_df = df_filtrado[['CODIGO_UPZ', 'UPZ', 'LOCALIDAD', 'JOVENES_VULNERABLES',
                          'JOVENES_TOTAL', 'RANKING', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D']].copy()
    map_df['CODIGO_UPZ'] = map_df['CODIGO_UPZ'].astype(str)

    # Calcular centro del mapa según filtro
    if localidad_sel != 'Todas las localidades':
        zoom_level = 11.5
    else:
        zoom_level = 10

    # Mapa coropletas con Plotly
    fig_map = px.choropleth_mapbox(
        map_df,
        geojson=geojson_data,
        locations='CODIGO_UPZ',
        featureidkey="id",
        color='JOVENES_VULNERABLES',
        color_continuous_scale=[
            [0, '#ffffcc'],
            [0.2, '#ffeda0'],
            [0.4, '#fed976'],
            [0.5, '#feb24c'],
            [0.6, '#fd8d3c'],
            [0.7, '#fc4e2a'],
            [0.8, '#e31a1c'],
            [0.9, '#bd0026'],
            [1, '#800026']
        ],
        range_color=[0, df_filtrado['JOVENES_VULNERABLES'].max()],
        hover_name='UPZ',
        hover_data={
            'CODIGO_UPZ': False,
            'LOCALIDAD': True,
            'RANKING': True,
            'JOVENES_VULNERABLES': ':,',
            'JOVENES_TOTAL': ':,',
            'GRUPO_A': ':,',
            'GRUPO_B': ':,',
            'GRUPO_C': ':,',
            'GRUPO_D': ':,'
        },
        labels={
            'JOVENES_VULNERABLES': 'Jóvenes Vulnerables',
            'JOVENES_TOTAL': 'Total Jóvenes',
            'LOCALIDAD': 'Localidad',
            'RANKING': 'Ranking',
            'GRUPO_A': 'Grupo A (Extrema)',
            'GRUPO_B': 'Grupo B (Moderada)',
            'GRUPO_C': 'Grupo C (Vulnerable)',
            'GRUPO_D': 'Grupo D (No vulnerable)'
        },
        mapbox_style="carto-positron",
        center={"lat": 4.65, "lon": -74.1},
        zoom=zoom_level,
        opacity=0.7
    )

    # Agregar contornos de UPZ
    fig_map.update_traces(
        marker_line_width=1,
        marker_line_color='white'
    )

    # Agregar límites de localidades
    if mostrar_limites or mostrar_nombres:
        localidades_info = obtener_limites_localidades(geo_df)

        if mostrar_limites:
            # Agregar bordes de localidades
            for loc_info in localidades_info:
                fig_map.add_trace(go.Scattermapbox(
                    lat=loc_info['border_lats'],
                    lon=loc_info['border_lons'],
                    mode='lines',
                    line=dict(width=3, color='#2c3e50'),
                    name=loc_info['nombre'],
                    hoverinfo='name',
                    showlegend=False
                ))

        if mostrar_nombres:
            # Agregar etiquetas de localidades
            labels_lat = [loc['centroid_lat'] for loc in localidades_info]
            labels_lon = [loc['centroid_lon'] for loc in localidades_info]
            labels_text = [loc['nombre'] for loc in localidades_info]

            fig_map.add_trace(go.Scattermapbox(
                lat=labels_lat,
                lon=labels_lon,
                mode='text',
                text=labels_text,
                textfont=dict(size=11, color='#2c3e50', family='Arial Black'),
                hoverinfo='text',
                showlegend=False
            ))

    fig_map.update_layout(
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="Jóvenes<br>Vulnerables",
            tickformat=",",
            len=0.7,
            thickness=15,
            x=0.98
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)

    # Panel de información debajo del mapa
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 🏆 Top 10 UPZ Prioritarias")
        top10 = df_filtrado.head(10)[['RANKING', 'UPZ', 'LOCALIDAD', 'JOVENES_VULNERABLES', 'GRUPO_A', 'GRUPO_B', 'GRUPO_C']]
        st.dataframe(
            top10.style.format({
                'JOVENES_VULNERABLES': '{:,.0f}',
                'GRUPO_A': '{:,.0f}',
                'GRUPO_B': '{:,.0f}',
                'GRUPO_C': '{:,.0f}'
            }).background_gradient(subset=['JOVENES_VULNERABLES'], cmap='YlOrRd'),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown("#### 📍 Leyenda e Instrucciones")
        st.markdown("""
        **Escala de colores:**
        - 🟨 **Amarillo claro**: Menos jóvenes vulnerables
        - 🟧 **Naranja**: Prioridad media
        - 🟥 **Rojo oscuro**: Mayor cantidad de jóvenes vulnerables (alta prioridad)

        **Cómo usar el mapa:**
        - **Zoom**: Usa la rueda del mouse o doble click
        - **Mover**: Arrastra con el mouse
        - **Detalles**: Pasa el cursor sobre una UPZ
        - **Resetear vista**: Doble click fuera del mapa

        **Datos mostrados al hacer hover:**
        - Nombre de UPZ y Localidad
        - Ranking de priorización
        - Total de jóvenes vulnerables
        - Desglose por grupo SISBEN
        """)

# ============================================
# TAB 2: TABLA DE DATOS
# ============================================
with tab2:
    st.markdown("### 📋 Tabla de UPZ Priorizadas")

    # Métricas rápidas de género
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👨 Hombres Vulnerables", f"{total_hombres_vuln:,}")
    with col2:
        st.metric("👩 Mujeres Vulnerables", f"{total_mujeres_vuln:,}")
    with col3:
        st.metric("👨 Total Hombres", f"{total_hombres:,}")
    with col4:
        st.metric("👩 Total Mujeres", f"{total_mujeres:,}")

    st.markdown("")

    # Selector de columnas
    cols_disponibles = {
        'Básicas': ['RANKING', 'UPZ', 'LOCALIDAD', 'JOVENES_VULNERABLES', 'JOVENES_TOTAL'],
        'Por Grupo SISBEN': ['GRUPO_A', 'GRUPO_B', 'GRUPO_C', 'GRUPO_D'],
        'Hombres por Grupo': ['HOMBRES_A', 'HOMBRES_B', 'HOMBRES_C', 'HOMBRES_D'],
        'Mujeres por Grupo': ['MUJERES_A', 'MUJERES_B', 'MUJERES_C', 'MUJERES_D']
    }

    grupos_sel = st.multiselect(
        "Seleccionar grupos de columnas",
        options=list(cols_disponibles.keys()),
        default=['Básicas', 'Por Grupo SISBEN']
    )

    cols_mostrar = []
    for grupo in grupos_sel:
        cols_mostrar.extend(cols_disponibles[grupo])

    if cols_mostrar:
        st.dataframe(
            df_filtrado[cols_mostrar].style.format({
                col: '{:,.0f}' for col in cols_mostrar if col not in ['RANKING', 'UPZ', 'LOCALIDAD', 'CODIGO_UPZ']
            }).background_gradient(subset=['JOVENES_VULNERABLES'] if 'JOVENES_VULNERABLES' in cols_mostrar else [], cmap='YlOrRd'),
            use_container_width=True,
            height=500
        )

    # Botón de descarga
    col1, col2 = st.columns([1, 4])
    with col1:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="datos_jco_filtrados.csv",
            mime="text/csv"
        )

# ============================================
# TAB 3: CATEGORÍAS SISBEN
# ============================================
with tab3:
    st.markdown("### 📊 Distribución por Categoría SISBEN")

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de dona
        totales_cat = {
            'Grupo A<br>Pobreza Extrema': df_filtrado['GRUPO_A'].sum(),
            'Grupo B<br>Pobreza Moderada': df_filtrado['GRUPO_B'].sum(),
            'Grupo C<br>Vulnerable': df_filtrado['GRUPO_C'].sum(),
            'Grupo D<br>No Vulnerable': df_filtrado['GRUPO_D'].sum()
        }

        fig_dona = go.Figure(data=[go.Pie(
            labels=list(totales_cat.keys()),
            values=list(totales_cat.values()),
            hole=0.5,
            marker_colors=['#d73027', '#fc8d59', '#fee08b', '#91cf60'],
            textinfo='percent+value',
            texttemplate='%{percent:.1%}<br>%{value:,}',
            hovertemplate='<b>%{label}</b><br>Jóvenes: %{value:,}<br>Porcentaje: %{percent:.1%}<extra></extra>'
        )])

        fig_dona.update_layout(
            title='Distribución Total por Grupo SISBEN',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2)
        )
        st.plotly_chart(fig_dona, use_container_width=True)

    with col2:
        # Tabla resumen con colores
        resumen = pd.DataFrame({
            'Grupo': ['A', 'B', 'C', 'D'],
            'Descripción': ['Pobreza Extrema', 'Pobreza Moderada', 'Vulnerable', 'No Vulnerable'],
            'Total': [df_filtrado['GRUPO_A'].sum(), df_filtrado['GRUPO_B'].sum(),
                     df_filtrado['GRUPO_C'].sum(), df_filtrado['GRUPO_D'].sum()],
            'Hombres': [df_filtrado['HOMBRES_A'].sum(), df_filtrado['HOMBRES_B'].sum(),
                       df_filtrado['HOMBRES_C'].sum(), df_filtrado['HOMBRES_D'].sum()],
            'Mujeres': [df_filtrado['MUJERES_A'].sum(), df_filtrado['MUJERES_B'].sum(),
                       df_filtrado['MUJERES_C'].sum(), df_filtrado['MUJERES_D'].sum()]
        })
        resumen['% del Total'] = (resumen['Total'] / resumen['Total'].sum() * 100).round(1)

        st.markdown("#### Resumen por Categoría")
        st.dataframe(resumen, use_container_width=True, hide_index=True)

        # Indicador de vulnerabilidad
        total_vuln = resumen[resumen['Grupo'].isin(['A', 'B', 'C'])]['Total'].sum()
        total_general = resumen['Total'].sum()
        pct_vuln = total_vuln / total_general * 100 if total_general > 0 else 0

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #d73027, #fc8d59); padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <h2 style="margin: 0;">{pct_vuln:.1f}%</h2>
            <p style="margin: 0;">de los jóvenes son vulnerables (Grupos A, B, C)</p>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico de barras apiladas por UPZ
    st.markdown("### Top 20 UPZ por Composición SISBEN")

    top20 = df_filtrado.head(20)

    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(name='Grupo A', x=top20['UPZ'], y=top20['GRUPO_A'], marker_color='#d73027'))
    fig_stack.add_trace(go.Bar(name='Grupo B', x=top20['UPZ'], y=top20['GRUPO_B'], marker_color='#fc8d59'))
    fig_stack.add_trace(go.Bar(name='Grupo C', x=top20['UPZ'], y=top20['GRUPO_C'], marker_color='#fee08b'))
    fig_stack.add_trace(go.Bar(name='Grupo D', x=top20['UPZ'], y=top20['GRUPO_D'], marker_color='#91cf60'))

    fig_stack.update_layout(
        barmode='stack',
        xaxis_tickangle=-45,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Número de Jóvenes"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# ============================================
# TAB 4: GÉNERO
# ============================================
with tab4:
    st.markdown("### 👥 Análisis por Género")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Dona género total
        fig_gen = go.Figure(data=[go.Pie(
            labels=['Hombres', 'Mujeres'],
            values=[total_hombres, total_mujeres],
            hole=0.6,
            marker_colors=['#3288bd', '#d53e4f'],
            textinfo='percent+value',
            texttemplate='%{percent:.1%}<br>%{value:,}'
        )])
        fig_gen.update_layout(title='Total por Género', height=350, showlegend=True)
        st.plotly_chart(fig_gen, use_container_width=True)

    with col2:
        # Dona género vulnerable
        fig_gen_vuln = go.Figure(data=[go.Pie(
            labels=['Hombres Vulnerables', 'Mujeres Vulnerables'],
            values=[total_hombres_vuln, total_mujeres_vuln],
            hole=0.6,
            marker_colors=['#3288bd', '#d53e4f'],
            textinfo='percent+value',
            texttemplate='%{percent:.1%}<br>%{value:,}'
        )])
        fig_gen_vuln.update_layout(title='Vulnerables por Género', height=350, showlegend=True)
        st.plotly_chart(fig_gen_vuln, use_container_width=True)

    with col3:
        # Métricas de género
        st.markdown("#### 📊 Estadísticas de Género")

        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #3288bd;">
            <h4 style="color: #3288bd; margin: 0;">👨 Hombres</h4>
            <p style="font-size: 1.5rem; margin: 0;"><strong>{total_hombres:,}</strong> total</p>
            <p style="margin: 0;">{total_hombres_vuln:,} vulnerables ({total_hombres_vuln/total_hombres*100:.1f}%)</p>
        </div>
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #d53e4f;">
            <h4 style="color: #d53e4f; margin: 0;">👩 Mujeres</h4>
            <p style="font-size: 1.5rem; margin: 0;"><strong>{total_mujeres:,}</strong> total</p>
            <p style="margin: 0;">{total_mujeres_vuln:,} vulnerables ({total_mujeres_vuln/total_mujeres*100:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico comparativo género x categoría
    st.markdown("### Comparativo Hombres vs Mujeres por Categoría SISBEN")

    categorias = ['Grupo A', 'Grupo B', 'Grupo C', 'Grupo D']
    hombres_vals = [df_filtrado['HOMBRES_A'].sum(), df_filtrado['HOMBRES_B'].sum(),
                   df_filtrado['HOMBRES_C'].sum(), df_filtrado['HOMBRES_D'].sum()]
    mujeres_vals = [df_filtrado['MUJERES_A'].sum(), df_filtrado['MUJERES_B'].sum(),
                   df_filtrado['MUJERES_C'].sum(), df_filtrado['MUJERES_D'].sum()]

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Hombres', x=categorias, y=hombres_vals, marker_color='#3288bd', text=hombres_vals, textposition='auto', texttemplate='%{value:,}'))
    fig_comp.add_trace(go.Bar(name='Mujeres', x=categorias, y=mujeres_vals, marker_color='#d53e4f', text=mujeres_vals, textposition='auto', texttemplate='%{value:,}'))

    fig_comp.update_layout(barmode='group', height=400, yaxis_title="Número de Jóvenes")
    st.plotly_chart(fig_comp, use_container_width=True)

# ============================================
# TAB 5: LOCALIDADES
# ============================================
with tab5:
    st.markdown("### 🏛️ Análisis por Localidad")

    # Agrupar por localidad
    por_loc = df_filtrado.groupby('LOCALIDAD').agg({
        'UPZ': 'count',
        'JOVENES_VULNERABLES': 'sum',
        'JOVENES_TOTAL': 'sum',
        'GRUPO_A': 'sum',
        'GRUPO_B': 'sum',
        'GRUPO_C': 'sum',
        'GRUPO_D': 'sum',
        'HOMBRES_A': 'sum', 'HOMBRES_B': 'sum', 'HOMBRES_C': 'sum', 'HOMBRES_D': 'sum',
        'MUJERES_A': 'sum', 'MUJERES_B': 'sum', 'MUJERES_C': 'sum', 'MUJERES_D': 'sum'
    }).reset_index()

    por_loc['HOMBRES'] = por_loc['HOMBRES_A'] + por_loc['HOMBRES_B'] + por_loc['HOMBRES_C'] + por_loc['HOMBRES_D']
    por_loc['MUJERES'] = por_loc['MUJERES_A'] + por_loc['MUJERES_B'] + por_loc['MUJERES_C'] + por_loc['MUJERES_D']
    por_loc = por_loc.sort_values('JOVENES_VULNERABLES', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de barras horizontal
        fig_loc = px.bar(
            por_loc,
            y='LOCALIDAD',
            x='JOVENES_VULNERABLES',
            orientation='h',
            color='JOVENES_VULNERABLES',
            color_continuous_scale='YlOrRd',
            title='Jóvenes Vulnerables por Localidad',
            text='JOVENES_VULNERABLES'
        )
        fig_loc.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_loc.update_layout(height=600, yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_loc, use_container_width=True)

    with col2:
        # Tabla resumen localidad
        tabla_loc = por_loc[['LOCALIDAD', 'UPZ', 'JOVENES_VULNERABLES', 'JOVENES_TOTAL', 'HOMBRES', 'MUJERES']].copy()
        tabla_loc.columns = ['Localidad', 'UPZ', 'Vulnerables', 'Total', 'Hombres', 'Mujeres']

        st.markdown("#### Resumen por Localidad")
        st.dataframe(
            tabla_loc.style.format({
                'Vulnerables': '{:,.0f}',
                'Total': '{:,.0f}',
                'Hombres': '{:,.0f}',
                'Mujeres': '{:,.0f}'
            }).background_gradient(subset=['Vulnerables'], cmap='YlOrRd'),
            use_container_width=True,
            height=550
        )

    # Treemap de localidades
    st.markdown("### Mapa de Árbol: Composición por Localidad y Grupo SISBEN")

    # Preparar datos para treemap
    treemap_data = []
    for _, row in por_loc.iterrows():
        for grupo, valor in [('A', row['GRUPO_A']), ('B', row['GRUPO_B']), ('C', row['GRUPO_C']), ('D', row['GRUPO_D'])]:
            treemap_data.append({
                'Localidad': row['LOCALIDAD'],
                'Grupo': f'Grupo {grupo}',
                'Jóvenes': valor
            })

    treemap_df = pd.DataFrame(treemap_data)

    fig_tree = px.treemap(
        treemap_df,
        path=['Localidad', 'Grupo'],
        values='Jóvenes',
        color='Jóvenes',
        color_continuous_scale='YlOrRd',
        title=''
    )
    fig_tree.update_layout(height=500)
    st.plotly_chart(fig_tree, use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>Fuente:</strong> Base de datos SISBEN IV |
    <strong>Elaborado por:</strong> Subdirección para la Juventud - Secretaría de Integración Social<br>
    <small>Tablero de exploración - Jóvenes con Oportunidades (JCO)</small>
</div>
""", unsafe_allow_html=True)
