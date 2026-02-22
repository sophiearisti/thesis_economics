import delimited "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics/data/chains/raw_data/D1.csv"

duplicates tag direccion, generate(dup_dir)


duplicates tag latitud longitud, generate(dup_ll)


drop if cámaradecomercio != "BOGOTA"
