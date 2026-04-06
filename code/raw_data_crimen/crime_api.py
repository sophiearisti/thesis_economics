import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# Diccionario de delitos con sus URLs
delitos_urls = {
    "theft_to_people": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/1/query?where=1%3D1&outFields=*&f=geojson",
    "theft_to_vehicles": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/4/query?where=1%3D1&outFields=*&f=geojson",
    "theft_to_motorcycles": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/5/query?where=1%3D1&outFields=*&f=geojson",
    "sexual_crimes": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/10/query?where=1%3D1&outFields=*&f=geojson",
    "homicide": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
}

output_dir = '../../data/crime/bogota_crime/'
os.makedirs(output_dir, exist_ok=True)

print("--- Iniciando descarga y limpieza de datos ---\n")

for nombre_delito, url in delitos_urls.items():
    print(f"Procesando: {nombre_delito}...")
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        original_data = r.json()
        
        # Conteo inicial
        features = original_data.get("features", [])
        total_inicial = len(features)
        
        if total_inicial == 0:
            print(f"No se encontraron datos para {nombre_delito}. Saltando...")
            continue

        headers = [
            'LONGITUD', 'LATITUD', 'codigo_localidad', 'nombre_localidad', 
            'codigo_upz', 'nombre_upz', 'FECHA_HECHO', 'HORA_HECHO', 'GENERO', 'AÑO', nombre_delito
        ]

        file_path = os.path.join(output_dir, f"delitos_bogota_{nombre_delito}.csv")
        total_final = 0

        with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=headers)
            writer.writeheader()

            for feature in features:
                # Verificación de seguridad para la geometría
                geom_data = feature.get("geometry")
                if not geom_data or "coordinates" not in geom_data:
                    continue # Aquí es donde se "pierden" los datos sin coordenadas
                
                coords = geom_data["coordinates"]
                props = feature.get("properties", {})
                
                # Extracción y limpieza
                raw_upz = props.get("DELIUUPLAN")
                codigo_upz = str(raw_upz).replace("UPZ", "") if raw_upz else ""
                
                ts_ms = props.get("DELTIEFECHA")
                fecha_hecho, hora_hecho, year = "", "", ""

                if ts_ms and isinstance(ts_ms, (int, float)):
                    dt_utc = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                    colombia_tz = timezone(timedelta(hours=-5))
                    dt_local = dt_utc.astimezone(colombia_tz)
                    fecha_hecho = dt_local.strftime('%Y-%m-%d')
                    hora_hecho = dt_local.strftime('%H:%M:%S')
                    year = dt_local.year
                else:
                    year = props.get("DELTIEANIO", "")

                row = {
                    'LONGITUD': coords[0],
                    'LATITUD': coords[1],
                    'codigo_localidad': props.get("DELIULOCAL"),
                    'nombre_localidad': props.get("DELNLOCAL"),
                    'codigo_upz': codigo_upz,
                    'nombre_upz': props.get("DELNUPLAN"),
                    'FECHA_HECHO': fecha_hecho,
                    'HORA_HECHO': hora_hecho,
                    'GENERO': props.get("DELSEXO"),
                    'AÑO': year,
                    nombre_delito: 1
                }
                writer.writerow(row)
                total_final += 1

        # Resumen por cada delito
        descartados = total_inicial - total_final
        print(f"   Total inicial: {total_inicial}")
        print(f"   Total guardado: {total_final}")
        print(f"   Registros descartados (sin coordenadas): {descartados}")
        print(f"   Archivo: {file_path}\n")

    except Exception as e:
        print(f"Error crítico en {nombre_delito}: {e}\n")

print("--- Proceso finalizado con éxito ---")