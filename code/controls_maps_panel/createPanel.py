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


#this is correct
def create_dependent_variable(final_geometry="upz", frequency="anual", panel_type="2015_2019"):
   
    # open the file of all crimes 
    if panel_type == "2015_2019":
        file_path_2015_2019 = "../../data/crime/bogota_crime/final_crime_data_bogota.csv"
        
        df = pd.read_csv(file_path_2015_2019)
    elif panel_type == "all":
        file_path_2015_2019 = "../../data/crime/bogota_crime/final_crime_data_bogota.csv"
        file_path_2018_2024 = "../../data/crime/bogota_crime/delitos_bogota_consolidado.csv"
        
        df_2015_2019 = pd.read_csv(file_path_2015_2019)
        df_2018_2024 = pd.read_csv(file_path_2018_2024)
        df = pd.concat([df_2015_2019, df_2018_2024], ignore_index=True)
        
        print(f"Datos combinados: {len(df)} registros.")

    else:
        # concatenar csvs de delitos_bogota_theft, delitos_bogota_homicide, delitos_bogota_sexual, delitos_bogota_theft_to_vehicle, delitos_bogota_theft_to_motorbike
        # la unica columna que no tienen igual es la del nombre del delito, entonces para concatenarlos toca a;adir las columnas de los otros delitos con valor 0, para luego concatenarlos y tener un solo csv con todos los delitos
        # these are the columns theft_to_vehicle,homicide,theft_to_motorbike,sexual,theft_to_people
        
        #diccionario de delitos y sus archivos
        delitos_urls = {
            "theft_to_people": "../../data/crime/bogota_crime/delitos_bogota_theft_to_people.csv",
            "theft_to_vehicle": "../../data/crime/bogota_crime/delitos_bogota_theft_to_vehicle.csv",
            "theft_to_motorbike": "../../data/crime/bogota_crime/delitos_bogota_theft_to_motorbike.csv",
            "sexual": "../../data/crime/bogota_crime/delitos_bogota_sexual.csv",
            "homicide": "../../data/crime/bogota_crime/delitos_bogota_homicide.csv"
        }
        
        #hacer un for e ir concatenando los csvs, para luego tener un solo csv con todos los delitos
        dfs = []

        for delito, file_path in delitos_urls.items():
            try:
                # Cargar el CSV
                df_temp = pd.read_csv(file_path)
                dfs.append(df_temp)
                print(f"Cargado: {delito} con {len(df_temp)} registros.")
            except Exception as e:
                print(f"Error cargando {delito}: {e}")

        # 1. Concatenar todos los DataFrames
        # pd.concat alinea automáticamente las columnas por nombre
        df_final = pd.concat(dfs, axis=0, ignore_index=True)

        # 2. Lista de las columnas de delitos para llenar con 0
        columnas_delitos = ["theft_to_people", "theft_to_vehicle", "theft_to_motorbike", "sexual", "homicide"]

        # 3. Reemplazar valores nulos (NaN) por 0 en las columnas de delitos
        # Esto es vital para tu análisis, ya que si es un hurto, homicidio debe ser 0.
        df_final[columnas_delitos] = df_final[columnas_delitos].fillna(0).astype(int)
        
        #quitar columnas que no necesitamos "codigo_upz", "codigo_localidad"
        df_final = df_final.drop(columns=["codigo_upz", "codigo_localidad"], errors='ignore')

        output_combined = "../../data/crime/bogota_crime/delitos_bogota_consolidado.csv"
        df_final.to_csv(output_combined, index=False, encoding='utf-8')
        
        
        df = df_final
        
    #print the data types of the columns
    print(df.dtypes)
    
    # create a gdf with the lat and long of the crimes
    df = df.dropna(subset=['LATITUD', 'LONGITUD'])
    df['geometry'] = gpd.points_from_xy(df.LONGITUD, df.LATITUD)
    crime_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    
    crime_gdf = crime_gdf.to_crs(epsg=3116)

    # since all data is in lat long, we need to do a spatial join to assign each crime to a ZAT
    crime_zat = gpd.sjoin(
        crime_gdf,
        zat_gdf[['geometry', 'ZAT']],  
        how="left",
        predicate="within"
    )
    
    # then use the csv data/panel/res_merges/zat_upz_localidad.csv to assign each ZAT to a UPZ and a Localidad
    merge_zat = pd.read_csv("../../data/panel/res_merges/zat_upz_localidad.csv")

    crime_zat = crime_zat.merge(
        merge_zat,
        on="ZAT",   # mismo nombre que arriba
        how="left"
    )
    
    #drop all zats that do not have a upz or localidad, since they are not in the panel
    crime_zat = crime_zat.dropna(subset=["codigo_upz", "codigo_localidad"])
    
    print(crime_zat.columns)
    print(crime_zat.head())
    
    crime_zat["FECHA_HECHO"] = pd.to_datetime(crime_zat["FECHA_HECHO"], errors="coerce")    
    crime_zat["MES"] = crime_zat["FECHA_HECHO"].dt.month
    crime_zat["DIA"] = crime_zat["FECHA_HECHO"].dt.day
    crime_zat["quarter"] = crime_zat["FECHA_HECHO"].dt.quarter
    crime_zat["semester"] = crime_zat["MES"].apply(lambda x: 1 if x <= 6 else 2) 
    
    # then we can aggregate the crimes by final_geometry and frequency to create the dependent variable for the panel
    #geometry
    if final_geometry == "zat":
        geo_col = "ZAT"
    elif final_geometry == "upz":
        geo_col = "codigo_upz"
    elif final_geometry == "localidad":
        geo_col = "codigo_localidad"
    else:
        raise ValueError("Geometría no válida")
    
    #frequency
    if frequency == "anual":
        group_cols = [geo_col, "AÑO"]
    elif frequency == "mensual":
        group_cols = [geo_col, "AÑO", "MES"]
    elif frequency == "trimestral":
        group_cols = [geo_col, "AÑO", "quarter"]
    elif frequency == "semestral":
        group_cols = [geo_col, "AÑO", "semester"]
    else:
        raise ValueError("Frecuencia no válida")
    
    crime_zat = pd.get_dummies(
        crime_zat,
        columns=["DIA_SEMANA", "GENERO"],
        prefix=["dia", "genero"]    
    )
 
    #tambien por la hora podria poner dummies de noche dia y tarde
    
    #day_cols = [col for col in crime_zat.columns if col.startswith("dia_")]
    gender_cols = [col for col in crime_zat.columns if col.startswith("genero_")]
    
    
    crime_vars = [
        "theft_to_people",
        "homicide",
        "sexual",
        "theft_to_vehicle",
        "theft_to_motorbike",
    ]

    all_sum_vars = crime_vars + gender_cols # + day_cols
    
    #aggregate info
    crime_panel = (
                    crime_zat
                    .groupby(group_cols)[all_sum_vars]
                    .sum()
                    .reset_index()
                )
    
    #after that we can create the index
    #open csv with the population info
    year_begin = crime_panel["AÑO"].min()
    year_end = crime_panel["AÑO"].max()
    
    if final_geometry != "zat":
        if final_geometry == "localidad":
            
            population_df, population_df_gender = get_population_by_year(year_begin, year_end, final_geometry=final_geometry)
            
            #create the index as crime/population
            #merge data sets by ANO AÑO and codigo_localidad COD_LOC
            crime_panel = crime_panel.merge(population_df, left_on=["AÑO", "codigo_localidad"], right_on=["ANO", "COD_LOC"], how="left")
            crime_panel = crime_panel.drop(columns=["ANO", "COD_LOC"])
            
            crime_panel = crime_panel.merge(population_df_gender, left_on=["AÑO", "codigo_localidad"], right_on=["ANO", "COD_LOC"], how="left")
            crime_panel = crime_panel.drop(columns=["ANO", "COD_LOC"])
            
        elif final_geometry == "upz":
            
            population_df, population_df_gender = get_population_by_year(year_begin, year_end, final_geometry=final_geometry)
            
            #create the index as crime/population
            crime_panel = crime_panel.merge(population_df, left_on=["AÑO", "codigo_upz"], right_on=["ANO", "COD_UPZ"], how="left")
            crime_panel = crime_panel.drop(columns=["ANO", "COD_UPZ"])
            
            crime_panel = crime_panel.merge(population_df_gender, left_on=["AÑO", "codigo_upz"], right_on=["ANO", "COD_UPZ"], how="left")
            crime_panel = crime_panel.drop(columns=["ANO", "COD_UPZ"])

        time_cols = [col for col in group_cols if col != geo_col]
            
        # 1. Lista temporal para guardar los resultados de cada pedazo de tiempo
        panel_list = []
        
        # 2. Procesamos bloque por bloque (ej: 2015-Q1, 2015-Q2...)
        for period, group in crime_panel.groupby(time_cols):
            
            group = group.copy()
            
            # Definimos el denominador (población)
            n = group["TOTAL_POBLACION"].fillna(0)
            
            if n.sum() > 0:
                # Calculamos EB para el total
                total_k = group[crime_vars].sum(axis=1)
                group["crime_index_eb"] = Empirical_Bayes(total_k, n).r * 10000
                
                # Calculamos EB para cada delito individual
                for crime in crime_vars:
                    k = group[crime].fillna(0)
                    # Aplicamos el suavizado de PySAL
                    eb_result = Empirical_Bayes(k, n)
                    group[f"{crime}_index_eb"] = eb_result.r * 10000
            else:
                # Si no hay población en este periodo, evitamos errores
                group["crime_index_eb"] = np.nan
                for crime in crime_vars:
                    group[f"{crime}_index_eb"] = np.nan
            
            panel_list.append(group)
        
        # 3. CONCATENAMOS TODO: Aquí es donde vuelves a tener un solo panel
        crime_panel = pd.concat(panel_list, ignore_index=True)   
            
            
        
        crime_panel["crime_index"] = crime_panel[crime_vars].sum(axis=1) / crime_panel["TOTAL_POBLACION"] * 10000
                
        #loop crime vars and create a new column for each one with the index of that crime (crime/population)
        for crime in crime_vars:
            crime_panel[f"{crime}_index"] = crime_panel[crime] / crime_panel["TOTAL_POBLACION"] * 10000
            
        # create gender variables
        crime_panel["male_index"] = crime_panel["genero_MASCULINO"] / crime_panel["Hombre"] * 10000
        crime_panel["female_index"] = crime_panel["genero_FEMENINO"] / crime_panel["Mujer"] * 10000
        
        
    #save the panel
    if panel_type == "2015_2019":
        crime_panel.to_csv(f"../../data/panel/preliminary_panel_datasets/crime_panel_{final_geometry}_{frequency}.csv", index=False)   
    elif panel_type == "all":
        crime_panel.to_csv(f"../../data/panel/preliminary_panel_datasets/crime_panel_all_{final_geometry}_{frequency}.csv", index=False)
    else:
        crime_panel.to_csv(f"../../data/panel/preliminary_panel_datasets/crime_panel_new_{final_geometry}_{frequency}.csv", index=False)
       
    return crime_panel      

