*********************************************************
*version 1: analisis de los modelos econometricos
*********************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/7/econometría avanzada/proyecto_econometria_avanzada"

global dir_dofile "$global_dir/dofiles" //dirección de los dofiles
global dir_dofile_controls_analysis "$dir_dofile/controls_analysis"
global dir_BDD_buffers "$global_dir/data/buffer_data"
global doc_panel "$dir_BDD_buffers/panel_final_clean.csv"
global dir_controls_results "$global_dir/data/controles_results"

*----------------------------------------------------------------------*

*********************************************************
*CONTROLES BASELINE Y CONTROLES "CONSTANTES"
* con base al tratamiento
*********************************************************
import delimited "$doc_panel", clear

replace area_urbana_2009 = subinstr(area_urbana_2009, ".", "", .)
destring area_urbana_2009, replace

replace densidad_urbana_2009 = subinstr(densidad_urbana_2009, ".", "", .)
destring densidad_urbana_2009, replace

replace personas_por_hogar_2007_localida = subinstr(personas_por_hogar_2007_localida, ",", ".", .)
destring personas_por_hogar_2007_localida, replace

replace gasto_promedio_mensual_2007_loca = subinstr(gasto_promedio_mensual_2007_loca, ".", "", .)
destring gasto_promedio_mensual_2007_loca, replace

replace icv_2007_localidad = subinstr(icv_2007_localidad, ",", ".", .)
destring icv_2007_localidad, replace

*borrar zat que no veo que sean relevantes por diferencias significativas
drop if inlist(zat, 819, 812, 820, 1845, 811, 801, 1829, 813, 935, 807, 816, 795, 685, 652, 605, 347, 304, 1620, 1, 738, 668, 931, 1045, 1019, 1040, 1901, 1005, 555, 1004, 746, 1002, 762, 764, 404, 249, 798, 796)

/*
ESTOS ZATS TIENEN ESA PARTICULARIDAD OPD
COMO VOLVIERON A SER TRATADOS, ENTONCES LOS DEJAREMOS EN EL ANALISIS
      +---------------------------+
      | zat   tie~2015   tie~2019 |
      |---------------------------|
 973. | 246          1          0 |
 974. | 246          1          0 |
 975. | 246          1          0 |
 976. | 246          1          0 |
1721. | 433          1          0 |
      |---------------------------|
1722. | 433          1          0 |
1723. | 433          1          0 |
1724. | 433          1          0 |
2289. | 575          1          0 |
2290. | 575          1          0 |
      |---------------------------|
2291. | 575          1          0 |
2292. | 575          1          0 |
      +---------------------------+	 
*/


//COMO TODOS LOS TRATADOS LLEGAN A 2023, INCLUSO ESOS 3 RAROS
list zat year dummy_oxxo if zat==246 | zat==433 | zat==575
*ssc install bacondecomp, replace
replace dummy_oxxo=1 if year==2019 & (zat==246 | zat==433 | zat==575)

cd "$dir_controls_results"

gen accesibilidad_arterial_dummy = (accesibilidad_arterial>0)

*PRIMERO VER SI EL TRATAMIENTO SE MANTIENE A LO LARGO DEL TIEMPO

local años 2011 2015 2019

foreach a of local años {
    local b = `a' + 4

    // Crear variables auxiliares para cada par de años
    bysort zat (year): egen tiene`a' = max(cond(year==`a' & dummy_oxxo==1, 1, 0))
    bysort zat (year): egen tiene`b' = max(cond(year==`b' & dummy_oxxo==1, 1, 0))

    // Mostrar los ZAT que lo tenían en `a' pero no en `b'
    display "----- ZAT que tenían en `a' pero NO en `b' -----"
    list zat tiene`a' tiene`b' if tiene`a'==1 & tiene`b'==0

    // Borrar las variables auxiliares
    drop tiene`a' tiene`b'
}


*ssc install ietoolkit

//se hace una tabla de diferencia de medias con los baselines entre tratados y nunca tratados

global controles poblacion_urbana_2009 poblacion_por_localidad_2005 poblacion_2005 personas_por_localidad_2007 personas_por_hogar_2007_localida num_est_transmi icv_2007_localidad gasto_promedio_mensual_2007_loca estrato_mean densidad_urbana_2009 area_urbana_2009 acceso_transmi accesibilidad_arterial accesibilidad_arterial_dummy total_personas ingreso 

local años 2011 2015 2019 2023

foreach a of local años {
    
	preserve 

		drop if year != `a'
		
		iebaltab $controles , groupvar(dummy_oxxo) control(0) savexlsx(difmedias_controles_baselines_fixed_`a') replace 

	restore

}


*********************************************************
*CONTROLES RESAGADOS TIENDAS
*********************************************************

*es basicamente la misma logica que lo anterior 

*pero en este caso si es para cada cohorte, porque cambian en el tiempo

*es ver si la presencia de otras tiendas parecidas afecta literalmente la presencia de las tiendas oxxo


global staggered_controls dummy_jb dummy_d1 dummy_ara cantidad_jb cantidad_d1 cantidad_ara ingreso

local años 2015 2019 2023 2011

*2011 no nos sirve porque no habia ningun ara ni jb antes de ese ano y en ese ano

foreach a of local años {
    
	preserve 

		drop if year != `a'
		
		iebaltab $staggered_controls , groupvar(dummy_oxxo) control(0) savexlsx(difmedias_controles_staggered_variables_`a') replace 

	restore

}


*******************************************************
* 1. Cohorte y tiempo relativo
*******************************************************
**VAMOS A CREAR VARIABLE DE COHORTE CUANDO INICIO A SER TRATADO

* Para cada ZAT, identificar el primer año con OXXO (solo para tratados)

preserve
	* 1. Año de primera entrada de OXXO
	bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
	gen rel_time = (year - first_treat)/4

	* 4. Calcular promedios por cohorte y tiempo relativo
	collapse (mean) $staggered_controls cantidad_oxxo, by(first_treat rel_time)


	*************haremos una tabla solo por curiosidad**********************

	* 5. Graficar cada cohorte
	* Añadir elementos comunes al gráfico
	twoway (line cantidad_oxxo rel_time if first_treat==2011, sort lcolor(orange)) ///
		   (line cantidad_oxxo rel_time if first_treat==2015, sort lcolor(blue)) ///
		   (line cantidad_oxxo rel_time if first_treat==2019, sort lcolor(red)) ///
		   (line cantidad_oxxo rel_time if first_treat==2023, sort lcolor(green)), ///
		   xline(0, lpattern(dash)) ///
		   ytitle("Promedio OXXO") ///
		   title("Evolución relativa de OXXO por cohorte") ///
		   legend(label(1 "Cohorte 2011") label(2 "Cohorte 2015") ///
				  label(3 "Cohorte 2019") label(4 "Cohorte 2023"))
restore

*********************************************************
*TABLA DE VAR DEP POR ANO POR TRATAMIENTO STAGGERED
*por tratamiento (presencia oxxo)
*********************************************************

global depVar prop_independiente_trabajando prop_independiente_total prop_independiente_buscando prop_formal_no_indep prop_desempleado prop_buscar

local años 2015 2019 2023 2011

*para ir comparando cada ano

foreach a of local años {
    
	preserve 

		drop if year != `a'
		
		iebaltab $depVar , groupvar(dummy_oxxo) control(0) savexlsx(difmedias_dep_vars_`a') replace 
		
		ttest prop_independiente_total, by(dummy_oxxo)

	restore

}

*total entre tratados y controles
iebaltab $depVar , groupvar(dummy_oxxo) control(0) savexlsx(difmedias_dep_vars_tot) replace 
