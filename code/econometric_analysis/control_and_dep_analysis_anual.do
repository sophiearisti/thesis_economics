*********************************************************
*version 2: analisis de los modelos econometricos
*********************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_dofile "$global_dir/code" //dirección de los dofiles
global dir_dofile_controls_analysis "$dir_dofile/controls_maps_panel"
global dir_BDD_panel "$global_dir/data/panel"

global panel 0

if $panel == 1 {
    global doc_panel "$dir_BDD_panel/panel_final_upz_anual.csv"
}
else if $panel == 0 {
	  //global doc_panel "$dir_BDD_panel/panel_final_all_upz_anual.csv"
	  global doc_panel "$dir_BDD_panel/panel_final_con_llamadas_anual.csv" 
}
else {
    global doc_panel "$dir_BDD_panel/panel_final_clean_new_upz_anual.csv"
}

global dir_controls_results "$global_dir/data/controles_results"
global dir_dif_medias "$dir_controls_results/dif_medias"

*----------------------------------------------------------------------*
*********************************************************
*CONTROLES BASELINE Y CONTROLES "CONSTANTES"
* con base al tratamiento
*********************************************************
import delimited "$doc_panel", clear

/*replace area_urbana_2009 = subinstr(area_urbana_2009, ".", "", .)
destring area_urbana_2009, replace

replace densidad_urbana_2009 = subinstr(densidad_urbana_2009, ".", "", .)
destring densidad_urbana_2009, replace*/

replace personas_por_hogar_2007_localida = subinstr(personas_por_hogar_2007_localida, ",", ".", .)
destring personas_por_hogar_2007_localida, replace

replace gasto_promedio_mensual_2007_loca = subinstr(gasto_promedio_mensual_2007_loca, ".", "", .)
destring gasto_promedio_mensual_2007_loca, replace

replace icv_2007_localidad = subinstr(icv_2007_localidad, ",", ".", .)
destring icv_2007_localidad, replace

gen accesibilidad_arterial_dummy = (accesibilidad_arterial>0)

*ssc install bacondecomp, replace

cd "$dir_dif_medias/controls_vars"

*ssc install ietoolkit

//se hace una tabla de diferencia de medias con los baselines entre tratados y nunca tratados

global controles poblacion_urbana_2009 personas_por_localidad_2007 personas_por_hogar_2007_localida num_est_transmi icv_2007_localidad gasto_promedio_mensual_2007_loca estrato_mean acceso_transmi accesibilidad_arterial accesibilidad_arterial_dummy

//recorrer por anos
if $panel == 1 {
	local anos 2015 2016 2017 2018
} 
else if $panel == 0 {
	local anos 2015 2016 2017 2018 2019 2020 2021 2022 2023
}
else {
	local anos 2018 2019 2020 2021 2022 2023
}

foreach a of local anos {
        
        preserve
        
		keep if year == `a'
        
        iebaltab $controles, ///
            groupvar(dummy_oxxo) ///
            control(0) ///
            savexlsx(difmedias_controles_baselines_fixed_`a'_T`t'_anual_$panel) ///
            replace
        
        restore
		
}


*********************************************************
*CONTROLES RESAGADOS TIENDAS
*********************************************************

* es basicamente la misma logica que lo anterior 

* pero en este caso si es para cada cohorte, porque cambian en el tiempo

* es ver si la presencia de otras tiendas parecidas afecta literalmente la presencia de las tiendas oxxo

cd "$dir_dif_medias/controls_staggered_vars"

global staggered_controls dummy_jb dummy_d1 dummy_ara cantidad_jb cantidad_d1 cantidad_ara

if $panel == 1 {
	local anos 2015 2016 2017 2018
} 
else if $panel == 0 {
	local anos 2015 2016 2017 2018 2019 2020 2021 2022 2023
}
else {
	local anos 2018 2019 2020 2021 2022 2023
}

foreach a of local anos {
   
	preserve
	
	keep if year == `a'
	
	iebaltab $staggered_controls, ///
		groupvar(dummy_oxxo) ///
		control(0) ///
		savexlsx(difmedias_controles_staggered_variables_`a'_T`t'_anual_$panel) ///
		replace
	
	restore		

}


