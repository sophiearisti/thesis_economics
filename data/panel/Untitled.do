import delimited "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics/data/crime/bogota_crime/delitos_bogota_consolidado.csv", clear

preserve

collapse (sum) theft_to_vehicle theft_to_people theft_to_motorbike sexual homicide, by(año)

restore
