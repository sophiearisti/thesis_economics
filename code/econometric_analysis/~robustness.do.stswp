*********************************************************
*version 4:analisis de controles y var dep
*********************************************************
* 1. Guardar la lista de números en una macro local llamada "mis_upz"

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
//global doc_panel "$dir_BDD_panel/panel_final_con_llamadas.csv"

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

duplicates list codigo_upz tq

duplicates drop codigo_upz tq, force

drop if year == 2023


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

//listar los always treated y esos tratar quitandolos o poniendolos como outliers


//1. Creamos una variable que marque con 1 a la UPZ si en 2015q1 ya tenía Oxxo
gen siempre_tratada = 0
replace siempre_tratada = 1 if tq == tq(2015q1) & dummy_oxxo == 1

* 2. Extendemos esa marca a todos los trimestres de esas mismas UPZ
by codigo_upz: egen max_siempre = max(siempre_tratada)

list codigo_upz if max_siempre == 1

* 3. Eliminamos por completo esas UPZ de la base de datos
drop if max_siempre == 1

* 4. Limpiamos las variables temporales que creamos
drop siempre_tratada max_siempre

//listar los always treated y esos tratar quitandolos o poniendolos como outliers


//mark the outliers in a variable
gen outliers = 0 


//replace outliers = 1 if codigo_upz == 97 | codigo_upz == 91 | codigo_upz == 93 | theft_to_people_index_eb > 400 

global crimes theft_to_vehicle theft_to_people theft_to_motorbike sexual homicide

//gen area_k2 = area_m2 / 1000000

foreach y of global crimes {
	
**# Bookmark #1
	
	* Log of raw count (levels + 1, to handle zeros)
	gen `y'_log_lvl_index = log(1 + `y')
	
	* Log of the population-based rate (levels + 1, to handle zeros)
	gen `y'_log_index = log(1 + `y'_index)
	
	* Count and print the number of observations where `y'_index == 0
	quietly count if `y'_index == 0
	local n_zero = r(N)
	
	quietly count
	local n_total = r(N)
	
	disp "`y'_index: `n_zero' zero observations out of `n_total' (" %4.1f 100*`n_zero'/`n_total' "%)"
}



***************************************************************
*REGRESIONES PARA LA ENTREGA
***************************************************************

cd "$dir_controls_results"

//global dep_var homicide_log_lvl_index theft_to_motorbike_log_lvl_index theft_to_people_log_lvl_index theft_to_vehicle_log_lvl_index sexual_log_lvl_index

global dep_var homicide_log_index theft_to_motorbike_log_index theft_to_people_log_index theft_to_vehicle_log_index sexual_log_index

global access_controls spillover_oxxo
 
global harddiscount_controls cantidad_d1 cantidad_ara cantidad_jb 

 
*********************************************************
*TWO WAY FIXED EFFECTS
*********************************************************
 
	
local first = 1

foreach y of global dep_var {

    if `first' == 1 {
		reghdfe `y' dummy_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
        local first = 0
		
    }
    else {
		
        reghdfe `y' dummy_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
    }
	
	//bacondecomp `y' dummy_oxxo outliers, ddetail vce(cluster codigo_upz)
}



preserve

	drop if year>2018
	
	reghdfe theft_to_people_log_index dummy_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

	outreg2 using tabla_regresiones_${panel}.xls, append label ///
	ctitle("TWFE ") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
	
		
	drop if tq != tq(2018q4)

	count if dummy_oxxo ==1

	count if dummy_oxxo ==0
	
	count
	
	sum theft_to_people_index if dummy_oxxo ==0

restore



preserve 

	drop if tq != tq(2022q4)

	
	count if dummy_oxxo ==1

	count if dummy_oxxo ==0
	
	count
	
	foreach y of global dep_var {
		sum `y'  if dummy_oxxo ==0
	}
	
restore



bysort dummy_oxxo: sum sexual_index



foreach y of global dep_var {

	
	reghdfe `y' dummy_oxxo $harddiscount_controls outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, NO)
	
	//bacondecomp `y' dummy_oxxo  $harddiscount_controls outliers, ddetail vce(cluster codigo_upz)


}



preserve

	drop if year>2018
	
	reghdfe theft_to_people_log_index dummy_oxxo outliers $harddiscount_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

	outreg2 using tabla_regresiones_${panel}.xls, append label ///
		ctitle("TWFE H") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
	//bacondecomp theft_to_people_index_eb dummy_oxxo outliers $harddiscount_controls, ddetail vce(cluster codigo_upz)

restore


*********************************************************
*SPILL OVER
*********************************************************
 


