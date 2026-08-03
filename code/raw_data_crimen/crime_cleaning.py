import pandas as pd

#create a dictionary with the file paths for the different crime types
# for each crime type there are two file paths, one for the years 2015-2018 and one for the year 2019
file_paths = {
    "sexual": {
        "2015_2018": "../../data/crime/raw_data_crimen/DELITOS_SEXUALES_2015_2018.xlsx",
        "2019": "../../data/crime/raw_data_crimen/DELITOS_SEXUALES_2019.xlsx"
    },
    "homicide": {
        "2015_2018": "../../data/crime/raw_data_crimen/HOMICIDIOS_COMUNES_2015-2018.xlsx",
        "2019": "../../data/crime/raw_data_crimen/HOMICIDIOS_COMUNES_2019.xlsx"
    },
    "theft_to_people": {
        "2015_2018": "../../data/crime/raw_data_crimen/HURTO_A_PERSONAS_2015_2018.xlsx",
        "2019": "../../data/crime/raw_data_crimen/HURTO_A_PERSONAS_2019.xlsx"
    },
    "theft_to_vehicle": {
        "2015_2018": "../../data/crime/raw_data_crimen/HURTO_AUTOMOTORES_2015_2018.xlsx",
        "2019": "../../data/crime/raw_data_crimen/HURTO_AUTOMOTORES_2019.xlsx"
    },
    "theft_to_motorbike": {
        "2015_2018": "../../data/crime/raw_data_crimen/HURTO_MOTOCICLETAS_2015_2018.xlsx",
        "2019": "../../data/crime/raw_data_crimen/HURTO_MOTOCICLETAS_2019.xlsx"
    }
}

def append_dfs_by_crime_type(file_path_2015_2018, file_path_2019, type_of_crime):

    # Columns you actually need
    cols_needed = [
        "AÑO",
        "MUNICIPIO_HECHO",
        "FECHA_HECHO",
        "DIA_SEMANA",
        "GENERO",
        "HORA_HECHO",
        "DIRECCION_HECHO",
        "LONGITUD",
        "LATITUD",   # assuming you meant LATITUD instead of repeating LONGITUD
        "MOVIL_VICTIMA"
    ]

    # Read all sheets
    dfs = pd.read_excel(file_path_2015_2018, sheet_name=None)

    df_list = []

    for name, df in dfs.items():
        # Keep only required columns
        df = df[cols_needed]
        df_list.append(df)

    # Append
    df_combined_2015_2018 = pd.concat(df_list, ignore_index=True)

    print(df_combined_2015_2018.head())

    df_2019 = pd.read_excel(file_path_2019)
    # Keep only required columns
    df_2019 = df_2019[cols_needed]

    print(df_combined_2015_2018.columns)
    print(df_2019.columns)

    df_combined = pd.concat([df_combined_2015_2018, df_2019], ignore_index=True)

    print(df_combined.head())
    print(df_combined.columns)
    
    #leave only crimes that took place in Bogota (MUNICIPIO_HECHO == BOGOTÁ D.C. (CT))
    df_combined = df_combined[df_combined["MUNICIPIO_HECHO"] == "BOGOTÁ D.C. (CT)"]
    
    # delete the column MUNICIPIO_HECHO since all the crimes took place in Bogota
    df_combined = df_combined.drop(columns=["MUNICIPIO_HECHO"])
    
    new_column_names = {"sexual", "homicide", "theft_to_people", "theft_to_motorbike", "theft_to_vehicle"}
    
    #ver la cantidad de delitos que se cometieron "A PIE" vs el total
    total_delitos = len(df_combined)
    a_pie = (df_combined["MOVIL_VICTIMA"] == "A PIE").sum()
    porcentaje_a_pie = (a_pie / total_delitos) * 100

    print(f"Total de delitos: {total_delitos}")
    print(f"Delitos 'A PIE': {a_pie} ({porcentaje_a_pie:.2f}%)")

    # Si además quieres ver la distribución completa de MOVIL_VICTIMA
    print("\nDistribución completa de MOVIL_VICTIMA:")
    print(df_combined["MOVIL_VICTIMA"].value_counts())
    print("\nDistribución en porcentajes:")
    
    if type_of_crime == "sexual":
        df_combined.to_csv("../../data/crime/bogota_crime/sexual_crimes_bogota.csv", index=False)
    elif type_of_crime == "homicide":
        df_combined.to_csv("../../data/crime/bogota_crime/homicide_crimes_bogota.csv", index=False)
    elif type_of_crime == "theft_to_people":
        df_combined.to_csv("../../data/crime/bogota_crime/theft_to_people_crimes_bogota.csv", index=False)
    elif type_of_crime == "theft_to_motorbike":
        df_combined.to_csv("../../data/crime/bogota_crime/theft_to_motorbike_crimes_bogota.csv", index=False)
    elif type_of_crime == "theft_to_vehicle":
        df_combined.to_csv("../../data/crime/bogota_crime/theft_to_vehicle_crimes_bogota.csv", index=False)
    
    # go over new_column_names add 1 if in the for loop the type_of_crime is equal to the name of the crime, else add 0
    for crime in new_column_names:
        if crime == type_of_crime:
            df_combined[crime] = 1
        else:
            df_combined[crime] = 0
            
    return df_combined

def main():
    final_df_list = []
    # loop through the file paths and call the append_dfs_by_crime_type function for each crime type
    # while getting the returned dataframe and appending it to the final_df_list
    for crime_type, paths in file_paths.items():
        df = append_dfs_by_crime_type(paths["2015_2018"], paths["2019"], crime_type)
        final_df_list.append(df)
        
    #append all the dataframes in the final_df_list into a single dataframe
    final_df = pd.concat(final_df_list, ignore_index=True)
    
    # Replace comma with dot and convert to float
    final_df["LONGITUD"] = (
        final_df["LONGITUD"]
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    final_df["LATITUD"] = (
        final_df["LATITUD"]
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    
    final_df["FECHA_HECHO"] = pd.to_datetime(final_df["FECHA_HECHO"], errors="coerce")
    print(final_df["FECHA_HECHO"].dtype)
    
    final_df["MES"] = final_df["FECHA_HECHO"].dt.month
    final_df["DIA"] = final_df["FECHA_HECHO"].dt.day
        
    print(final_df.head())
    print(final_df.columns)
    
    #save the final dataframe to a csv file
    final_df.to_csv("../../data/crime/bogota_crime/final_crime_data_bogota.csv", index=False)

if __name__ == "__main__":
    main()