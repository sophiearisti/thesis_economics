# IMPORT LIBRARIES
import pandas as pd
import geopandas as gpd
import sys


years = range(2006, 2026)  # years

# Lista de archivos por cadena
tiendas_files = {
    'oxxo': '../../data/chains/raw_data/oxxos.csv',
    'ara': '../../data/chains/raw_data/tienda_ara.csv',
    'd1': '../../data/chains/raw_data/D1.csv',
    'jb': '../../data/chains/raw_data/justo_y_bueno.csv'
}

def clean_police_crime_files(temporality="anual"):
    
    all_data = []  # store each year's cleaned df
    
    # open codigos municipios 
    municipios = pd.read_csv("../../data/municipalities/codigos_municipios.csv", sep=",")
    
    # rename Código Municipio to Código Dane
    municipios = municipios.rename(columns={"Código Municipio": "Código Dane"})
    
    # only take into account observations that have Municipio in Tipo: Municipio / Isla / Área no municipalizada, that is no Isla / Área no municipalizada
    #municipios = municipios[municipios["Tipo: Municipio / Isla / Área no municipalizada"].isin(["Municipio"])]
    
    # only leave the columns Código Dane 
    municipios = municipios[["Código Dane"]]
    
    # Limpiar y convertir 'municipios'
    municipios["Código Dane"] = pd.to_numeric(municipios["Código Dane"], errors='coerce')
    municipios = municipios.dropna(subset=["Código Dane"])
    municipios["Código Dane"] = municipios["Código Dane"].astype(int)
    
    for year in years:
        print(f"Processing {year}...")
        
        # Load file
        file = f"../../data/municipalities/crime_police/hurto_personas/{year}.xlsx"
        df = pd.read_excel(file)
        
        # Drop unnecessary columns (ignore if not present)
        df = df.drop(columns=[
            "Temática", "Agrupa Edad Persona", "Zona", "Clase de Sitio"
        ], errors="ignore")
        
        # Clean Código Dane (remove last 3 digits)
        df["Código Dane"] = df["Código Dane"].astype(str).str[:-3]
        
        # Ensure numeric values (adjust column name if needed)
        # Assuming crimes are counted in a column like 'Total' or similar
        value_col = "Cantidad"

        # Ensure it's numeric (important if Excel has strings or NaNs)
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
        
        #delete rows Código Dane that are empty or only spaces, because they cause problems when merging with the population projection
        df = df[df["Código Dane"].astype(str).str.strip() != ""]
        
        # 1. Limpiar y convertir 'df' (asegurando que no haya vacíos)
        df["Código Dane"] = pd.to_numeric(df["Código Dane"], errors='coerce')
        df = df.dropna(subset=["Código Dane"])
        df["Código Dane"] = df["Código Dane"].astype(int)

        # 3. Ahora sí, el merge funcionará
        df = df.merge(municipios[["Código Dane"]], on="Código Dane", how="outer")
                
        df[value_col] = df[value_col].fillna(0)
        
        if temporality == "anual":
            # Group by municipality
            df_grouped = df.groupby("Código Dane")[value_col].sum().reset_index()
            df_grouped["year"] = year
        
        elif temporality == "trimestral":
            # Assume there is a 'Mes' column (1–12)
            if "Mes" not in df.columns:
                raise ValueError("Column 'Mes' not found for trimestral aggregation")
            
            # Create trimester
            df["trimestre"] = ((df["Mes"] - 1) // 3) + 1
            
            df_grouped = (
                df.groupby(["Código Dane", "trimestre"])[value_col]
                .sum()
                .reset_index()
            )
            df_grouped["year"] = year
        
        elif temporality == "semestral":
            if "Mes" not in df.columns:
                raise ValueError("Column 'Mes' not found for semestral aggregation")

            # Create semester (1 or 2)
            df["semestre"] = ((df["Mes"] - 1) // 6) + 1

            df_grouped = (
                df.groupby(["Código Dane", "semestre"])[value_col]
                .sum()
                .reset_index()
            )
            df_grouped["year"] = year
            
        else:
            raise ValueError("temporality must be 'anual' or 'trimestral' or 'semestral'")
        
        # Append to list
        all_data.append(df_grouped)
    
    # Concatenate all years
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Rename columns: Asegúrate que 'Código Dane' en final_df sea numérico más adelante
    final_df = final_df.rename(columns={"Código Dane": "codigo_municipio", value_col: "crime_count", "Año": "year"})
    
    # Leer la proyección de población con el separador correcto
    population_projection = pd.read_csv(
        "../../data/municipalities/socioeconomic/poblacion_2005_2042.csv", 
        sep=';', 
        encoding='utf-8-sig'
    )  

    # Limpiar posibles espacios en los nombres de las columnas
    population_projection.columns = population_projection.columns.str.strip()
    
    # Filtrar por ÁREA GEOGRÁFICA == "Total"
    population_projection = population_projection[population_projection["area geografica"] == "Total"]
    
    # IMPORTANTE: Según tu muestra, el código 05001 está en la columna 'MPIO'
    # Vamos a extraer solo lo necesario y renombrar
    population_projection = population_projection[["MPIO", "year", "Poblacion"]].copy()
    population_projection = population_projection.rename(columns={
        "MPIO": "codigo_municipio", 
        "Poblacion": "population"
    })

    # LIMPIEZA DE POBLACIÓN: Quitar puntos de miles y convertir a entero
    if population_projection['population'].dtype == 'object':
        population_projection['population'] = (
            population_projection['population']
            .str.replace('.', '', regex=False)
            .astype(int)
        )
    
    
    # Estandarizar tipos de datos para el merge (ambos a entero)
    final_df["codigo_municipio"] = final_df["codigo_municipio"].astype(int)
    population_projection["codigo_municipio"] = population_projection["codigo_municipio"].astype(int)
    final_df["year"] = final_df["year"].astype(int)
    population_projection["year"] = population_projection["year"].astype(int)

    # Merge final_df con population_projection
    final_df = final_df.merge(
        population_projection[["codigo_municipio", "year", "population"]], 
        on=["codigo_municipio", "year"], 
        how="left"
    )
    
    # Calcular la tasa: (crime_count / population) * 100000
    # Usamos "crime_count" porque ya renombraste la columna arriba
    final_df["crime_rate_per_100k_inhabitants"] = (final_df["crime_count"] / final_df["population"]) * 100000
    
    print(final_df.columns)
    print(final_df.head())
    
    #ver si todos los municipios parecen todos los anos en el final_df
    municipios_por_ano = final_df.groupby("year")["codigo_municipio"].nunique()
    print("Número de municipios únicos por año:")
    print(municipios_por_ano)
    
    return final_df
       
def clean_municipalities_shapefile():
    
    # Path to shapefile
    shp_path = "../../data/municipalities/municipality_shp/MGN_ANM_MPIOS.shp"
    
    # Open shapefile
    gdf = gpd.read_file(shp_path)
    
    # Columns to explicitly drop
    cols_explicit = [
        'VERSION', 'AREA', 'LATITUD', 'LONGITUD',
        'STCTNENCUE', 'STVIVIENDA', 'TSP16_HOG',
        'Shape_Leng', 'Shape_Area'
    ]

    # Columns that start with 'STP'
    cols_stp = [col for col in gdf.columns if col.startswith("STP")]

    # Combine both
    cols_to_drop = cols_explicit + cols_stp

    # Drop safely (ignore errors if some columns don’t exist)
    gdf = gdf.drop(columns=cols_to_drop, errors="ignore")
    
    # Print basic info
    print("=== GeoDataFrame Info ===")
    print(gdf.info())
    
    print("\n=== Columns ===")
    print(gdf.columns)
    
    print("\n=== First rows ===")
    print(gdf.head())
    
    print("\n=== CRS (Coordinate Reference System) ===")
    print(gdf.crs)
    
    #reproject to a metric CRS for accurate spatial operations (like buffering)
    gdf = gdf.to_crs(epsg=3116)

    return gdf

def create_tienda_gdf():
    
    # Leer todos y concatenar
    tienda_list = []
    
    #crear un df con todas las cadenas en un solo lugar
    for cadena, file in tiendas_files.items():
        
        df = pd.read_csv(file)

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

def add_convenience_stores(municipalities, temporality = "anual", tiendas_gdf = None, map = False):
    
    tienda_counts_by_geometry_list = [] #lista para guardar los conteos por año
    
    joined_geometry_tiendas_list = [] # Aquí guardaremos cada joined

    #crear el panel inical sin la parte socioeconomica
    #depending on temporality, we can create different panels
    
    temporality_list = {
        "anual": 1,
        "mensual": 12,
        "trimestral": 4,
        "semestral": 2
    }
    
    #assign based on temporality, the value of the next for loop, for example if it is anual, we will loop by year, if it is mensual we will loop by month and year, etc
    freq_value = temporality_list[temporality]
    
    municipalities.rename(columns={"MPIO_CDPMP": "codigo_municipio"}, inplace=True)
    
    # Spatial join: ahora left_df sigue siendo GeoDataFrame
    # this depends on the geometry chosen for the panel, if it is by upz, we need to do a spatial join with the upz, if it is by localidad we need to do a spatial join with the localidad, and if it is by zat we need to do a spatial join with the zat
    tiendas_gdf = gpd.sjoin(
        municipalities,       # polígonos con geometría
        tiendas_gdf,          # puntos
        how="inner",             # solo nos quedamos con los municipios que tienen tiendas
        predicate="contains"
    )
    
    for year in years:
        
        #loop from 1 to freq_value, for example if it is anual, we will loop only once, if it is mensual we will loop 12 times, etc
        
        for i in range(1, freq_value + 1):     
            
            municipalities['year'] = year
            
            if temporality == "mensual":
                municipalities['month'] = i
            elif temporality == "trimestral":
                municipalities['quarter'] = i
            elif temporality == "semestral":
                municipalities['semester'] = i

            #solo cogemos las tiendas que nos sirven de ese periodo
            if map:
                
                # Filtrar tiendas vigentes en ese año
                # ESTE ES PARA HACER EL MAPA REAL DE TIENDAS ABIERTAS EN ESE AÑO Y FRECUENCIA
                if temporality == "anual":                    
                    joined_geometry_tiendas = tiendas_gdf[
                        (tiendas_gdf['Fecha de Matrícula'].dt.year <= year) &
                        (tiendas_gdf['Último año renovado'] >= year)
                    ]
                    
                else:
                    
                    joined_geometry_tiendas = tiendas_gdf[
                        ((tiendas_gdf['Fecha de Matrícula'].dt.year < year )| 
                         ((tiendas_gdf['Fecha de Matrícula'].dt.year == year) & 
                          (
                            (temporality == "mensual") & (tiendas_gdf['month'] <= i) |
                            (temporality == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (temporality == "semestral") & (tiendas_gdf['semester'] <= i)
                        )) &
                        ((tiendas_gdf['Último año renovado'] > year)| ((tiendas_gdf['Último año renovado'] == year) &
                                (
                            (temporality == "mensual") & (tiendas_gdf['month'] <= i) |
                            (temporality == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (temporality == "semestral") & (tiendas_gdf['semester'] <= i)
                        )
                        )))   
                    ]  
            else:
                #EL COMENTARIADOS ES PARA TENER EL CONTROL RESAGADO
            
                # Filtrar tiendas vigentes en ese año si son oxxo
                # para las demas cadenas sera menor a year la fecha de matricula
                if temporality == "anual":
                    oxxo_mask = (
                        (tiendas_gdf['Fecha de Matrícula'].dt.year <= year) &
                        (tiendas_gdf['Último año renovado'] >= year) &
                        (tiendas_gdf['cadena'] == 'oxxo')
                    )

                    other_mask = (
                        (tiendas_gdf['Fecha de Matrícula'].dt.year < year) &
                        (tiendas_gdf['Último año renovado'] >= year) &
                        (tiendas_gdf['cadena'] != 'oxxo')
                    )

                    joined_geometry_tiendas = tiendas_gdf[oxxo_mask | other_mask]
                else:
                    joined_geometry_tiendas = tiendas_gdf[
                        ((tiendas_gdf['Fecha de Matrícula'].dt.year < year) | 
                         ((tiendas_gdf['Fecha de Matrícula'].dt.year == year) & 
                          (
                            (temporality == "mensual") & (tiendas_gdf['month'] <= i) |
                            (temporality == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (temporality == "semestral") & (tiendas_gdf['semester'] <= i)
                        ))) &
                        ((tiendas_gdf['Último año renovado'] > year) | 
                         ((tiendas_gdf['Último año renovado'] == year) &
                          (
                            (temporality == "mensual") & (tiendas_gdf['month'] <= i) |
                            (temporality == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (temporality == "semestral") & (tiendas_gdf['semester'] <= i)
                        ))) &
                        ((tiendas_gdf['cadena'] == 'oxxo') | 
                         (((tiendas_gdf['Fecha de Matrícula'].dt.year < year) | 
                           ((tiendas_gdf['Fecha de Matrícula'].dt.year == year) & 
                            (
                                (temporality == "mensual") & (tiendas_gdf['month'] < i) |
                                (temporality == "trimestral") & (tiendas_gdf['quarter'] < i) |
                                (temporality == "semestral") & (tiendas_gdf['semester'] < i)
                            ))) &
                          (tiendas_gdf['cadena'] != 'oxxo'))
                        )
                    ]
            
            print (f"Año {year} - Frecuencia {i} - Tiendas vigentes: {len(joined_geometry_tiendas)}")
            print (f"Año {year} - Frecuencia {i} - Tiendas vigentes por cadena: {joined_geometry_tiendas.head()}")        
            
            joined_geometry_tiendas_list.append(joined_geometry_tiendas)

            # Contar tiendas por geometry y cadena
            tienda_counts_by_geometry = joined_geometry_tiendas.groupby(["codigo_municipio",'cadena']).size().unstack(fill_value=0).reset_index()
            
            # Merge con todos los geometry (para asegurarnos de que los que no tengan tiendas aparezcan)
            geo_col = "codigo_municipio"

            time_cols = ['year']

            if temporality == "mensual":
                time_cols.append('month')
            elif temporality == "trimestral":
                time_cols.append('quarter')
            elif temporality == "semestral":
                time_cols.append('semester')     
            
            panel_base = municipalities[[geo_col] + time_cols + ['geometry']].copy() 

            tienda_counts_by_geometry = (
                panel_base
                .merge(tienda_counts_by_geometry,
                    on=[geo_col],
                    how='left')
                .fillna(0)
            )
            
            # Crear columnas de cantidad y dummy
            for cadena in ['oxxo','ara','d1','jb']:
                tienda_counts_by_geometry[f'cantidad_{cadena}'] = tienda_counts_by_geometry.get(cadena, 0)
                tienda_counts_by_geometry[f'dummy_{cadena}'] = (tienda_counts_by_geometry[f'cantidad_{cadena}'] > 0).astype(int)
            
            # Eliminar columnas originales de cadena
            tienda_counts_by_geometry = tienda_counts_by_geometry.drop(columns=[c for c in ['oxxo','ara','d1','jb'] if c in tienda_counts_by_geometry.columns])
                  
            tienda_counts_by_geometry_list.append(tienda_counts_by_geometry)

    # Concatenar todos los años
    tiendas_counts = pd.concat(tienda_counts_by_geometry_list, ignore_index=True)

    # Guardar without geometry
    tiendas_counts = tiendas_counts.drop(columns=['geometry'])          
    tiendas_counts.to_csv("../../data/municipalities/panel/oxxo_counts.csv", index=False)
   
    print(tiendas_counts.columns)
    
    #count the number of each municipio in each year
    municipios_por_ano = tiendas_counts.groupby("year")["codigo_municipio"].nunique()
    print("Número de municipios únicos por año en tiendas_counts:")
    print(municipios_por_ano)
    

    return tiendas_counts, tienda_counts_by_geometry_list, joined_geometry_tiendas_list

def create_panel( crime, convenience_stores, temporality = "anual"):
    #merge all the data and create a panel data set
    
    cols = ['year']

    if temporality == "mensual":
        cols.append('month')
    elif temporality == "trimestral":
        cols.append('quarter')
    elif temporality == "semestral":
        cols.append('semester')  
        
    cols.append('codigo_municipio')
    
    # 2. ESTANDARIZACIÓN CRÍTICA:
    # Iteramos sobre las columnas que vamos a usar para el merge en ambos DataFrames
    for df in [crime, convenience_stores]:
        for col in cols:
            if col in df.columns:
                # Convertimos a numérico, los errores (vacíos o texto) se vuelven NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Eliminamos filas donde la llave de cruce sea inválida (opcional pero recomendado)
                # df.dropna(subset=[col], inplace=True) 
                df[col] = df[col].astype(int)
    
    panel = pd.merge(
        convenience_stores,
        crime,
        on=cols,
        how='right'  # mantener todos los ZAT con tiendas (o sin, si ya estaban en oxxo_counts)
    )
    
    # Reemplazar todos los NaN por 0
    cols_to_fill = [col for col in panel.columns if col != 'codigo_municipio' and col != 'year' and col != 'month' and col != 'quarter' and col != 'semester']
    
    panel[cols_to_fill] = panel[cols_to_fill].fillna(0)
    
    #contar el numero de municipios únicos en el panel
    print(f"Número de municipios únicos en el panel: {panel['codigo_municipio'].nunique()}")
    print(f"Número de filas en el panel: {len(panel)}") 
    
    #quiero saber cuales son los municipios que no salen todos los anos
    municipios_por_ano = panel.groupby("year")["codigo_municipio"].nunique()
    print("Número de municipios únicos por año en el panel:")
    print(municipios_por_ano)
    
    # Guardar el panel final
    panel.to_csv(f"../../data/municipalities/panel/panel_final_municipios_{temporality}.csv", index=False)

def create_panel_map(panel_cleaned, joined_by_geometry_list, joined_tiendas_list):
    #crear un mapa con la ubicacion de las tiendas y el crimen en ese año, dependiendo de la frecuencia, por ejemplo si es anual, se hace un mapa por año, si es mensual se hace un mapa por mes y año, etc
    # Ruta del GeoPackage
    gpkg_path_stores = "../../data/municipalities/maps/joined_all_stores_years.gpkg"
    gpkg_path_municipalities = "../../data/municipalities/maps/joined_all_municipalities_years.gpkg"
    
    #create a list of Ruta del GeoPackage
    gpkg_paths = [gpkg_path_municipalities, gpkg_path_stores]
    
    # create a list of tienda_counts_by_geometry_list and joined_geometry_tiendas_list
    lists_to_save = [joined_by_geometry_list, joined_tiendas_list]
    
    # unir el panel_cleaned con la geometria de zat zat_gdf
    # de zat_gdf solo necesito ZAT y geometry
    # del panel_cleaned todo
    # iterar por años y crear un GeoDataFrame por año
        
    
    for the_list, gpkg_path in zip (lists_to_save, gpkg_paths):
        
        joined_years_panel = []
        
        for year, joined in zip(range(2006, 2026), the_list):
            panel_year = panel_cleaned[panel_cleaned['year'] == year]
            
            if gpkg_path == gpkg_path_municipalities:
                #convert both codigo_municipio to numeric to be able to merge
                panel_year['codigo_municipio'] = pd.to_numeric(panel_year['codigo_municipio'], errors='coerce')
                joined['codigo_municipio'] = pd.to_numeric(joined['codigo_municipio'], errors='coerce')
                
                #ver observaciones en panel_year
                print(f"Año {year} - panel_year: {len(panel_year)} observaciones")
                #ver observaciones en joined
                print(f"Año {year} - joined: {len(joined)} observaciones")

                # unir solo los ZAT que están en panel_year
                merged = joined.merge(panel_year, on='codigo_municipio', how='inner')
                
                # eliminar columnas no deseadas si existen
                cols_drop = ['Fecha de Matrícula', 'estadodelamatrícula', 'fechaderenovación']
                merged = merged.drop(columns=[c for c in cols_drop if c in merged.columns])

                # aseguramos que siga siendo GeoDataFrame
                merged_gdf = gpd.GeoDataFrame(merged, geometry='geometry', crs=joined.crs)
                
                #print number of observations in merged_gdf and how many have geometry and how many not, to see if we are losing a lot of observations when we merge with the geometry
                print(f"Año {year}: {len(merged_gdf)} observaciones, {merged_gdf['geometry'].notna().sum()} con geometría, {merged_gdf['geometry'].isna().sum()} sin geometría")
                #print crs
                print(f"CRS de merged_gdf: {merged_gdf.crs}")
            
            else:
                #en este caso no tenemos que hacer merge porque ya tenemos la geometria de las tiendas con sus datos, solo tenemos que asegurarnos de que el GeoDataFrame tenga la misma estructura que el otro para poder guardarlo en el mismo GeoPackage
                merged_gdf = gpd.GeoDataFrame(joined, geometry='geometry', crs=joined.crs)
                
                #print number of observations in merged_gdf and how many have geometry and how many not, to see if we are losing a lot of observations cuando hacemos el filtro por año y frecuencia
                print(f"Año {year}: {len(merged_gdf)} observaciones, {merged_gdf['geometry'].notna().sum()} con geometría, {merged_gdf['geometry'].isna().sum()} sin geometría")
                #print crs
                print(f"CRS de merged_gdf: {merged_gdf.crs}")

            joined_years_panel.append(merged_gdf)

        # guardar cada año como capa en el GPKG
        for year, gdf in zip(range(2006, 2026), joined_years_panel):
            gdf.to_file(gpkg_path, layer=f"joined_{year}", driver="GPKG")    
    

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print("Uso: python script.py [anual | mensual | semestral | trimestral] [map | panel]")
        sys.exit(1)

    temporality = sys.argv[1].lower()
    output_type = sys.argv[2].lower()

    municipalities = clean_municipalities_shapefile()
    print("MUNICIPALITIES CLEANED")

    tiendas_gdf = create_tienda_gdf()
    print("TIENDAS GDF CREATED")

    tiendas_counts, joined_by_geometry_list, joined_tiendas_list = add_convenience_stores(municipalities = municipalities, temporality = temporality, tiendas_gdf = tiendas_gdf, map = (output_type == "map"))

    print("CONVENIENCE STORES ADDED TO PANEL")
    print (tiendas_counts.columns)
    print(tiendas_counts.head())

    dependent_variable = clean_police_crime_files(temporality = temporality )
    print("CRIME DATA CLEANED")

    create_panel(dependent_variable, tiendas_counts, temporality)
    print("PANEL CREATED")

    if   temporality == "anual" and output_type == "map":    
        #leer el panel limpio
        panel_cleaned = pd.read_csv("../../data/municipalities/panel/panel_final_municipios_anual.csv")
                
        # in joined_zat_tiendas_list how many observations have geometry and how many not, to see if we are losing a lot of observations when we merge with the geometry
        for i, joined in enumerate(joined_by_geometry_list):
            print(f"Año {2006 + i}: {len(joined)} observaciones, {joined['geometry'].notna().sum()} con geometría, {joined['geometry'].isna().sum()} sin geometría")
        
       
        #crear geopackage con el panel y la geometria
        # joined_by_geometry_list tiene la geometria de los municipios con sus daots
        # joined_tiendas_list tiene la geometria de las tiendas con sus datos
        create_panel_map(panel_cleaned, joined_by_geometry_list, joined_tiendas_list)
        print("PANEL MAP CREATED")