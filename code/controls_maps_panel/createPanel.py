#vamos a usar geopandas para unir absolutamente todos 
import geopandas as gpd
import pandas as pd
import sys

# shapefile de ZAT
zat_gdf = gpd.read_file("../../data/panel/zat/ZAT.shp")

#ver los datos del shapefile y asi obtener el geometry y el nombre del id del zat
print(zat_gdf.columns)


zat_gdf = zat_gdf.to_crs(epsg=3116)


# Leer los .dta de información socioeconómica para cada año
socioeconomic_datasets = {2011: "../../data/panel/collapsed_years/collapsed_2011.dta", 
                          2019: "../../data/panel/collapsed_years/collapsed_2019.dta", 
                          2023: "../../data/panel/collapsed_years/collapsed_2023.dta", 
                          2015: "../../data/panel/collapsed_years/collapsed_2015.dta"}


# Lista de archivos por cadena
tiendas_files = {
    'oxxo': '../../data/negocios/raw_data/oxxos.csv',
    'ara': '../../data/negocios/raw_data/tienda_ara.csv',
    'd1': '../../data/negocios/raw_data/D1.csv',
    'jb': '../../data/negocios/raw_data/justo_y_bueno.csv'
}

años = [2011, 2019, 2023, 2015]


def create_zat_yearly_data_list():
    
    zat_data_list = []
    
    #crear lista de datos por año o sea concatenar todo
    for year, file in socioeconomic_datasets.items():
        df = pd.read_stata(file)
        df['year'] = year
        print(f"Datos para el año {year}:")
        print(df.columns)
        zat_data_list.append(df)

    # Concatenar todos los años
    zat_data_socioeconomic = pd.concat(zat_data_list, ignore_index=True)
    
    return zat_data_socioeconomic


def create_tienda_gdf():
    # Leer todos y concatenar
    tienda_list = []
    
    #crear un df con todas las cadenas en un solo lugar
    for cadena, file in tiendas_files.items():
        
        df = pd.read_csv(file)
        
        #solo seleccionar las tiendas de bogota
        df = df[df['Cámara de Comercio'].str.contains('BOGOTÁ', na=False)]
        
        #no incluir estas columnas  "Cámara de Comercio", "Número de Matrícula"
        df = df.drop(columns=["Cámara de Comercio", "Número de Matrícula"])
        
        #crear columna cadena
        df['cadena'] = cadena
        
        #crear columna geometry
        df['geometry'] = gpd.points_from_xy(df.longitud, df.latitud)
        
        #convertir a geodataframe
        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
        
        #añadir a la lista
        tienda_list.append(gdf)

    tienda_gdf = pd.concat(tienda_list, ignore_index=True)

    print(tienda_gdf.columns)

    # Reproyectar ambos GeoDataFrames a un CRS métrico (por ejemplo, EPSG:3116 - MAGNA-SIRGAS / Colombia Bogota)
    tienda_gdf = tienda_gdf.to_crs(epsg=3116)
    
    # Convertir fecha de matrícula
    tienda_gdf['Fecha de Matrícula'] = pd.to_datetime(
        tienda_gdf['Fecha de Matrícula'], format='%Y/%m/%d', errors='coerce'
    )
    
    return tienda_gdf