*******************************************************
* 1. Cohorte y tiempo relativo
*******************************************************
* VAMOS A CREAR VARIABLE DE COHORTE CUANDO INICIO A SER TRATADO

* Para cada upz, identificar el primer año con OXXO (solo para tratados)

* Para cada upz, identificar el primer trimestre con OXXO

cd "$dir_controls_results/graficas"

preserve

    * 1. Crear índice de tiempo trimestral
    //gen tq = yq(year, quarter)
    //format tq %tq

    * 2. Primer trimestre con OXXO por UPZ
    bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, year, .))

    * 3. Mantener solo tratados
    drop if missing(first_treat)

    * 4. Tiempo relativo en trimestres
    gen rel_time = year - first_treat

    * 5. Colapsar
    collapse (mean) $staggered_controls cantidad_oxxo, by(first_treat rel_time)

    ************* tabla / gráfico **********************

	* Obtener cohortes
	levelsof first_treat, local(cohortes)

	* Construir gráfico y leyenda
	local plotcmd
	local legendcmd
	local i = 1

	foreach c of local cohortes {

		* línea del gráfico
		local plotcmd `plotcmd' ///
			(line cantidad_oxxo rel_time if first_treat==`c', sort)

		* etiqueta de la leyenda
		local label = string(`c', "%tq")
		local legendcmd `legendcmd' label(`i' "`label'")

		local ++i
	}

	twoway `plotcmd', ///
		xline(0, lpattern(dash)) ///
		ytitle("Promedio OXXO") ///
		xtitle("Trimestres relativos al tratamiento") ///
		title("Evolución relativa de OXXO por cohorte") ///
		legend(`legendcmd')
			
	graph export "difference_in_oxxo_counts_panel_${panel}_over_time_year.png", replace

restore

cd "$dir_dif_medias/dep_vars"

*********************************************************
*TABLA DE VAR DEP POR ANO POR TRATAMIENTO STAGGERED PREGUNTAR
*por tratamiento (presencia oxxo)
*********************************************************
global depVar theft_to_vehicle_index theft_to_vehicle theft_to_people_index crime_index theft_to_motorbike_index theft_to_motorbike sexual_index homicide_index male_index female_index


if $panel == 1 {
	local anos 2015 2016 2017 2018
} 
else if $panel == 0 {
	local anos 2015 2016 2017 2018 2019 2020 2021 2022
}
else {
	local anos 2018 2019 2020 2021 2022 2023
}

*para ir comparando cada ano
foreach a of local anos {
    
        
        preserve
        
        keep if year == `a'
        
        iebaltab $depVar, ///
            groupvar(dummy_oxxo) ///
            control(0) ///
            savexlsx(ddifmedias_dep_vars_`a'_T`t'_anual_$panel) ///
            replace
			
        ttest crime_index, by(dummy_oxxo)
		
        restore
}


*total entre tratados y controles
iebaltab $depVar , groupvar(dummy_oxxo) control(0) savexlsx(difmedias_dep_vars_tot_anual_$panel) replace 

global depVar2 tasa_total_violacion_maltrato tasa_total_violacion_domicilio tasa_total_tendida tasa_total_sospechoso tasa_total_rapto_secuestro tasa_total_pandillas_drogas tasa_total_hurto tasa_total_homicidio tasa_total_auxilio tasa_total_atraco tasa_total_armas tasa_total_alteracion_orden tasa_total_alcohol_menores


if $panel == 1 {
	local anos 2015 2016 2017 2018
} 
else if $panel == 0 {
	local anos 2015 2016 2017 2018 2019 2020 2021 2022
}
else {
	local anos 2018 2019 2020 2021 2022 2023
}

*para ir comparando cada ano
foreach a of local anos {
    
        
        preserve
        
        keep if year == `a'
        
        iebaltab $depVar2, ///
            groupvar(dummy_oxxo) ///
            control(0) ///
            savexlsx(ddifmedias_dep_vars2_`a'_T_anual_$panel) ///
            replace
			
        ttest crime_index, by(dummy_oxxo)
		
        restore
}
