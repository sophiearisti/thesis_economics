import delimited "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics/data/crime/bogota_crime/delitos_bogota_consolidado.csv", clear



collapse (sum) theft_to_vehicle theft_to_people theft_to_motorbike sexual homicide, by(año)



import delimited "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics/data/crime/bogota_crime/final_crime_data_bogota.csv", clear

preserve

collapse (sum) theft_to_vehicle theft_to_people theft_to_motorbike sexual homicide, by(año)

restore


import delimited "/Users/sophiaaristizabal/Downloads/30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef.csv", clear