def get_population_by_year(year_begin, year_end,final_geometry="upz"):
    
    population_df=pd.read_csv("../../data/panel/baselines/poblacion_bogota_desaggregated.csv")
    population_df = population_df[(population_df["ANO"] >= year_begin) & (population_df["ANO"] <= year_end)]
        
    #if it is by upz, aggregate info by upz and year (sum), just leave the years from year_begin to year_end
    if final_geometry == "upz":
    #if it is by localidad, aggregate info by localidad (sum)
        code = "COD_UPZ"
    elif final_geometry == "localidad":
        code = "COD_LOC"
        
    population_df_gender = (
        population_df
            .groupby(["ANO", code, "SEXO"])["TOTAL_POBLACION"]
            .sum()
            .reset_index()
            .pivot(index=["ANO", code], 
                columns="SEXO", 
                values="TOTAL_POBLACION")
            .reset_index()
    )
    

    population_df = population_df.groupby(["ANO", code])["TOTAL_POBLACION"].sum().reset_index()
    

    return population_df, population_df_gender
    
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

def create_basic_panel(map=False, tienda_gdf = None, final_geometry = "upz", frequency = "anual", panel_type="2015_2019"):

    tienda_counts_by_geometry_list = [] #lista para guardar los conteos por año
    
    joined_geometry_tiendas_list = [] # Aquí guardaremos cada joined

    #crear el panel inical sin la parte socioeconomica
    #depending on frequency, we can create different panels
    
    if panel_type == "2015_2019": 
        años= range(2015, 2019)  # years
        
    elif panel_type == "all":
        años= range(2015, 2024)  # years
    else:
        años= range(2018, 2024)  # years
        
   #años= range(2009, 2026)  # years
    
    frequency_list = {
        "anual": 1,
        "mensual": 12,
        "trimestral": 4,
        "semestral": 2
    }
    
    #assign based on frequency, the value of the next for loop, for example if it is anual, we will loop by year, if it is mensual we will loop by month and year, etc
    freq_value = frequency_list[frequency]
    
    print(f"Creando panel con geometría {final_geometry} y frecuencia {freq_value} y ...")
    
    localidad_gdf.rename(columns={"Identificad": "codigo_localidad"}, inplace=True)
    
    # Copiar todo el GeoDataFrame de ZAT y agregar año y frecuencia (mes, trimestre, semestre)
    
    if final_geometry == "zat":
        geometry_year = zat_gdf[['ZAT','geometry']].copy()
    elif final_geometry == "upz":
        geometry_year = upz_gdf[['codigo_upz','geometry']].copy()
    elif final_geometry == "localidad":
        geometry_year = localidad_gdf[['codigo_localidad','geometry']].copy()
            
    # Spatial join: ahora left_df sigue siendo GeoDataFrame
    # this depends on the geometry chosen for the panel, if it is by upz, we need to do a spatial join with the upz, if it is by localidad we need to do a spatial join with the localidad, and if it is by zat we need to do a spatial join with the zat
    #
    # IMPORTANTE: gpd.sjoin conserva la columna 'geometry' del DataFrame
    # de la IZQUIERDA (geometry_year = polígonos de UPZ), no la del de
    # la derecha (tienda_gdf = puntos). Esto significa que, tras el sjoin,
    # la columna 'geometry' de cada tienda deja de ser su ubicación puntual
    # y pasa a ser el polígono completo de la UPZ que la contiene.
    # Para no perder la ubicación puntual real (necesaria para el buffer
    # de spillover más abajo), la guardamos aparte ANTES del sjoin.
    tienda_gdf = tienda_gdf.copy()
    tienda_gdf['geometry_tienda'] = tienda_gdf.geometry  # copia de la geometría de PUNTO

    tiendas_gdf = gpd.sjoin(
        geometry_year,       # polígonos con geometría
        tienda_gdf,          # puntos
        how="left",
        predicate="contains"
    )
    # Nota: tiendas_gdf['geometry'] es ahora el polígono de la UPZ (heredado
    # de geometry_year). tiendas_gdf['geometry_tienda'] sigue siendo el punto
    # real de la tienda -esta es la que hay que usar para bufferear tiendas.
    
    ####################################################
    # Polígonos de UPZ (sin buffer) para el cálculo de spillover.
    # El buffer se aplica sobre las TIENDAS (dentro del loop, ya
    # que la lista de tiendas cambia cada periodo), no sobre la
    # UPZ. Aquí solo dejamos listo el polígono original de cada
    # geometría, una sola vez, para no repetirlo en cada iteración.
    ####################################################

    geo_col_name = geometry_dict[final_geometry]
    spillover_buffer_m = 400  # metros <-- AQUÍ se define la distancia del buffer

    # Reproyectar a CRS métrico para trabajar con distancias reales (metros)
    geometry_year_metric = geometry_year.to_crs("EPSG:3116")

    # Un polígono por geometría (sin duplicados, SIN buffer)
    upz_polygons = geometry_year_metric[[geo_col_name, 'geometry']].drop_duplicates(
        subset=geo_col_name
    ).reset_index(drop=True)


    for year in años:
        #loop from 1 to freq_value, for example if it is anual, we will loop only once, if it is mensual we will loop 12 times, etc
        for i in range(1, freq_value + 1):     
            
            geometry_year['year'] = year
            
            if frequency == "mensual":
                geometry_year['month'] = i
            elif frequency == "trimestral":
                geometry_year['quarter'] = i
            elif frequency == "semestral":
                geometry_year['semester'] = i

            #solo cogemos las tiendas que nos sirven de ese periodo
            if map:
                
                # Filtrar tiendas vigentes en ese año
                # ESTE ES PARA HACER EL MAPA REAL DE TIENDAS ABIERTAS EN ESE AÑO Y FRECUENCIA
                if frequency == "anual":                    
                    joined_geometry_tiendas = tiendas_gdf[
                        (tiendas_gdf['Fecha de Matrícula'].dt.year <= year) &
                        (tiendas_gdf['Último año renovado'] >= year)
                    ]
                    
                else:
                    
                    joined_geometry_tiendas = tiendas_gdf[
                        ((tiendas_gdf['Fecha de Matrícula'].dt.year < year )| 
                         ((tiendas_gdf['Fecha de Matrícula'].dt.year == year) & 
                          (
                            (frequency == "mensual") & (tiendas_gdf['month'] <= i) |
                            (frequency == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (frequency == "semestral") & (tiendas_gdf['semester'] <= i)
                        )) &
                        ((tiendas_gdf['Último año renovado'] > year)| ((tiendas_gdf['Último año renovado'] == year) &
                                (
                            (frequency == "mensual") & (tiendas_gdf['month'] <= i) |
                            (frequency == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (frequency == "semestral") & (tiendas_gdf['semester'] <= i)
                        )
                        )))   
                    ]  
            else:
                #EL COMENTARIADOS ES PARA TENER EL CONTROL RESAGADO
            
                # Filtrar tiendas vigentes en ese año si son oxxo
                # para las demas cadenas sera menor a year la fecha de matricula
                if frequency == "anual":
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
                            (frequency == "mensual") & (tiendas_gdf['month'] <= i) |
                            (frequency == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (frequency == "semestral") & (tiendas_gdf['semester'] <= i)
                        ))) &
                        ((tiendas_gdf['Último año renovado'] > year) | 
                         ((tiendas_gdf['Último año renovado'] == year) &
                          (
                            (frequency == "mensual") & (tiendas_gdf['month'] <= i) |
                            (frequency == "trimestral") & (tiendas_gdf['quarter'] <= i) |
                            (frequency == "semestral") & (tiendas_gdf['semester'] <= i)
                        ))) &
                        ((tiendas_gdf['cadena'] == 'oxxo') | 
                         (((tiendas_gdf['Fecha de Matrícula'].dt.year < year) | 
                           ((tiendas_gdf['Fecha de Matrícula'].dt.year == year) & 
                            (
                                (frequency == "mensual") & (tiendas_gdf['month'] < i) |
                                (frequency == "trimestral") & (tiendas_gdf['quarter'] < i) |
                                (frequency == "semestral") & (tiendas_gdf['semester'] < i)
                            ))) &
                          (tiendas_gdf['cadena'] != 'oxxo'))
                        )
                    ]
                    

            joined_geometry_tiendas_list.append(joined_geometry_tiendas)

            # Contar tiendas por geometry y cadena
            tienda_counts_by_geometry = joined_geometry_tiendas.groupby([geometry_dict[final_geometry],'cadena']).size().unstack(fill_value=0).reset_index()
            
            # Merge con todos los geometry (para asegurarnos de que los que no tengan tiendas aparezcan)
            geo_col = geometry_dict[final_geometry]

            time_cols = ['year']

            if frequency == "mensual":
                time_cols.append('month')
            elif frequency == "trimestral":
                time_cols.append('quarter')
            elif frequency == "semestral":
                time_cols.append('semester')     
            
            panel_base = geometry_year[[geo_col] + time_cols]
            
            print(panel_base.columns)
            print(panel_base.head())
            print(tienda_counts_by_geometry.columns)
            print(tienda_counts_by_geometry.head())


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
        
            ####################################################
            # Spillover effects:
            # a cada tienda OXXO (punto) se le pone un buffer de
            # 20m a su alrededor. Si ese buffer toca el polígono
            # de una UPZ, esa tienda cuenta como spillover de esa
            # UPZ -salvo que la tienda esté DENTRO de esa misma UPZ,
            # en cuyo caso ya se cuenta en cantidad_oxxo, no en spillover.
            ####################################################

            oxxo_points = joined_geometry_tiendas[joined_geometry_tiendas['cadena'] == 'oxxo'].copy()

            if not oxxo_points.empty:

                # CORRECCIÓN: usar 'geometry_tienda' (el punto real de la tienda),
                # NO 'geometry' (que aquí es el polígono de la UPZ heredado del
                # primer sjoin). Activamos esa columna como la geometría del gdf.
                oxxo_points = gpd.GeoDataFrame(
                    oxxo_points.drop(columns='geometry'),
                    geometry='geometry_tienda',
                    crs="EPSG:3116"
                )
                oxxo_points = oxxo_points.to_crs("EPSG:3116")

                # Buffer alrededor de cada TIENDA (aquí es donde se aplica spillover_buffer_m)
                oxxo_buffered = oxxo_points[['geometry_tienda']].copy()
                oxxo_buffered = oxxo_buffered.rename_geometry('geometry')
                oxxo_buffered['geometry'] = oxxo_buffered.buffer(spillover_buffer_m)

                # sjoin: qué buffers de tienda tocan qué polígonos de UPZ (sin buffer)
                # (predicate="intersects" -> un mismo buffer de tienda puede tocar
                # varias UPZ a la vez si está cerca de un límite compartido por 2 o más)
                tiendas_en_buffer = gpd.sjoin(
                    upz_polygons[[geo_col_name, 'geometry']],
                    oxxo_buffered[['geometry']],
                    how="inner",
                    predicate="intersects"
                )

                # Total de "toques" tienda-buffer -> UPZ por geometría
                total_en_buffer = (
                    tiendas_en_buffer.groupby(geo_col_name)
                    .size()
                    .reset_index(name='total_en_buffer')
                )

                # Restar las tiendas que YA están dentro del polígono original de esa
                # UPZ (esas cuentan en cantidad_oxxo, no son spillover)
                total_en_buffer = total_en_buffer.merge(
                    tienda_counts_by_geometry[[geo_col, 'cantidad_oxxo']],
                    left_on=geo_col_name, right_on=geo_col, how='left'
                ).fillna({'cantidad_oxxo': 0})

                total_en_buffer['spillover_oxxo'] = (
                    total_en_buffer['total_en_buffer'] - total_en_buffer['cantidad_oxxo']
                ).clip(lower=0)  # nunca negativo, por seguridad numérica

                tienda_counts_by_geometry = tienda_counts_by_geometry.merge(
                    total_en_buffer[[geo_col, 'spillover_oxxo']], on=geo_col, how='left'
                ).fillna({'spillover_oxxo': 0})

            else:
                tienda_counts_by_geometry['spillover_oxxo'] = 0

            tienda_counts_by_geometry_list.append(tienda_counts_by_geometry)

    # Concatenar todos los años
    tiendas_counts = pd.concat(tienda_counts_by_geometry_list, ignore_index=True)

    # Guardar
    tiendas_counts.to_csv("../../data/panel/preliminary_panel_datasets/oxxo_counts.csv", index=False)
    
    
    return tiendas_counts, joined_geometry_tiendas_list, tienda_counts_by_geometry_list

