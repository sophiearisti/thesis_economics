import folium
import geopandas as gpd
from folium.features import GeoJson, GeoJsonTooltip

# Colors by retail chain
colores_cadena = {
    'oxxo': 'red',
    'd1': 'blue',
    'jb': 'black',
    'ara': 'orange'
}

años = [2011, 2015, 2019, 2023]

for year in años:
    # Load the layer corresponding to each year
    gdf = gpd.read_file(
        "../../data/maps_data/joined_all_years.gpkg",
        layer=f"joined_{year}"
    )
    
    # Check data types of all columns
    print(gdf.dtypes)   

    # Create map centered on Bogotá
    m = folium.Map(location=[4.6, -74.1], zoom_start=11)

    # Fields to display in the tooltip
    campos_info = [
        'ZAT', 'cantidad_oxxo', 'cantidad_ara', 'cantidad_d1', 'cantidad_jb',
        'spillover_oxxo', 'codigo_upz', 'nombre_upz', 'codigo_localidad',
        'nombre_localidad', 'estrato_mean', 'poblacion_2005',
        'area_urbana_2009', 'poblacion_urbana_2009', 'densidad_urbana_2009',
        'poblacion_por_localidad_2005', 'personas_por_localidad_2007',
        'personas_por_hogar_2007_localidad',
        'gasto_promedio_mensual_2007_localidad', 'ICV_2007_localidad',
        'num_est_transmi', 'acceso_transmi', 'accesibilidad_arterial', 'prop_independiente_total', 'prop_independiente_trabajando',
        'prop_independiente_buscando', 'prop_buscar', 'prop_desempleado',
        'vendedor_informal'
    ]

    # Draw ZAT polygons with tooltip
    folium.GeoJson(
        gdf,
        style_function=lambda x: {
            'fillColor': 'purple',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.4
        },
        tooltip=GeoJsonTooltip(
            fields=campos_info,
            aliases=[f"{c}:" for c in campos_info],  # readable labels
            localize=True,
            sticky=True
        )
    ).add_to(m)

    # Draw store points by retail chain
    tiendas = gdf[~gdf['index_right'].isna()]
    for _, row in tiendas.iterrows():
        cadena = row['cadena'].lower()
        color = colores_cadena.get(cadena, 'gray')
        folium.CircleMarker(
            location=[row['latitud'], row['longitud']],
            radius=3,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=row['cadena']
        ).add_to(m)

    # Save HTML per year
    m.save(f"../../data/maps_data/map_{year}.html")