def create_basic_panel(map=False, tienda_gdf = None):

    tienda_counts_by_zat_list = [] #lista para guardar los conteos por año
    
    joined_zat_tiendas_list = [] # Aquí guardaremos cada joined

    #crear el panel inical sin la parte socioeconomica
    for year in años:
        
        # Copiar todo el GeoDataFrame de ZAT y agregar año
        zat_year = zat_gdf[['ZAT','geometry']].copy()
        zat_year['year'] = year
        
        if map:
            # Filtrar tiendas vigentes en ese año
            # ESTE ES PARA HACER EL MAPA REAL DE TIENDAS ABIERTAS EN ESE AÑO
            tiendas_year = tienda_gdf[
                (tienda_gdf['Fecha de Matrícula'].dt.year <= year) &
                (tienda_gdf['Último año renovado'] >= year)
            ]
            
        else:
            #EL COMENTARIADOS ES PARA TENER EL CONTROL RESAGADO
        
            # Filtrar tiendas vigentes en ese año si son oxxo
            # para las demas cadenas sera menor a year la fecha de matricula
            tiendas_year = tienda_gdf[
                (tienda_gdf['fechadematrícula'].dt.year <= year) &
                (tienda_gdf['últimoañorenovado'] >= year) &
                (tienda_gdf['cadena'] == 'oxxo') | (tienda_gdf['fechadematrícula'].dt.year < year) &
                (tienda_gdf['cadena'] != 'oxxo') & (tienda_gdf['últimoañorenovado'] >= year)
            ]
    
    
        # Spatial join: ahora left_df sigue siendo GeoDataFrame
        joined_zat_tiendas = gpd.sjoin(
            zat_year,              # polígonos con geometría
            tiendas_year,          # puntos
            how="left",
            predicate="contains"
        )

        joined_zat_tiendas_list.append(joined_zat_tiendas)

        # Contar tiendas por ZAT y cadena
        tienda_counts_by_zat = joined_zat_tiendas.groupby(['ZAT','cadena']).size().unstack(fill_value=0).reset_index()
        
        # Merge con todos los ZAT (para asegurarnos de que los que no tengan tiendas aparezcan)
        tienda_counts_by_zat = zat_year[['ZAT','year']].merge(tienda_counts_by_zat, on='ZAT', how='left').fillna(0)
        
        # Crear columnas de cantidad y dummy
        for cadena in ['oxxo','ara','d1','jb']:
            tienda_counts_by_zat[f'cantidad_{cadena}'] = tienda_counts_by_zat.get(cadena, 0)
            tienda_counts_by_zat[f'dummy_{cadena}'] = (tienda_counts_by_zat[f'cantidad_{cadena}'] > 0).astype(int)
        
        # Eliminar columnas originales de cadena
        tienda_counts_by_zat = tienda_counts_by_zat.drop(columns=[c for c in ['oxxo','ara','d1','jb'] if c in tienda_counts_by_zat.columns])
    
        ####################################################
        # Spillover effects:
        # variable de zat cercano a un oxxo (que no tiene oxxo)
        ####################################################
        
        # para cada oxxo, crear un buffer de x metros
        # si ese buffer intersecta con otro ZAT, ese ZAT tiene spillover
        #la variable es la cantidad de veces que un ZAT tiene un oxxo cerca
        
        # -------------------------------
        # Spillover de OXXO
        # -------------------------------
        
        buffer = 400  # metros

        oxxo_buffers = tiendas_year[tiendas_year['cadena'] == 'oxxo'].copy()
        
        if not oxxo_buffers.empty:
            
            # Guardar CRS original
            crs_tiendas_orig = oxxo_buffers.crs

            # Reproyectar a CRS métrico
            oxxo_buffers = oxxo_buffers.to_crs("EPSG:3116")

            # Crear buffers alrededor de cada OXXO
            oxxo_buffers['geometry'] = oxxo_buffers.buffer(buffer)

            # Overlay para obtener intersecciones reales ZAT - OXXO buffers
            intersect = gpd.overlay(zat_year[['ZAT','geometry']], oxxo_buffers[['geometry']], how='intersection')

            # Contar cuántos buffers tocan cada ZAT
            spill_counts = intersect.groupby('ZAT').size().reset_index(name='spillover_oxxo')

            # Restar cantidad interna de OXXO si existe
            spill_counts = spill_counts.merge(tienda_counts_by_zat[['ZAT','cantidad_oxxo']], on='ZAT', how='left')
            spill_counts['spillover_oxxo'] = spill_counts['spillover_oxxo'] - spill_counts['cantidad_oxxo']
            spill_counts['spillover_oxxo'] = spill_counts['spillover_oxxo'].clip(lower=0)  # evitar negativos

            # Unir resultado a counts y llenar NaN con 0
            tienda_counts_by_zat = tienda_counts_by_zat.merge(spill_counts[['ZAT','spillover_oxxo']], on='ZAT', how='left').fillna({'spillover_oxxo':0})

            # Volver CRS original
            oxxo_buffers = oxxo_buffers.to_crs(crs_tiendas_orig)

        else:
            tienda_counts_by_zat['spillover_oxxo'] = 0

                    
        tienda_counts_by_zat_list.append(tienda_counts_by_zat)

    # Concatenar todos los años
    tiendas_counts = pd.concat(tienda_counts_by_zat_list, ignore_index=True)

    # Guardar
    tiendas_counts.to_csv("../../data/panel/preliminary_panel_datasets/oxxo_counts.csv", index=False)
    
    print(tiendas_counts.columns)
    
    return tiendas_counts, joined_zat_tiendas_list


####################################################
# Unir controles baseline y otros
####################################################


