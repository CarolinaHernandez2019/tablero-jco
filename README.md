# Tablero JCO - Priorizacion Territorial

Tablero interactivo para explorar la priorizacion de UPZ de Bogota basado en
poblacion juvenil vulnerable (Jovenes con Oportunidades - SDIS).

- **Ranking dinamico por grupos SISBEN**:Se puede seleccionar que grupos
  incluir en el calculo del ranking (A, B, C, D)
- **Descarga de datos filtrados**: Se pueden exportar los resultados a CSV

## Grupos SISBEN

| Grupo | Descripcion | Por defecto |
|-------|-------------|-------------|
| A | Pobreza Extrema | Incluido |
| B | Pobreza Moderada | Incluido |
| C | Vulnerable | Incluido |
| D | No Vulnerable | Excluido |

## Estructura de archivos

```
streamlit_app/
├── app.py                              # Aplicacion principal
├── requirements.txt                    # Dependencias
├── README.md                           # Este archivo
├── Tabla_Completa_Priorizacion_JCO.xlsx  # Datos de poblacion por UPZ
├── upz-bogota-para-shape-con-resultad.xlsx  # Geodatos (fallback)
└── UPZ06_22/                           # Shapefile de UPZ
    └── pensionadosupz_0622.shp         # Geometrias oficiales
```

## Instalacion local

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

## Uso

1. **Seleccionar grupos SISBEN**: En la barra lateral, marca/desmarca los grupos
   que deseas incluir en el ranking
2. **Filtrar por localidad**: Selecciona una localidad especifica o todas
3. **Ajustar rango**: Usa el slider para ver solo las UPZ en cierto rango
4. **Explorar tabs**: Mapa, Ranking, Categorias, Genero, Localidades

## Ejemplos de uso

### Solo poblacion en pobreza extrema (Grupo A)
- Desmarca B, C, D
- Marca solo A
- El ranking mostrara las UPZ con mayor poblacion en pobreza extrema

### Poblacion vulnerable total (A + B + C)
- Configuracion por defecto
- Excluye Grupo D (no vulnerable)

### Toda la poblacion juvenil (A + B + C + D)
- Marca todos los grupos
- Muestra ranking por poblacion total

## Fuente de datos

- **Poblacion**: Base de datos SISBEN IV
- **Geometrias**: Datos Abiertos Bogota - UPZ (2022)
- **Elaborado por**: Subdireccion para la Juventud - SDIS

## Despliegue en Streamlit Cloud

Disponible en: https://tablero-jco-fmeyctbuhogjs5tgttm2iw.streamlit.app/

---
Enero 2026