####################################################
# Unir controles baseline y otros
####################################################
def create_final_panel(tiendas_counts, dependent_variable_panel, final_geometry, frequency, panel_type="2015_2019"):
       
    print(dependent_variable_panel.columns)
    print(dependent_variable_panel.head())
    print(dependent_variable_panel.dtypes)
    
    # convert the geometry column to float64, to be able to merge with the baselines
    # Convert the geometry column to float64 without using numpy
    tiendas_counts[geometry_dict[final_geometry]] = tiendas_counts[geometry_dict[final_geometry]].astype(float)    
    
    baselines= pd.read_csv(f"../../data/panel/preliminary_panel_datasets/{final_geometry}_all_controls.csv")
    
    # Unir con tiendas_counts
    tiendas_and_baselines = pd.merge(
        tiendas_counts,
        baselines,
        on=geometry_dict[final_geometry],   
        how='left'  # mantener todos los geometries con tiendas (o sin, si ya estaban en oxxo_counts)
    )
    
    print("tiendas_and_baselines")
    print(tiendas_and_baselines.columns)
    print(tiendas_and_baselines.head())

    # ver si en el 2019 cuantos ZAT no tienen codigo_upz
    #print("ZAT sin codigo_upz en 2018:")
    #print(tiendas_and_baselines[tiendas_and_baselines['year']==2018]['codigo_upz'].isna().sum())
  
    #finalmente hacer el merge con zat_data_list
    #zat_data en este es segun zat y year 
    # oxxo_counts es en ZAT y year

    # Asegurarse de que las columnas de ZAT y year tengan mismo tipo

    #renombrar zat_destino a ZAT
    dependent_variable_panel = dependent_variable_panel.rename(columns={'AÑO': 'year'})
    
    cols = ['year']

    if frequency == "mensual":
        cols.append('month')
    elif frequency == "trimestral":
        cols.append('quarter')
    elif frequency == "semestral":
        cols.append('semester')     
    
    cols.append(geometry_dict[final_geometry])
    
    # Merge: todos los ZAT x year de oxxo_counts, si no hay info socioeconómica queda NaN
    panel = pd.merge(
        tiendas_and_baselines,
        dependent_variable_panel,
        on=cols,
        how='left'  # mantener todos los ZAT con tiendas (o sin, si ya estaban en oxxo_counts)
    )
    
   # Reemplazar todos los NaN por 0 excepto estrato_mean
    cols_to_fill = [col for col in panel.columns if col != 'estrato_mean' and col != 'codigo_upz']
    panel[cols_to_fill] = panel[cols_to_fill].fillna(0)
    
    # Guardar el panel final
    if panel_type == "2015_2019":
        panel.to_csv(f"../../data/panel/panel_final_{final_geometry}_{frequency}.csv", index=False)
    
    elif panel_type == "all":
        panel.to_csv(f"../../data/panel/panel_final_all_{final_geometry}_{frequency}.csv", index=False)
        
    else:
        panel.to_csv(f"../../data/panel/panel_final_new_{final_geometry}_{frequency}.csv", index=False)

    #solo quedarme con zats de bogota que tienen codigo_upz
    panel = panel.dropna(subset=[geometry_dict[final_geometry]])

    #ver la cantidad de zat que no estan en todos los anos
    # Número de años distintos en tu panel
    # Número de años distintos según frecuencia
    cols = ['year']
    if frequency == "mensual":
        cols.append('month')
    elif frequency == "trimestral":
        cols.append('quarter')
    elif frequency == "semestral":
        cols.append('semester') 

    # Contar en cuántos periodos aparece cada ZAT
    zat_counts = panel.groupby(geometry_dict[final_geometry])[cols].nunique()

    # Crear un boolean Series indicando ZATs incompletos
    # Aquí usamos min(axis=1) para obtener el valor mínimo por fila
    zat_incompletos = zat_counts.min(axis=1) < 1

    # Filtrar los índices (ZATs) que están incompletos
    zat_incompletos_list = zat_incompletos[zat_incompletos].index.tolist()

    # Quitar esos ZAT del panel
    panel_cleaned = panel[~panel[geometry_dict[final_geometry]].isin(zat_incompletos_list)]

    # Ver cuántos ZATs quedan
    print(f"{final_geometry}s totales después de limpiar: {panel_cleaned[geometry_dict[final_geometry]].nunique()}") 

    # Guardar el panel limpio
    if panel_type == "2015_2019":
        panel_cleaned.to_csv(f"../../data/panel/panel_final_clean_{final_geometry}_{frequency}.csv", index=False)
    elif panel_type == "all":
        panel_cleaned.to_csv(f"../../data/panel/panel_final_clean_all_{final_geometry}_{frequency}.csv", index=False)
    else:
        panel_cleaned.to_csv(f"../../data/panel/panel_final_clean_new_{final_geometry}_{frequency}.csv", index=False)