def create_final_panel(tiendas_counts, zat_data_socioeconomic):
    
    baselines= pd.read_csv("../../data/panel/preliminary_panel_datasets/zat_all_controls.csv")

    # Unir con tiendas_counts
    tiendas_and_baselines = pd.merge(
        tiendas_counts,
        baselines,
        on='ZAT',
        how='left'  # mantener todos los ZAT con tiendas (o sin, si ya estaban en oxxo_counts)
    )

    # ver si en el 2019 cuantos ZAT no tienen codigo_upz
    print("ZAT sin codigo_upz en 2019:")
    print(tiendas_and_baselines[tiendas_and_baselines['year']==2019]['codigo_upz'].isna().sum())

    #abrir el csv 
    #lo hice en un stata porque no me funcionaba y no encontre el error
    #precisamente creo que es porque hay un duplicado en los controles que exploto todo 
    """tiendas_and_baselines = pd.read_csv(
        "../../data/panel/tiendas_and_baselines.csv",
        sep=",",              # separador correcto
        quotechar='"',        # respeta comillas
        decimal=",",          # convierte "4,07" en 4.07
        thousands="."         # quita puntos de miles en números largos
    )"""

    #finalmente hacer el merge con zat_data_list
    #zat_data en este es segun zat y year 
    # oxxo_counts es en ZAT y year

    # Asegurarse de que las columnas de ZAT y year tengan mismo tipo

    #renombrar zat_destino a ZAT
    zat_data_socioeconomic = zat_data_socioeconomic.rename(columns={'zat_destino': 'ZAT'})
    tiendas_and_baselines = tiendas_and_baselines.rename(columns={'zat': 'ZAT'})

    zat_data_socioeconomic['ZAT'] = zat_data_socioeconomic['ZAT'].fillna(-1).astype(int)
    zat_data_socioeconomic['year'] = zat_data_socioeconomic['year'].astype(int)
    tiendas_and_baselines['ZAT'] = tiendas_and_baselines['ZAT'].astype(int)
    tiendas_and_baselines['year'] = tiendas_and_baselines['year'].astype(int)

    # Merge: todos los ZAT x year de oxxo_counts, si no hay info socioeconómica queda NaN
    panel = pd.merge(
        tiendas_and_baselines,
        zat_data_socioeconomic,
        on=['ZAT', 'year'],
        how='left'  # mantener todos los ZAT con tiendas (o sin, si ya estaban en oxxo_counts)
    )

    # Reemplazar todos los NaN por 0 excepto estrato_mean
    cols_to_fill = [col for col in panel.columns if col != 'estrato_mean' and col != 'codigo_upz']
    panel[cols_to_fill] = panel[cols_to_fill].fillna(0)
    

    # Guardar el panel final
    panel.to_csv("../../data/panel/panel_final.csv", index=False)


    #solo quedarme con zats de bogota que tienen codigo_upz
    panel = panel.dropna(subset=['codigo_upz'])

    #ver la cantidad de zat que no estan en todos los anos
    # Número de años distintos en tu panel
    n_years = panel['year'].nunique()

    # Contar en cuántos años aparece cada ZAT
    zat_counts = panel.groupby('ZAT')['year'].nunique()

    # Filtrar los que no están en todos los años
    zat_incompletos = zat_counts[zat_counts < n_years].index.tolist()

    #quitar esos ZAT del panel
    panel_cleaned = panel[~panel['ZAT'].isin(zat_incompletos)]

    #ver con cuantos zats se queda
    print(f"ZATs totales después de limpiar: {panel_cleaned['ZAT'].nunique()}") 

    #guardar el panel final limpio
    panel_cleaned.to_csv("../../data/panel/panel_final_clean.csv", index=False)


def create_geopackage_with_panel(panel_cleaned, joined_zat_tiendas_list):
    # Ruta del GeoPackage
    gpkg_path = "../../data/maps_data/joined_all_years.gpkg"

    #unir el panel_cleaned con la geometria de zat zat_gdf
    # de zat_gdf solo necesito ZAT y geometry
    # del panel_cleaned todo
    # iterar por años y crear un GeoDataFrame por año
        
    joined_years_panel = []

    for year, joined in zip(años, joined_zat_tiendas_list):
        panel_year = panel_cleaned[panel_cleaned['year'] == year]

        # unir solo los ZAT que están en panel_year
        merged = joined.merge(panel_year, on='ZAT', how='inner')
        
        # eliminar columnas no deseadas si existen
        cols_drop = ['fechadematrícula', 'estadodelamatrícula', 'fechaderenovación']
        merged = merged.drop(columns=[c for c in cols_drop if c in merged.columns])

        # aseguramos que siga siendo GeoDataFrame
        merged_gdf = gpd.GeoDataFrame(merged, geometry='geometry', crs=joined.crs)

        joined_years_panel.append(merged_gdf)

    # guardar cada año como capa en el GPKG
    for year, gdf in zip(años, joined_years_panel):
        gdf.to_file(gpkg_path, layer=f"joined_{year}", driver="GPKG")
  
        
def createPanel(map):
    
    #crear el panel final
    zat_data_socioeconomic = create_zat_yearly_data_list()
    
    tienda_gdf = create_tienda_gdf()
    
    tiendas_counts, joined_zat_tiendas_list = create_basic_panel(tienda_gdf=tienda_gdf, map=map)
   
    create_final_panel(tiendas_counts, zat_data_socioeconomic)
    
    #leer el panel limpio
    panel_cleaned = pd.read_csv("../../data/panel/panel_final_clean.csv")
    
    #crear geopackage con el panel y la geometria
    create_geopackage_with_panel(panel_cleaned, joined_zat_tiendas_list)
  
  
#pedir por consola si mapa o panel
# <nombre_del_script>.py map
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py [panel | map]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "panel":
        createPanel(False)
    elif mode == "map":
         createPanel(True)
    else:
        print("Opción inválida. Usa 'panel' o 'map'")