import folium
import geopandas as gpd
import pandas as pd
from folium.features import GeoJson, GeoJsonTooltip
import os

# --- AJUSTES PARA QUE NO PESE ---
# Aumenta la tolerancia si el mapa sigue sin abrir. 0.05 es muy ligero.
TOLERANCIA = 0.03 

colores_cadena = {
    'oxxo': 'red',
    'd1': 'blue',
    'jb': 'black',
    'ara': 'orange'
}

# 1. Definir qué vamos a procesar
# Si quieres puntos, usa el GPKG de stores. Si quieres polígonos, el de municipios.
MODO = "municipalities" # Cambia a "municipalities" según necesites
input_path = f"../../data/municipalities/maps/joined_all_{MODO}_years.gpkg"
output_dir = f"../../data/municipalities/maps/{MODO}/"
os.makedirs(output_dir, exist_ok=True)

for year in range(2006, 2026):
    try:
        gdf = gpd.read_file(input_path, layer=f"joined_{year}")
        gdf = gdf.to_crs(epsg=4326)


        m = folium.Map(location=[4.57, -74.3], zoom_start=6, tiles="cartodbpositron")

        print (gdf.columns)

        if MODO == "municipalities":
                        
            # 2. SELECCIÓN DE CAMPOS (Solo los que existen en tu merge de municipios)
            # Ajusté estos nombres a los que vi en tus logs anteriores
            campos_info = [
                'codigo_municipio', 'cantidad_oxxo_y', 'cantidad_ara_y', 
                'cantidad_d1_y', 'cantidad_jb_y', 'crime_count', 
                'population', 'crime_rate_per_100k_inhabitants'
            ]
            
            # Asegurarnos de que solo pedimos columnas que realmente existan
            campos_presentes = [c for c in campos_info if c in gdf.columns]
                # --- DIBUJAR POLÍGONOS (Solo municipios únicos) ---
                
            poligonos = gdf.drop_duplicates(subset=['codigo_municipio']).copy()
                
            print (f"Año {year} - Campos presentes: {campos_presentes}")  # Ver qué campos están realmente en el GeoDataFrame
            print (f"Año {year} - Cantidad de polígonos: {len(poligonos)}")  # Ver cuántos polígonos hay    
            print (f"Año {year} - Cantidad de observacioes: {len(gdf)}")  # Ver cuántos polígonos hay    
            
            # CRÍTICO: Simplificar la geometría para que el archivo sea ligero
            poligonos['geometry'] = poligonos['geometry'].simplify(TOLERANCIA, preserve_topology=True)

            folium.GeoJson(
                poligonos,
                style_function=lambda x: {
                    'fillColor': 'purple',
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.2
                },
                tooltip=GeoJsonTooltip(
                    fields=campos_presentes,
                    aliases=[f"{c}:" for c in campos_presentes],
                    localize=True,
                    sticky=True
                )
            ).add_to(m)

        else:
            #delete unimportant columns to make the file lighter, we only need latitud, longitud, cadena, codigo_municipio and Nombre
            gdf = gdf[['latitud', 'longitud', 'cadena', 'codigo_municipio', 'Nombre', 'geometry']].copy()

            # --- DIBUJAR PUNTOS (STORES) ---
            # En el modo stores, 'gdf' ya tiene los puntos
            for _, row in gdf.iterrows():
                if pd.notna(row.geometry):
                    # Intentar sacar cadena, si no existe poner 'desconocido'
                    cadena = str(row.get('cadena', 'oxxo')).lower()
                    color = colores_cadena.get(cadena, 'gray')
                    
                    folium.CircleMarker(
                        location=[row.latitud, row.longitud],
                        radius=3,
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.7,
                        popup=f"Cadena: {cadena}<br>Mpio: {row.get('codigo_municipio')} <br> Nombre: {row.get('Nombre')}"
                    ).add_to(m)
                    
            """poligonos = gdf.drop_duplicates(subset=['codigo_municipio']).copy()
            
            # CRÍTICO: Simplificar la geometría para que el archivo sea ligero
            poligonos['geometry'] = poligonos['geometry'].simplify(TOLERANCIA, preserve_topology=True)

            folium.GeoJson(
                poligonos,
                style_function=lambda x: {
                    'fillColor': 'purple',
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.2
                },
                tooltip=GeoJsonTooltip(
                    fields= ["codigo_municipio"],  # Solo mostrar el código del municipio en el tooltip para no sobrecargarlo
                    aliases=["Municipio:"],
                    localize=True,
                    sticky=True
                )
            ).add_to(m)"""


        # 3. GUARDAR 
        m.save(f"{output_dir}map_{year}.html")
        print(f"✅ Año {year} ({MODO}) generado exitosamente.")

    except Exception as e:
        print(f"Error en {year}: {e}")