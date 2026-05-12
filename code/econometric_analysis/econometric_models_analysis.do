*********************************************************
*version 4:analisis de controles y var dep
*********************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_dofile "$global_dir/code" //dirección de los dofiles
global dir_dofile_controls_analysis "$dir_dofile/controls_maps_panel"
global dir_BDD_panel "$global_dir/data/panel"

global panel 0

if $panel == 1 {
    global doc_panel "$dir_BDD_panel/panel_final_upz_trimestral.csv"
}
else if $panel == 0 {
	    global doc_panel "$dir_BDD_panel/panel_final_all_upz_trimestral.csv"
}
else {
    global doc_panel "$dir_BDD_panel/panel_final_clean_new_upz_trimestral.csv"
}

global dir_controls_results "$global_dir/data/controles_results"

*----------------------------------------------------------------------*

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

*drop UPZ 108 PORQUE APARECE Y DESAPARECEN LOS OXXOS 



* Crear una variable de tiempo trimestral
gen tq = yq(year, quarter)
format tq %tq

*borrar duplicados
duplicates drop

* Declarar el panel
xtset codigo_upz tq

* Calcular la diferencia con el trimestre anterior
* Asumiendo que tu variable se llama 'cant_oxxo'
gen diff_oxxo = cantidad_oxxo - L.cantidad_oxxo

* Crear una bandera (flag) para las UPZ que tuvieron una disminución
gen disminuyo = 1 if diff_oxxo < 0 & !missing(diff_oxxo)

* Listar las UPZ, el periodo y el cambio para los casos donde disminuyó
list codigo_upz year quarter cantidad_oxxo diff_oxxo if disminuyo == 1

//upz 99 y 13
drop if codigo_upz == 13
drop if codigo_upz == 99
drop if codigo_upz == 108
drop if codigo_upz == 63
drop if codigo_upz == 117

***************************************************************
*REGRESIONES PARA LA ENTREGA
***************************************************************

cd "$dir_controls_results"

*ssc install outreg2, replace

if $panel == 1 | $panel == 0 {
	global dep_var crime_index theft_to_vehicle_index theft_to_vehicle theft_to_people_index theft_to_motorbike_index theft_to_motorbike sexual_index homicide_index male_index female_index
}
else {
    global dep_var crime_index theft_to_people_index male_index female_index
}

if $panel == 1 | $panel == 0 {
	global day_controls dia_viernes dia_sábado dia_miércoles dia_martes dia_lunes dia_jueves dia_domingo
}

global access_controls spillover_oxxo
 
global harddiscount_controls cantidad_d1 cantidad_ara cantidad_jb 

 
*********************************************************
*TWO WAY FIXED EFFECTS
*********************************************************
 
	
local first = 1

foreach y of global dep_var {

    //reg `y' dummy_oxxo

    if `first' == 1 {
		reghdfe `y' dummy_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		

        local first = 0
    }
    else {
        reghdfe `y' dummy_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
    }
} 


bys codigo_upz (tq): gen change = dummy_oxxo - dummy_oxxo[_n-1]

list codigo_upz tq dummy_oxxo if change < 0

bacondecomp crime_index dummy_oxxo, ddetail vce(cluster codigo_upz)


foreach y of global dep_var {

	
	reghdfe `y' dummy_oxxo $harddiscount_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, NO)
		
	if "`y'" == "crime_index" {
		bacondecomp crime_index dummy_oxxo $harddiscount_controls, ddetail vce(cluster codigo_upz)
	}
	
	reghdfe `y' dummy_oxxo $access_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, NO, Day controls, NO, Control spillover, SI)
		
	if "`y'" == "crime_index" {
		bacondecomp crime_index dummy_oxxo  $access_controlss, ddetail vce(cluster codigo_upz)
	}
		
	if $panel == 1 {
			
		
		reghdfe `y' dummy_oxxo $day_controls $harddiscount_controls ,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

			
		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y' D H") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, SI, Day controls, SI, Control spillover, NO)
		
		if "`y'" == "crime_index" {
			bacondecomp crime_index dummy_oxxo $day_controls $harddiscount_controls , ddetail vce(cluster codigo_upz)
		}

			
		reghdfe `y' dummy_oxxo $day_controls  ,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
		
			
		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y' D A") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Day controls, SI, Control spillover, NO)
		
		if "`y'" == "crime_index" {
			bacondecomp crime_index dummy_oxxo $day_controls , ddetail vce(cluster codigo_upz)
		}
		
		reghdfe `y' dummy_oxxo $day_controls $access_controls ,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

			
		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y' D A") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Day controls, SI, Control spillover, SI)
		
		
		reghdfe `y' dummy_oxxo $day_controls $access_controls $harddiscount_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

			
		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y' D A") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, SI,  Day controls, SI, Control spillover, SI)

	
	}	

	
	reghdfe `y' dummy_oxxo $harddiscount_controls $access_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_multiples_${panel}.xls, append label ///
	ctitle("TWFE `y' H A") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, SI,  Day controls, NO, Control spillover, SI)	
	
	
}
		


