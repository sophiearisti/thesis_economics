#vamos a usar geopandas para unir absolutamente todos 
import geopandas as gpd
import pandas as pd
import sys
from esda.smoothing import Empirical_Bayes
import numpy as np

# --- 1. Charge shapefiles ---
zat_gdf = gpd.read_file("../../data/panel/zat/ZAT.shp")
localidad_gdf = gpd.read_file("../../data/panel/localidades/poligonos-localidades.shp")
upz_gdf = gpd.read_file("../../data/panel/upz-bogota/upz-bogota.shp")


zat_gdf = zat_gdf.to_crs(epsg=3116)
localidad_gdf = localidad_gdf.to_crs(epsg=3116)
upz_gdf = upz_gdf.to_crs(epsg=3116)

# Lista de archivos por cadena
tiendas_files = {
    'oxxo': '../../data/chains/raw_data/oxxos.csv',
    'ara': '../../data/chains/raw_data/tienda_ara.csv',
    'd1': '../../data/chains/raw_data/D1.csv',
    'jb': '../../data/chains/raw_data/justo_y_bueno.csv'
}

geometry_dict={
    "zat": "ZAT",
    "upz": "codigo_upz",
    "localidad": "codigo_localidad"
}


def create_dependent_variable(final_geometry="upz", frequency="anual"):
    file_path_2015_2019 = "../../data/crime/bogota_crime/final_crime_data_bogota.csv"
    file_path_2018_2024 = "../../data/crime/bogota_crime/delitos_bogota_consolidado.csv"
    
    df_2015_2019 = pd.read_csv(file_path_2015_2019)
    df_2018_2024 = pd.read_csv(file_path_2018_2024)
    df = pd.concat([df_2015_2019, df_2018_2024], ignore_index=True)
    
    print(f"Datos combinados: {len(df)} registros.")
    
    #print the data types of the columns
    print(df.dtypes)
    
    # create a gdf with the lat and long of the crimes
    df = df.dropna(subset=['LATITUD', 'LONGITUD'])
    df['geometry'] = gpd.points_from_xy(df.LONGITUD, df.LATITUD)
    crime_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    
    crime_gdf = crime_gdf.to_crs(epsg=3116)
    
    return crime_gdf

def create_tienda_gdf():
    
    # Leer todos y concatenar
    tienda_list = []
    
    #crear un df con todas las cadenas en un solo lugar
    for cadena, file in tiendas_files.items():
        
        df = pd.read_csv(file)

        #solo seleccionar las tiendas de bogota
        df = df[df['Cámara de Comercio'].str.contains('BOGOTA', na=False)]

        #no incluir estas columnas  "Cámara de Comercio", "Número de Matrícula"
        df = df.drop(columns=["Cámara de Comercio", "Número de Matrícula"])

        #crear columna cadena
        df['cadena'] = cadena
        
        df['longitud'] = (
            df['longitud']
            .astype(str)
            .str.replace('"', '', regex=False)
            .str.strip()
        )

        df['latitud'] = (
            df['latitud']
            .astype(str)
            .str.replace('"', '', regex=False)
            .str.strip()
        )

        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        
        df = df.dropna(subset=['latitud', 'longitud'])

        #crear columna geometry
        df['geometry'] = gpd.points_from_xy(df.longitud, df.latitud)
        
        #convertir a geodataframe
        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
        
        print(gdf.columns)
        print(gdf.head())
        
        #añadir a la lista
        tienda_list.append(gdf)

    tienda_gdf = pd.concat(tienda_list, ignore_index=True)

    # Reproyectar ambos GeoDataFrames a un CRS métrico
    tienda_gdf = tienda_gdf.to_crs(epsg=3116)
    
    # Convertir fecha de matrícula
    tienda_gdf['Fecha de Matrícula'] = pd.to_datetime(
        tienda_gdf['Fecha de Matrícula'], format='%Y/%m/%d', errors='coerce'
    )
    
    #add to tienda_gdf the columns month, quarter and semester based on the date of matricula, to be able to filter by year and month, year and quarter, etc
    tienda_gdf['month'] = tienda_gdf['Fecha de Matrícula'].dt.month
    tienda_gdf['quarter'] = tienda_gdf['Fecha de Matrícula'].dt.quarter
    tienda_gdf['semester'] = ((tienda_gdf['month'] - 1) // 6 + 1)
    
    return tienda_gdf

def buffers_per_oxxo(tienda_gdf):
    
    #crear 2 geodataframes, uno con los buffers de 100 metros y otro con los buffers de 100 + x metros, para poder hacer tratados y controles
   
    # Filtrar solo las tiendas OXXO
    oxxo_gdf = tienda_gdf[tienda_gdf['cadena'] == 'oxxo'].copy()
    
    buffer_central = 100
    
    # Crear buffers de buffer_central metros alrededor de cada tienda OXXO
    oxxo_gdf['buffer'] = oxxo_gdf.geometry.buffer(buffer_central)
    
    #crear otro buffer de buffer_central + x metros 
    x = 65
    oxxo_gdf['buffer_extended'] = oxxo_gdf.geometry.buffer(buffer_central + x)
    
    # Crear un GeoDataFrame con los buffers
    buffer_gdf_central = gpd.GeoDataFrame(oxxo_gdf[['cadena', 'Fecha de Matrícula', 'buffer']], geometry='buffer', crs=oxxo_gdf.crs)
    buffer_gdf_extended = gpd.GeoDataFrame(oxxo_gdf[['cadena', 'Fecha de Matrícula', 'buffer_extended']], geometry='buffer_extended', crs=oxxo_gdf.crs)
    
    return buffer_gdf_central, buffer_gdf_extended

def cant_crime_per_buffer(buffer_gdf_central, buffer_gdf_extended, crime_gdf, frequency="trimestral" ):
    
    print(f"Calculando cantidad de delitos por buffer con frecuencia {frequency}...")