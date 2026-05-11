import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# Diccionario de delitos con sus URLs
delitos_urls = {
    "theft_to_people": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/1/query?where=1%3D1&outFields=*&f=geojson",
    "theft_to_vehicle": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/4/query?where=1%3D1&outFields=*&f=geojson",
    "theft_to_motorbike": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/5/query?where=1%3D1&outFields=*&f=geojson",
    "sexual": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/10/query?where=1%3D1&outFields=*&f=geojson",
    "homicide": "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
}

# Diccionario para traducir días de la semana a español
dias_semana_es = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
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
        
        print(f"Datos descargados para {nombre_delito}. Iniciando limpieza y transformación...")
        print(f"Total registros obtenidos: {len(original_data.get('features', []))}")
        
        features = original_data.get("features", [])
        total_inicial = len(features)
        
        #print features todos los registros para verificar estructura (descomentar si se necesita)
        for i, feature in enumerate(features[:30]):  # Mostrar solo los primeros 3 para no saturar la salida
            print(f"Registro {i+1}: {feature}")
        
        
        if total_inicial == 0:
            print(f"⚠️ No se encontraron datos para {nombre_delito}. Saltando...")
            continue

        # NUEVOS HEADERS AÑADIDOS
        headers = [
            'LONGITUD', 'LATITUD', 'codigo_localidad', 'nombre_localidad', 
            'codigo_upz', 'nombre_upz', 'FECHA_HECHO', 'HORA_HECHO', 
            'DIA', 'MES', 'AÑO', 'DIA_SEMANA', 'DIRECCION_HECHO', 
            'GENERO', nombre_delito
        ]

        file_path = os.path.join(output_dir, f"delitos_bogota_{nombre_delito}.csv")
        total_final = 0

        with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=headers)
            writer.writeheader()

            for feature in features:
                geom_data = feature.get("geometry")
                if not geom_data or "coordinates" not in geom_data:
                    continue
                
                coords = geom_data["coordinates"]
                props = feature.get("properties", {})
                
                raw_upz = props.get("DELIUUPLAN")
                codigo_upz = str(raw_upz).replace("UPZ", "") if raw_upz else ""
                
                ts_ms = props.get("DELTIEFECHA")
                fecha_hecho, hora_hecho, year = "", "", ""
                dia, mes, dia_semana = "", "", ""

                if ts_ms and isinstance(ts_ms, (int, float)):
                    dt_utc = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                    colombia_tz = timezone(timedelta(hours=-5))
                    dt_local = dt_utc.astimezone(colombia_tz)
                    
                    fecha_hecho = dt_local.strftime('%Y-%m-%d')
                    hora_hecho = dt_local.strftime('%H:%M:%S')
                    year = dt_local.year
                    # EXTRACCIÓN DE NUEVOS DATOS TEMPORALES
                    dia = dt_local.day
                    mes = dt_local.month
                    dia_semana = dias_semana_es[dt_local.weekday()]
                else:
                    year = props.get("DELTIEANIO", "")

                # EXTRACCIÓN DE DIRECCIÓN (Usualmente DELNSCATA es el barrio/sector, 
                # pero si existe DELDIRECC se prefiere. Ajustado según SIEDCO estándar)
                direccion = props.get("DELDIRECC") or props.get("DELNSCATA", "NO REPORTA")

                row = {
                    'LONGITUD': coords[0],
                    'LATITUD': coords[1],
                    'codigo_localidad': props.get("DELIULOCAL"),
                    'nombre_localidad': props.get("DELNLOCAL"),
                    'codigo_upz': codigo_upz,
                    'nombre_upz': props.get("DELNUPLAN"),
                    'FECHA_HECHO': fecha_hecho,
                    'HORA_HECHO': hora_hecho,
                    'DIA': dia,
                    'MES': mes,
                    'AÑO': year,
                    'DIA_SEMANA': dia_semana,
                    'DIRECCION_HECHO': direccion,
                    'GENERO': props.get("DELSEXO"),
                     nombre_delito: 1
                }
                writer.writerow(row)
                total_final += 1

        descartados = total_inicial - total_final
        print(f"Total inicial: {total_inicial} | Guardado: {total_final} | Descartados: {descartados}")

    except Exception as e:
        print(f"Error en {nombre_delito}: {e}")

print("\n--- Proceso finalizado ---")