local first = 1

foreach y of global dep_var {

    //reg `y' dummy_oxxo

    if `first' == 1 {
		reghdfe `y' dummy_oxxo spillover_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_spill_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo spillover_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO)
		

        local first = 0
    }
    else {
        reghdfe `y' dummy_oxxo spillover_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_spill_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo spillover_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO)
		
    }
	
	//bacondecomp `y' dummy_oxxo outliers, ddetail vce(cluster codigo_upz)
}

preserve

	drop if year>2018
	
	reghdfe theft_to_people_index_eb dummy_oxxo outliers spillover_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

	outreg2 using tabla_regresiones_spill_${panel}.xls, append label ///
		ctitle("TWFE `y' spill") ///
		keep(dummy_oxxo spillover_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, SI)
		
	//bacondecomp theft_to_people_index_eb dummy_oxxo outliers $harddiscount_controls, ddetail vce(cluster codigo_upz)

restore


foreach y of global dep_var {

	
	reghdfe `y' dummy_oxxo $harddiscount_controls spillover_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_spill_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(dummy_oxxo spillover_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, SI)
	
}

preserve

	drop if year>2018
	
	reghdfe theft_to_people_index_eb $harddiscount_controls dummy_oxxo outliers spillover_oxxo ,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

	outreg2 using tabla_regresiones_spill_${panel}.xls, append label ///
		ctitle("TWFE `y' spill") ///
		keep(dummy_oxxo spillover_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, SI, Access controles, NO)
		
	//bacondecomp theft_to_people_index_eb dummy_oxxo outliers $harddiscount_controls, ddetail vce(cluster codigo_upz)

restore


*********************************************************
*TWO WAY FIXED EFFECTS INTENSITY OF TREATMENT
*********************************************************
 
local first = 1

foreach y of global dep_var {

    //reg `y' dummy_oxxo

    if `first' == 1 {
		reghdfe `y' cantidad_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_intensity_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(cantidad_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		

        local first = 0
    }
    else {
        reghdfe `y' cantidad_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_intensity_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(cantidad_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
    }
	
}



preserve

	drop if year>2018
	
	reghdfe theft_to_people_log_index  cantidad_oxxo outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_intensity_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(cantidad_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
		
	drop if tq != tq(2018q4)

	count if dummy_oxxo ==1

	count if dummy_oxxo ==0
	
	count
	
	sum theft_to_people_index if dummy_oxxo ==0

restore


preserve

drop if cantidad_oxxo ==0

sum theft_to_people_index

restore


preserve

drop if cantidad_oxxo !=0

sum theft_to_people_index

restore


foreach y of global dep_var {

	
	reghdfe `y' cantidad_oxxo $harddiscount_controls outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_intensity_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(cantidad_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, NO)

}


preserve


	drop if year>2018

	reghdfe theft_to_people_log_index cantidad_oxxo $harddiscount_controls outliers,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_intensity_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(cantidad_oxxo) ///
	addtext(Chain stores, SI,  Day controls, NO, Control spillover, NO)	
	
restore 


********************************************************
*C&S
*********************************************************

cd "$dir_controls_results/events study/CS/multiple"

global dep_var theft_to_motorbike_log_index //theft_to_people_log_index theft_to_vehicle_log_index sexual_log_index

foreach y of global dep_var {
	preserve

		di "`y'"
		
		if "`y'" == "theft_to_people_area_index" {
			di "Estrategia especial: Filtrando datos para Theft to People (Solo hasta 2018)"
			drop if year > 2018
		}
		
		* Let's first install drdid
		*ssc install drdid, all replace
		* Now let's install csdid
		*ssc install csdid, all replace

		* Asegúrate de tener la variable del año de tratamiento
		bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))
		replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

			* Ejecutar el método de Callaway & Sant'Anna
		csdid `y' $harddiscount_controls outliers, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz) notyet

		* Revisar los efectos promedio
		estat pretrend

		*ver el ATT
		estat simple
		
		* Guardar los resultados en una matriz
		matrix results = r(table)

		matrix list results
		
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
		
		graph export "event_study_csM_${panel}_`y'.png", replace width(1200) height(800)
		
		
		
		* 1. Estimar los efectos dinámicos (event study)
		estat event, window(-24 24) estore(cs1)

		* 2. Extraer resultados y transponer
		matrix M = r(table)'
		di "revisar"
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
		replace exp = real(substr(rowname, 3, .)) if strpos(rowname, "Tp") // Post
		replace exp = -real(substr(rowname, 3, .)) if strpos(rowname, "Tm") // Pre
		replace exp = 0 if rowname == "t0" | rowname == "T0"

		* 5. Renombrar para que coincida con tu estructura
		rename b `y'1
		rename se `y'0
		rename ll lb
		rename ul ub

		* 6. Agregar el periodo de referencia (-1) que siempre es CERO
		set obs `=_N + 1'
		replace exp = -1 in L
		foreach var in `y'1 `y'0 lb ub {
			replace `var' = 0 in L
		}

		* 7. Limpieza final y exportación
		drop if missing(exp) // Eliminar filas extra de la matriz que no sean periodos
		sort exp
		keep exp `y'1 `y'0 lb ub
		
		list, noobs
		

		export delimited using "paraEventsStudyMultipleCS_${panel}_`y'.csv", replace

	restore
}



