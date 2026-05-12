*****************************************************************************
*version 1: limpieza y merge de llamadas de emergencia con el panel procesado
****************************************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_dofile "$global_dir/code" //dirección de los dofiles
global dir_dofile_controls_analysis "$dir_dofile/controls_maps_panel"
global dir_BDD_panel "$global_dir/data/panel"
global dir_BDD_crimen "$global_dir/data/crime"

global panel 0


global doc_panel "$dir_BDD_panel/panel_final_clean_new_upz_trimestral.csv"

global doc_llamadas "$dir_BDD_crimen/llamadas123.csv"

import delimited "$doc_llamadas", clear

cd "$dir_BDD_panel"

des


//CREAR VARIABLES DUMMY PARA LA TIPOLOGIA  CON  tipo_detalle

levelsof tipo_detalle


* Lista de categorías a mantener según tu imagen
gen to_keep = 0

"ALTERACIÓN DEL ORDEN PÚBLICO", "ATRACO / HURTO EN PROCESO", "DISPAROS", "INTENTO O VIOLACIÓN DE DOMICILIO", "INTENTO/VIOLACIÓN DE DOMICILIO", "MALTRATO", "MALTRATO A MUJER", "MANIFESTACIÓN / MOTÍN", "MANIFESTACIÓN O MOTÍN", "MUERTO", "NARCÓTICOS", "PANDILLAS", "PANDILLAS JUVENILES", "PERSONA O VEHÍCULO SOSPECHOSO", "PERSONA PIDIENDO AUXILIO", "PERSONA TENDIDA EN LA VÍA", "PORTE DE ARMAS", "PORTE ILEGAL DE ARMAS", "RAPTO", "RAPTO / SECUESTRO", "RIÑA", "SECUESTRO", "VEHÍCULO HURTADO", "VENTA O CONSUMO ALCOHOL U OTRO EN MENOR","VIOLENCIA SEXUAL"


* 1. Definir la lista de categorías en una "macro"
local categorias `"ALTERACIÓN DEL ORDEN PÚBLICO"' `"ATRACO / HURTO EN PROCESO"' `"DISPAROS"' ///
    `"INTENTO O VIOLACIÓN DE DOMICILIO"' `"INTENTO/VIOLACIÓN DE DOMICILIO"' `"MALTRATO"' ///
    `"MALTRATO A MUJER"' `"MANIFESTACIÓN / MOTÍN"' `"MANIFESTACIÓN O MOTÍN"' `"MUERTO"' ///
    `"NARCÓTICOS"' `"PANDILLAS"' `"PANDILLAS JUVENILES"' `"PERSONA O VEHÍCULO SOSPECHOSO"' ///
    `"PERSONA PIDIENDO AUXILIO"' `"PERSONA TENDIDA EN LA VÍA"' `"PORTE DE ARMAS"' ///
    `"PORTE ILEGAL DE ARMAS"' `"RAPTO"' `"RAPTO / SECUESTRO"' `"RIÑA"' `"SECUESTRO"' ///
    `"VEHÍCULO HURTADO"' `"VENTA O CONSUMO ALCOHOL U OTRO EN MENOR"' `"VIOLENCIA SEXUAL"'
	
* 2. Crear el indicador usando el bucle

foreach cat in `categorias' {
    replace to_keep = 1 if tipo_detalle == "`cat'"
}

* 3. Filtrar
keep if to_keep == 1
drop to_keep

//DESTRING COD UPZ



//AGRUPAR POR UPZ Y QUARTER Y SUMAR POR TIPO DE INCIDENTE



// ELIMINAR 2026, 2025, 2024, 2023 (POR AHORA)



//ELIMINAR COLUMNAS INNECESARIAS



//MERGE CON EL PANEL FINAL SEGUN EL QUARTER Y EL UPZ