def create_geopackage_with_panel(panel_cleaned, joined_zat_tiendas_list, tienda_counts_by_geometry_list, final_geometry, panel_type="2015_2019"):
    # Ruta del GeoPackage
    # unir el panel_cleaned con la geometria de zat zat_gdf
    # de zat_gdf solo necesito ZAT y geometry
    # del panel_cleaned todo
    # iterar por años y crear un GeoDataFrame por año
        
    gpkg_path_stores = f"../../data/maps_data/joined_all_stores_years_{final_geometry}.gpkg"
    gpkg_path_geometries = f"../../data/maps_data/joined_all_{final_geometry}_years.gpkg"
    
    #create a list of Ruta del GeoPackage
    gpkg_paths = [gpkg_path_geometries, gpkg_path_stores]
    
    # create a list of tienda_counts_by_geometry_list and joined_geometry_tiendas_list
    lists_to_save = [tienda_counts_by_geometry_list, joined_zat_tiendas_list]
    
    # unir el panel_cleaned con la geometria de zat zat_gdf
    # de zat_gdf solo necesito ZAT y geometry
    # del panel_cleaned todo
    # iterar por años y crear un GeoDataFrame por año
    
    if panel_type == "2015_2019":
        years = range(2015, 2019)
    elif panel_type == "all":
        years = range(2015, 2024)
    else:
        years = range(2018, 2024)
        
    #years = range(2009, 2026)
        
    
    for the_list, gpkg_path in zip (lists_to_save, gpkg_paths):
        
        joined_years_panel = []

        for year, joined in zip(years, the_list):
            
            if gpkg_path == gpkg_path_geometries:
                #first merge with the geometry shp
                if final_geometry == "zat":
                    geometry_gdf = zat_gdf[['ZAT','geometry']].copy()
                elif final_geometry == "upz":
                    geometry_gdf = upz_gdf[['codigo_upz','geometry']].copy()
                elif final_geometry == "localidad":
                    geometry_gdf = localidad_gdf[['codigo_localidad','geometry']].copy()
                
                #merge 
                joined = geometry_gdf.merge(joined, left_on=geometry_dict[final_geometry], right_on=geometry_dict[final_geometry], how='left')
                
                panel_year = panel_cleaned[panel_cleaned['year'] == year]

                # 1. Asegurar que la llave de unión sea STRING en ambos dataframes
                key_col = geometry_dict[final_geometry]

                # Limpiamos el panel
                panel_year[key_col] = panel_year[key_col].astype(str).str.replace('.0', '', regex=False).str.strip()

                # Limpiamos la geometría
                joined[key_col] = joined[key_col].astype(str).str.replace('.0', '', regex=False).str.strip()

                # 2. Ahora sí, el merge funcionará sin error
                merged = joined.merge(panel_year, on=key_col, how='left')
                
                # eliminar columnas no deseadas si existen
                cols_drop = ['Fecha de Matrícula', 'estadodelamatrícula', 'fechaderenovación']
                merged = merged.drop(columns=[c for c in cols_drop if c in merged.columns])

                # aseguramos que siga siendo GeoDataFrame
                merged_gdf = gpd.GeoDataFrame(merged, geometry='geometry', crs=joined.crs)
            else:
                merged_gdf = gpd.GeoDataFrame(joined, geometry='geometry', crs=joined.crs)


            joined_years_panel.append(merged_gdf)

        #print (f"Guardando GeoPackage para {gpkg_path}...")
        #print (f"Cantidad de capas a guardar: {len(joined_years_panel)}")
        
        # guardar cada año como capa en el GPKG
        for year, gdf in zip(years, joined_years_panel):
            gdf.to_file(gpkg_path, layer=f"joined_{year}", driver="GPKG") 
        