cd "$dir_controls_results/events study/CS/simple"

foreach y of global dep_var {
	preserve

		di "`y'"
		
		if "`y'" == "theft_to_people_area_index" {
			di "Estrategia especial: Filtrando datos para Theft to People (Solo hasta 2018)"
			drop if year > 2018
		}
		
		* Let's first install drdid
		*ssc install drdid, all replace
		* Now let's install csdid
		*ssc install csdid, all replace

		* Asegúrate de tener la variable del año de tratamiento
		bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))
		replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

		* Ejecutar el método de Callaway & Sant'Anna
		csdid `y' outliers, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz) notyet

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
		
		graph export "event_study_csS_${panel}_`y'.png", replace width(1200) height(800)
		
		
		
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
		replace exp = real(substr(rowname, 3, .)) if strpos(rowname, "Tp") // Post
		replace exp = -real(substr(rowname, 3, .)) if strpos(rowname, "Tm") // Pre
		replace exp = 0 if rowname == "t0" | rowname == "T0"

		* 5. Renombrar para que coincida con tu estructura
		rename b `y'1
		rename se `y'0
		rename ll lb
		rename ul ub

		* 6. Agregar el periodo de referencia (-1) que siempre es CERO
		set obs `=_N + 1'
		replace exp = -1 in L
		foreach var in `y'1 `y'0 lb ub {
			replace `var' = 0 in L
		}

		* 7. Limpieza final y exportación
		drop if missing(exp) // Eliminar filas extra de la matriz que no sean periodos
		sort exp
		keep exp `y'1 `y'0 lb ub
		
		list, noobs
		

		export delimited using "paraEventsStudySimpleCS_${panel}_`y'.csv", replace

	restore

}
		
*********************************************************
*ESTUDIO DE EVENTOS
*********************************************************

cd "$dir_controls_results/events study/FE/multiple"

