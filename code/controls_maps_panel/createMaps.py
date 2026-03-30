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

años = range(2018, 2024)  # Example range of years to process

geometry = "upz"

"""for year in años:
    # Load the layer corresponding to each yearjoined_all_stores_years_{final_geometry}
    gdf = gpd.read_file(
        f"../../data/maps_data/joined_all_stores_years_{geometry}.gpkg",
        layer=f"joined_{year}"
    )
    
    # Check data types of all columns
    #print(gdf.dtypes)   
    
    #delete unimportant columns to make the file lighter, we only need latitud, longitud, cadena, codigo_municipio and Nombre
    gdf = gdf[['latitud', 'longitud', 'cadena', 'Nombre', 'geometry', f'codigo_{geometry}']].copy()

    # Create map centered on Bogotá
    m = folium.Map(location=[4.6, -74.1], zoom_start=11)

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
            fields=[f'codigo_{geometry}'],  # Only a few key fields for tooltip
            aliases=[f'Codigo {geometry.upper()}'],  # readable labels
            localize=True,
            sticky=True
        )
    ).add_to(m)

    # Draw store points by retail chain
    for _, row in gdf.iterrows():
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
    m.save(f"../../data/maps_data/points/map_{year}_{geometry}.html")
    
    print(f"Map for year {year} created successfully.")
"""
for year in años:
    
    # Load the layer corresponding to each yearjoined_all_stores_years_{final_geometry}
    gdf = gpd.read_file(
        f"../../data/maps_data/joined_all_{geometry}_years.gpkg",
        layer=f"joined_{year}"
    )
    
    #print observation with upz code 105
    print(f"Observación con código {geometry} 105:")
    print(gdf[gdf[f'codigo_{geometry}'] == 105])
    print(gdf[gdf[f'codigo_{geometry}'] == 105]['geometry'])
    print(gdf[gdf[f'codigo_{geometry}'] == 109])
    print(gdf[gdf[f'codigo_{geometry}'] == 109]['geometry'])
    
    # Check data types of all columns
    #print(gdf.dtypes)   

    # Create map centered on Bogotá
    m = folium.Map(location=[4.6, -74.1], zoom_start=11)

    # Fields to display in the tooltip
    campos_info = [
        'cantidad_oxxo_x', 'cantidad_ara_x', 'cantidad_d1_x', 'cantidad_jb_x',
        'spillover_oxxo_x', 'codigo_upz', 'nombre_upz',
        'nombre_localidad', 'estrato_mean', 'poblacion_2005',
        'poblacion_urbana_2009',
        'personas_por_localidad_2007',
        'personas_por_hogar_2007_localidad',
        'gasto_promedio_mensual_2007_localidad', 'ICV_2007_localidad',
        'num_est_transmi', 'acceso_transmi', 'accesibilidad_arterial',
        'theft_to_people',
        'crime_index',
        'theft_to_people_index',
        'female_index',
        'male_index'
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

    # Save HTML per year
    m.save(f"../../data/maps_data/geometries/map_{year}_{geometry}.html")
    
    print(f"Map for year {year} created successfully.")