def createPanel(map, final_geometry="upz", frequency="anual", panel_type="2015_2019"):
    
    #crear el panel final
    dependent_variables= create_dependent_variable(final_geometry=final_geometry, frequency=frequency, panel_type=panel_type)
    
    tienda_gdf = create_tienda_gdf()
    
    tiendas_counts, joined_zat_tiendas_list, tienda_counts_by_geometry_list = create_basic_panel(tienda_gdf=tienda_gdf, map=map, final_geometry=final_geometry, frequency=frequency, panel_type=panel_type)
   
    create_final_panel(tiendas_counts, dependent_variables, final_geometry=final_geometry, frequency=frequency, panel_type=panel_type  )
    
    if frequency == "anual" and map:
        #leer el panel limpio
        if panel_type == "2015_2019":
            panel_cleaned = pd.read_csv(f"../../data/panel/panel_final_clean_{final_geometry}_anual.csv")
       
        elif panel_type == "all":
            panel_cleaned = pd.read_csv(f"../../data/panel/panel_final_clean_all_{final_geometry}_anual.csv")

        else:
            panel_cleaned = pd.read_csv(f"../../data/panel/panel_final_clean_new_{final_geometry}_anual.csv")
        
        """ #merge tienda_counts_by_geometry_list with the geometry shapefile to have all upz, then add 0 to all the NanS

            #get the geometry shapefile based on the final_geometry
            # Also clean the geometry dataframes as they are loaded
            if final_geometry == "zat" and geometry_dict[final_geometry] in zat_gdf.columns:
                zat_gdf[geometry_dict[final_geometry]] = zat_gdf[geometry_dict[final_geometry]].astype(str).str.replace('.0', '', regex=False)
            elif final_geometry == "upz" and geometry_dict[final_geometry] in upz_gdf.columns:
                upz_gdf[geometry_dict[final_geometry]] = upz_gdf[geometry_dict[final_geometry]].astype(str).str.replace('.0', '', regex=False)
            
            elif final_geometry == "localidad" and geometry_dict[final_geometry] in localidad_gdf.columns:
                localidad_gdf[geometry_dict[final_geometry]] = localidad_gdf[geometry_dict[final_geometry]].astype(str).str.replace('.0', '', regex=False)
            
            
            if final_geometry == "zat":
                geometry_gdf = zat_gdf[['ZAT','geometry']].copy()
            
            elif final_geometry == "upz":
                geometry_gdf = upz_gdf[['codigo_upz','geometry']].copy()
                print(len(geometry_gdf))
                #all upz have a geometry?
                print ("UPZ sin geometría:", geometry_gdf['geometry'].isna().sum())
                #show the upz without geometry
                print(geometry_gdf[geometry_gdf['geometry'].isna()])
                
            elif final_geometry == "localidad":
                geometry_gdf = localidad_gdf[['codigo_localidad','geometry']].copy()
                
            #drop all obs with no upz or localidad, since they are not in the panel
            #geometry_gdf = geometry_gdf.dropna(subset=['codigo_upz', 'codigo_localidad'])
                
            tienda_counts_by_geometry_list2 = []
            for tienda_counts_by_geometry in tienda_counts_by_geometry_list:
                
            
                #merge with the geometry_gdf
                merged = geometry_gdf.merge(tienda_counts_by_geometry, left_on=geometry_dict[final_geometry], right_on=geometry_dict[final_geometry], how='left')
                
                # all observations that dont have geometry
                print(f"Observaciones sin geometría en {final_geometry} para el año {tienda_counts_by_geometry['year'].iloc[0]}:")
                print(merged[merged['geometry'].isna()])
                print(len(merged))
                
                #fillna with 0
                merged = merged.fillna(0)
                
                tienda_counts_by_geometry_list2.append(merged)"""
            
        #crear geopackage con el panel y la geometria
        create_geopackage_with_panel(panel_cleaned, joined_zat_tiendas_list, tienda_counts_by_geometry_list, final_geometry=final_geometry, panel_type=panel_type)
   
#pedir por consola si mapa o panel
# <nombre_del_script>.py map
if __name__ == "__main__":
    
    if len(sys.argv) < 5:
        print("Uso: python script.py [panel | map] [upz | localidad | zat] [anual | mensual | semestral | trimestral] [final panel type: 2015_2019 | new]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    final_geometry = sys.argv[2].lower()
    frequency = sys.argv[3].lower()
    panel_type = sys.argv[4].lower()

    if mode == "panel":
         createPanel(False, final_geometry=final_geometry, frequency=frequency, panel_type=panel_type)
    elif mode == "map":
         createPanel(True, final_geometry=final_geometry, frequency=frequency, panel_type=panel_type)
    else:
        print("Opción inválida. Usa 'panel' o 'map'")