foreach y of global dep_var {
    preserve
        
        * 1. Filtro especial por datos temporales si aplica
        if "`y'" == "theft_to_people_area_index" {
            di "Estrategia especial: Filtrando datos para Theft to People (Solo hasta 2018)"
            drop if year > 2018
        }
        
        * 2. Año de primera entrada de OXXO
        bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))

        * 3. Quedarse solo con cohortes tratadas (Treated only)
        drop if missing(first_treat)

        * 4. Crear tiempo relativo
        gen rel_time = tq - first_treat

        * Generar Leads (antes del tratamiento)
        forvalues k = 2/24 {
            gen lead`k' = (rel_time == -`k')
        }

        * Generar Lags (después del tratamiento)
        forvalues k = 0/24 {
            gen lag`k' = (rel_time == `k')
        }
        
        * 5. Armar la lista ordenada de variables para la regresión
        local evlist
        forvalues k = 24(-1)2 {
            local evlist `evlist' lead`k'
        }
        forvalues k = 0/24 {
            local evlist `evlist' lag`k'
        }

        di "Corriendo xtreg para la variable: `y'"
            
        * 6. Ejecutar la estimación según las macros globales del panel
        if $panel == 1 {
            xtreg `y' $day_controls $access_controls $harddiscount_controls `evlist' i.tq, fe vce(cluster codigo_upz)
			
			* Mostrar en la consola
		}
        else {
            xtreg `y' $harddiscount_controls `evlist' i.tq outliers, fe vce(cluster codigo_upz)

        }
	
		matrix M = r(table)'
		
		* 2. Extraer el Coeficiente (fila 1) y el Error Estándar (fila 2) del primer Lag
		matrix list M
        
        * 7. Graficar con Coefplot (Opcional pero recomendado para control rápido)
        coefplot, keep(`evlist') ///
            xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
            ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
            mcolor(purple) title("Tasa de crimen `y'") 

        graph export "event_study_feoM_${panel}_`y'.png", replace

        * =====================================================================
        * ¡INICIA EL PROCESO DE EXTRACCIÓN Y LIMPIEZA DE MATRIZ PARA TWFE FEO!
        * =====================================================================
        
        * 8. Guardar la matriz de resultados de xtreg y transponerla
		
		matrix list M

        
        * 9. Limpiar memoria actual (el "preserve" del inicio protege tus datos)
        clear
        
        * Convertir matriz a variables en un dataset nuevo
        svmat M, names(col)
        
        * Obtener los nombres de las filas originales (lead24, lead23..., lag0...)
        gen rowname = ""
        local names : rowfullnames M
        forvalues i = 1/`: word count `names'' {
            replace rowname = "`: word `i' of `names''" in `i'
        }
        
        * 10. Procesar y traducir el periodo relativo numérico (exp)
        gen exp = .
        
        * Si el nombre de la fila contiene "lead", el periodo es negativo
        replace exp = -real(substr(rowname, 5, .)) if strpos(rowname, "lead")
        
        * Si el nombre de la fila contiene "lag", el periodo es positivo
        replace exp = real(substr(rowname, 4, .)) if strpos(rowname, "lag")
        
        * 11. Eliminar filas que no correspondan a los Leads o Lags (ej: controles o la constante)
        drop if missing(exp)
        
        * 12. Renombrar las columnas para mantener tus nombres dinámicos de crímenes
        rename b `y'1
        rename se `y'0
        rename ll lb
        rename ul ub
        
        * 13. AGREGAR EL PERIODO DE REFERENCIA (-1) EN CERO ABSOLUTO
        set obs `=_N + 1'
        replace exp = -1 in L
        foreach var in `y'1 `y'0 lb ub {
            replace `var' = 0 in L
        }
        
        * 14. Ordenar cronológicamente y limpiar
        sort exp
        keep exp `y'1 `y'0 lb ub
        
        * Mostrar en consola para verificar pretrends visualmente
        list exp `y'1 `y'0, noobs
        
        * 15. Exportar el CSV idéntico (cambiando el prefijo a MultipleFE para diferenciarlo de CS)
        export delimited using "paraEventsStudyMultipleFE_${panel}_`y'.csv", replace

    * Recupera el dataset original intacto para la siguiente variable del loop
    restore
}



cd "$dir_controls_results/events study/FE/simple"

foreach y of global dep_var {
    preserve
        
        * 1. Filtro especial por datos temporales si aplica
        if "`y'" == "theft_to_people_area_index" {
            di "Estrategia especial: Filtrando datos para Theft to People (Solo hasta 2018)"
            drop if year > 2018
        }
        
        * 2. Año de primera entrada de OXXO
        bysort codigo_upz: egen first_treat = min(cond(dummy_oxxo==1, tq, .))

        * 3. Quedarse solo con cohortes tratadas (Treated only)
        drop if missing(first_treat)

        * 4. Crear tiempo relativo
        gen rel_time = tq - first_treat

        * Generar Leads (antes del tratamiento)
        forvalues k = 2/24 {
            gen lead`k' = (rel_time == -`k')
        }

        * Generar Lags (después del tratamiento)
        forvalues k = 0/24 {
            gen lag`k' = (rel_time == `k')
        }
        
        * 5. Armar la lista ordenada de variables para la regresión
        local evlist
        forvalues k = 24(-1)2 {
            local evlist `evlist' lead`k'
        }
        forvalues k = 0/24 {
            local evlist `evlist' lag`k'
        }

        di "Corriendo xtreg para la variable: `y'"
            
     
        xtreg `y' `evlist' i.tq outliers, fe vce(cluster codigo_upz)

		
		
		matrix M = r(table)'
		
		* 2. Extraer el Coeficiente (fila 1) y el Error Estándar (fila 2) del primer Lag
		matrix list M
        
        * 7. Graficar con Coefplot (Opcional pero recomendado para control rápido)
        coefplot, keep(`evlist') ///
            xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
            ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
            mcolor(purple) title("Tasa de crimen `y'") 

        graph export "event_study_feoS_${panel}_`y'.png", replace

        * =====================================================================
        * ¡INICIA EL PROCESO DE EXTRACCIÓN Y LIMPIEZA DE MATRIZ PARA TWFE FEO!
        * =====================================================================
        
        * 8. Guardar la matriz de resultados de xtreg y transponerla
		
		matrix list M

        
        * 9. Limpiar memoria actual (el "preserve" del inicio protege tus datos)
        clear
        
        * Convertir matriz a variables en un dataset nuevo
        svmat M, names(col)
        
        * Obtener los nombres de las filas originales (lead24, lead23..., lag0...)
        gen rowname = ""
        local names : rowfullnames M
        forvalues i = 1/`: word count `names'' {
            replace rowname = "`: word `i' of `names''" in `i'
        }
        
        * 10. Procesar y traducir el periodo relativo numérico (exp)
        gen exp = .
        
        * Si el nombre de la fila contiene "lead", el periodo es negativo
        replace exp = -real(substr(rowname, 5, .)) if strpos(rowname, "lead")
        
        * Si el nombre de la fila contiene "lag", el periodo es positivo
        replace exp = real(substr(rowname, 4, .)) if strpos(rowname, "lag")
        
        * 11. Eliminar filas que no correspondan a los Leads o Lags (ej: controles o la constante)
        drop if missing(exp)
        
        * 12. Renombrar las columnas para mantener tus nombres dinámicos de crímenes
        rename b `y'1
        rename se `y'0
        rename ll lb
        rename ul ub
        
        * 13. AGREGAR EL PERIODO DE REFERENCIA (-1) EN CERO ABSOLUTO
        set obs `=_N + 1'
        replace exp = -1 in L
        foreach var in `y'1 `y'0 lb ub {
            replace `var' = 0 in L
        }
        
        * 14. Ordenar cronológicamente y limpiar
        sort exp
        keep exp `y'1 `y'0 lb ub
        
        * Mostrar en consola para verificar pretrends visualmente
        list exp `y'1 `y'0, noobs
        
        * 15. Exportar el CSV idéntico (cambiando el prefijo a MultipleFE para diferenciarlo de CS)
        export delimited using "paraEventsStudySimpleFE_${panel}_`y'.csv", replace

    * Recupera el dataset original intacto para la siguiente variable del loop
    restore
}


list codigo_upz theft_to_people_index_eb theft_to_people_area_index

drop if theft_to_people_index_eb < theft_to_people_area_index

list codigo_upz theft_to_people_index_eb theft_to_people_area_index 
histogram theft_to_people_index_eb

histogram theft_to_people_log_index

********************************************************************
* STEP 1: Skewness / distributional check
********************************************************************

sum theft_to_people_index_eb, detail
sum theft_to_people_log_index, detail
* Compare skewness stat: levels should be high (>1), log should be near 0

histogram theft_to_people_index_eb, name(hist_levels, replace) title("Levels")
histogram theft_to_people_log_index, name(hist_log, replace) title("Log")


********************************************************************
* STEP 2: Mean-variance relationship (core multiplicative-error test)
********************************************************************
* Multiplicative error => variance grows with square of the mean
* Additive error => variance roughly constant across the mean


egen mean_crime_upz = mean(theft_to_people_index_eb), by(codigo_upz)
egen sd_crime_upz   = sd(theft_to_people_index_eb),   by(codigo_upz)

preserve

duplicates drop codigo_upz, force

scatter sd_crime_upz mean_crime_upz, ///
    title("Mean-Variance Relationship") ///
    ytitle("SD of crime rate") xtitle("Mean crime rate")
* Add a fitted line to check if relationship is linear (~multiplicative)
* or flat (~additive)
lpoly sd_crime_upz mean_crime_upz, addplot(scatter sd_crime_upz mean_crime_upz)

restore

* Formal test: regress log(SD) on log(mean) -- slope near 1 supports
* multiplicative error (SD proportional to mean); slope near 0 supports additive
preserve

duplicates drop codigo_upz, force

gen log_mean = log(mean_crime_upz)

gen log_sd   = log(sd_crime_upz)

regress log_sd log_mean
* Check the slope coefficient on log_mean: near 1 = multiplicative signature

restore

********************************************************************
* STEP 3: Heteroscedasticity tests -- levels vs. log
********************************************************************
* Levels model

//ssc install xttest3
preserve

	drop if year>2018

	xtreg theft_to_people_log_index dummy_oxxo outliers i.tq, fe
	xttest3

		
	drop if tq != tq(2018q4)

	count if dummy_oxxo ==1

	count if dummy_oxxo ==0
	
	count
	
	sum theft_to_people_index if dummy_oxxo ==0

restore

preserve

	drop if year>2018
	
	xtreg theft_to_people_index_eb dummy_oxxo outliers i.tq, fe
	xttest3

		
	drop if tq != tq(2018q4)

	count if dummy_oxxo ==1

	count if dummy_oxxo ==0
	
	count
	
	sum theft_to_people_index if dummy_oxxo ==0

restore