********************************************************
*C&S
*********************************************************

cd "$dir_controls_results/events study"

preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	if $panel == 1 {
		csdid crime_index  $day_controls $access_controls $harddiscount_controls, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz)

	}
	else {
		csdid crime_index $access_controls $harddiscount_controls, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz)

	}
	
	estat all
	
	* Revisar los efectos promedio
	estat pretrend

	*ver el ATT
	estat simple
	
	* Guardar los resultados en una matriz
	matrix results = r(table)

	* Extraer valores del ATT
	local ATT     = results[1,1]
	local SE      = results[2,1]
	local zstat   = results[3,1]
	local pvalue  = results[4,1]
	local ll      = results[5,1]
	local ul      = results[6,1]

	* Mostrar para verificar
	di "ATT = `ATT'"
	di "SE = `SE'"
	di "p-value = `pvalue'"

	/*outreg2 using tabla_regresiones.xls, append label ///
    ctitle("ATT Callaway & Sant'Anna Controles") ///
    addstat("ATT", `ATT', "Std. Err.", `SE', "p(ATT)", `pvalue', "CI [95%]", "`ll' - `ul'") ///
    addtext(Método, "CSDID", Controles, "Sí", Cluster, "codigo_upz")*/


	* Estimar los efectos dinámicos (event study)
	estat all

	* Graficar el event study	
	estat event, estore(cs1)
	csdid_plot, title("ES de CS")
	
	graph export "event_study_csS_${panel}.png", replace width(1200) height(800)

	
	* 1. Estimar los efectos dinámicos (event study)
	estat event, window(-24 24) estore(cs1)

	* 2. Extraer resultados y transponer
	matrix M = r(table)'
	matrix list M

	* 3. Convertir matriz a dataset sin borrar memoria
	clear
    * Convertir la matriz directamente a variables
    svmat M, names(col)
    
    * Extraer los nombres de las filas (donde Stata guarda el periodo relativo)
    gen rowname = ""
    local names : rowfullnames M
    forvalues i = 1/`: word count `names'' {
        replace rowname = "`: word `i' of `names''" in `i'
    }

    * 4. Limpiar el periodo relativo (exp)
    * Stata los llama "tm3" para -3, "tp2" para +2, "t0" para 0
    gen exp = .
    replace exp = real(substr(rowname, 3, .)) if strpos(rowname, "tp") // Post
    replace exp = -real(substr(rowname, 3, .)) if strpos(rowname, "tm") // Pre
    replace exp = 0 if rowname == "t0" | rowname == "T0"

    * 5. Renombrar para que coincida con tu estructura
    rename b crime_index1
    rename se crime_index0
    rename ll lb
    rename ul ub

    * 6. Agregar el periodo de referencia (-1) que siempre es CERO
    set obs `=_N + 1'
    replace exp = -1 in L
    foreach var in crime_index1 crime_index0 lb ub {
        replace `var' = 0 in L
    }

    * 7. Limpieza final y exportación
    drop if missing(exp) // Eliminar filas extra de la matriz que no sean periodos
    sort exp
    keep exp crime_index1 crime_index0 lb ub
    
    list, noobs
    export delimited using "paraEventsStudyMultipleCS_${panel}.csv", replace
	
restore

preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	csdid crime_index, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz) notyet

	* Revisar los efectos promedio
	estat pretrend

	*ver el ATT
	estat simple
	
	* Guardar los resultados en una matriz
	matrix results = r(table)

	* Extraer valores del ATT
	local ATT     = results[1,1]
	local SE      = results[2,1]
	local zstat   = results[3,1]
	local pvalue  = results[4,1]
	local ll      = results[5,1]
	local ul      = results[6,1]

	* Mostrar para verificar
	di "ATT = `ATT'"
	di "SE = `SE'"
	di "p-value = `pvalue'"
	
	/*local ci = string(`ll') + " - " + string(`ul')

	outreg2 using tabla_regresiones.xls, append label ///
    ctitle("ATT Callaway & Sant'Anna") ///
    addstat("ATT", `ATT', "Std. Err.", `SE', "p(ATT)", `pvalue', "CI [95%]", "`ci'") ///
    addtext(Método, "CSDID", Controles, "Sí", Cluster, "codigo_upz")*/
	
	estat all

	* Graficar el event study	
	estat event, estore(cs1)
	csdid_plot, title("ES de CS")
	
	graph export "event_study_csM_${panel}.png", replace width(1200) height(800)
	
	
	
	* 1. Estimar los efectos dinámicos (event study)
	estat event, window(-24 24) estore(cs1)

	* 2. Extraer resultados y transponer
	matrix M = r(table)'
	matrix list M

	* 3. Convertir matriz a dataset sin borrar memoria
	clear
    * Convertir la matriz directamente a variables
    svmat M, names(col)
    
    * Extraer los nombres de las filas (donde Stata guarda el periodo relativo)
    gen rowname = ""
    local names : rowfullnames M
    forvalues i = 1/`: word count `names'' {
        replace rowname = "`: word `i' of `names''" in `i'
    }

    * 4. Limpiar el periodo relativo (exp)
    * Stata los llama "tm3" para -3, "tp2" para +2, "t0" para 0
    gen exp = .
    replace exp = real(substr(rowname, 3, .)) if strpos(rowname, "tp") // Post
    replace exp = -real(substr(rowname, 3, .)) if strpos(rowname, "tm") // Pre
    replace exp = 0 if rowname == "t0" | rowname == "T0"

    * 5. Renombrar para que coincida con tu estructura
    rename b crime_index1
    rename se crime_index0
    rename ll lb
    rename ul ub

    * 6. Agregar el periodo de referencia (-1) que siempre es CERO
    set obs `=_N + 1'
    replace exp = -1 in L
    foreach var in crime_index1 crime_index0 lb ub {
        replace `var' = 0 in L
    }

    * 7. Limpieza final y exportación
    drop if missing(exp) // Eliminar filas extra de la matriz que no sean periodos
    sort exp
    keep exp crime_index1 crime_index0 lb ub
    
    list, noobs
	

	export delimited using "paraEventsStudySimpleCS_${panel}.csv", replace

restore
		
*********************************************************
*ESTUDIO DE EVENTOS
*********************************************************

preserve
	* 1. Año de primera entrada de OXXO
	bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
    gen rel_time = tq - first_treat

	* Leads (antes del tratamiento)
	forvalues k = 2/40 {
		gen lead`k' = (rel_time == -`k')
	}

	* Lags (después del tratamiento)
	forvalues k = 0/40 {
		gen lag`k' = (rel_time == `k')
	}
	
	* lista de variables para la regresión
	local evlist

	* leads (-15 a -2)
	forvalues k = 40(-1)2 {
		local evlist `evlist' lead`k'
	}

	* lags (0 a 15)
	forvalues k = 0/40 {
		local evlist `evlist' lag`k'
	}

	display "`evlist'"
		
	*check hard discound controls
	if $panel == 1 {
		xtreg crime_index ///
		 $day_controls $access_controls $harddiscount_controls ///
		`evlist' i.tq, fe vce(cluster codigo_upz)

	}
	else {
				xtreg crime_index ///
		  $access_controls $harddiscount_controls ///
		`evlist' i.tq, fe vce(cluster codigo_upz)

	}
	
	coefplot, keep(`evlist') ///
		xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
		ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
		mcolor(purple) title("Tasa de crimen") 

restore



preserve
	* 1. Año de primera entrada de OXXO
	bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))
	
	summarize crime_index if first_treat==2018 

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
    gen rel_time = tq - first_treat

	* Leads (antes del tratamiento)
	forvalues k = 2/40 {
		gen lead`k' = (rel_time == -`k')
	}

	* Lags (después del tratamiento)
	forvalues k = 0/40 {
		gen lag`k' = (rel_time == `k')
	}
	
	* lista de variables para la regresión
	local evlist

	* leads (-15 a -2)
	forvalues k = 40(-1)2 {
		local evlist `evlist' lead`k'
	}

	* lags (0 a 15)
	forvalues k = 0/40 {
		local evlist `evlist' lag`k'
	}

	display "`evlist'"
		

	xtreg crime_index ///
		`evlist' i.year, fe vce(cluster codigo_upz)

	*ssc install coefplot


	* Plot the coefficients using coefplot

	coefplot, keep(`evlist') ///
		xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
		ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
		mcolor(purple) title("Tasa de crimen") 
		
		
	 graph export "event_study_feoS_${panel}.png", replace

restore
