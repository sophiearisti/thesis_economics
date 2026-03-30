import requests
import csv
from datetime import datetime, timezone, timedelta

# 1. Fetch the data
url = "https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/SIEDCO_Delitos_Pub/FeatureServer/1/query?where=1%3D1&outFields=*&f=geojson"

r = requests.get(url)

original_data = r.json()

# 2. Define the CSV headers (the names you requested)
headers = [
    'LONGITUD', 'LATITUD', 'codigo_localidad', 'nombre_localidad', 
    'codigo_upz', 'nombre_upz', 'FECHA_HECHO', 'HORA_HECHO', 'GENERO', 'AÑO', 'theft_to_people'
]

# 3. Process and write to CSV
with open('../../data/crime/bogota_crime/delitos_bogota_theft.csv', 'w', newline='', encoding='utf-8') as output_file:
    writer = csv.DictWriter(output_file, fieldnames=headers)
    writer.writeheader()

    for feature in original_data["features"]:
        props = feature["properties"]
        geom = feature["geometry"]["coordinates"] # [long, lat]
        
        # --- Transformations ---
        
        # Extract number from UPZ (e.g., "UPZ15" -> "15")
        raw_upz = props.get("DELIUUPLAN", "")
        codigo_upz = raw_upz.replace("UPZ", "") if raw_upz else ""
        
        # Convert Unix Timestamp (ms) to Date and Hour
        ts_ms = props.get("DELTIEFECHA", 0)

        if ts_ms:
            # Interpretar como UTC
            dt_utc = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            
            # Convertir a hora de Colombia (UTC-5)
            colombia_tz = timezone(timedelta(hours=-5))
            dt_local = dt_utc.astimezone(colombia_tz)

            fecha_hecho = dt_local.strftime('%Y-%m-%d')
            hora_hecho = dt_local.strftime('%H:%M:%S')
            year = dt_local.year
        else:
            fecha_hecho = ""
            hora_hecho = ""

        # Build the row
        row = {
            'LONGITUD': geom[0],
            'LATITUD': geom[1],
            'codigo_localidad': props.get("DELIULOCAL"),
            'nombre_localidad': props.get("DELNLOCAL"),
            'codigo_upz': codigo_upz,
            'nombre_upz': props.get("DELNUPLAN"),
            'FECHA_HECHO': fecha_hecho,
            'HORA_HECHO': hora_hecho,
            'GENERO': props.get("DELSEXO"),
            'AÑO': year,
            'theft_to_people' : 1,
        }
        
        writer.writerow(row)

print(f"Successfully converted {len(original_data['features'])} records to 'delitos_bogota.csv'")