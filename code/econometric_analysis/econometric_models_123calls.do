*********************************************************
* version 1: 123 calls econometric analysis
*********************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_dofile "$global_dir/code" //dirección de los dofiles
global dir_dofile_controls_analysis "$dir_dofile/controls_maps_panel"
global dir_BDD_panel "$global_dir/data/panel"

global doc_panel "$dir_BDD_panel/panel_final_con_llamadas.csv"

import delimited "$doc_panel", clear


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

global dep_var tasa_total_atraco tasa_total_violacion_maltrato tasa_total_homicidio tasa_total_hurto

global access_controls spillover_oxxo
 
global harddiscount_controls cantidad_d1 cantidad_ara cantidad_jb 
	
local first = 1

foreach y of global dep_var {

    if `first' == 1 {
		reghdfe `y' dummy_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_123calls_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		

        local first = 0
    }
    else {
        reghdfe `y' dummy_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_123calls_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(dummy_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
    }
}


foreach y of global dep_var {

	
	reghdfe `y' dummy_oxxo $harddiscount_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_123calls_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(dummy_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, NO)
		
}


local first = 1

foreach y of global dep_var {

    //reg `y' dummy_oxxo

    if `first' == 1 {
		reghdfe `y' cantidad_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_123calls_intensity_${panel}.xls, replace label ///
		ctitle("TWFE `y'") ///
		keep(cantidad_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		

        local first = 0
    }
    else {
        reghdfe `y' cantidad_oxxo,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)

		outreg2 using tabla_regresiones_123calls_intensity_${panel}.xls, append label ///
		ctitle("TWFE `y'") ///
		keep(cantidad_oxxo) ///
		addtext(Chain stores, NO, Gender controles, NO, Day controls, NO, Control spillover, NO, Access controles, NO)
		
    }
}

foreach y of global dep_var {

	
	reghdfe `y' cantidad_oxxo $harddiscount_controls,  absorb(codigo_upz i.tq) vce(cluster codigo_upz)
	
		
	outreg2 using tabla_regresiones_123calls_intensity_${panel}.xls, append label ///
	ctitle("TWFE `y' H") ///
	keep(cantidad_oxxo) ///
	addtext(Chain stores, SI, Day controls, NO, Control spillover, NO)
		
	
}

********************************************************
*C&S
*********************************************************

cd "$dir_controls_results/events study/CS/multiple"

foreach y of global dep_var {
	preserve

		di "`y'"
		
		if "`y'" == "theft_to_people_index_eb" {
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
		csdid `y' $harddiscount_controls, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz) notyet

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
		
		graph export "event_study_csM_123calls_${panel}_`y'.png", replace width(1200) height(800)
		
		
		
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
		

		export delimited using "paraEventsStudyMultipleCS_123calls_${panel}_`y'.csv", replace

	restore
}


cd "$dir_controls_results/events study/CS/simple"

foreach y of global dep_var {
	preserve

		di "`y'"
		
		if "`y'" == "theft_to_people_index_eb" {
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
		csdid theft_to_people_index, ivar(codigo_upz) time(tq) gvar(first_treat) vce(cluster codigo_upz) notyet

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
		
		graph export "event_study_csS_123calls_${panel}_`y'.png", replace width(1200) height(800)
		
		
		
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
		

		export delimited using "paraEventsStudySimpleCS_123calls_${panel}_`y'.csv", replace

	restore

}

		
*********************************************************
*ESTUDIO DE EVENTOS
*********************************************************

cd "$dir_controls_results/events study/FE/multiple"

foreach y of global dep_var {
    preserve
        
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
            xtreg `y' $harddiscount_controls `evlist' i.tq, fe vce(cluster codigo_upz)

        }
	
		matrix M = r(table)'
		
		* 2. Extraer el Coeficiente (fila 1) y el Error Estándar (fila 2) del primer Lag
		matrix list M
        
        * 7. Graficar con Coefplot (Opcional pero recomendado para control rápido)
        coefplot, keep(`evlist') ///
            xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
            ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
            mcolor(purple) title("Tasa de crimen `y'") 

        graph export "event_study_feoM_123calls_${panel}_`y'.png", replace

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
        export delimited using "paraEventsStudyMultipleFE_123calls_${panel}_`y'.csv", replace

    * Recupera el dataset original intacto para la siguiente variable del loop
    restore
}

cd "$dir_controls_results/events study/FE/simple"


foreach y of global dep_var {
    preserve
        
        * 1. Filtro especial por datos temporales si aplica
        if "`y'" == "theft_to_people_index_eb" {
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
            
     
        xtreg `y' `evlist' i.tq, fe vce(cluster codigo_upz)

		
		
		matrix M = r(table)'
		
		* 2. Extraer el Coeficiente (fila 1) y el Error Estándar (fila 2) del primer Lag
		matrix list M
        
        * 7. Graficar con Coefplot (Opcional pero recomendado para control rápido)
        coefplot, keep(`evlist') ///
            xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
            ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
            mcolor(purple) title("Tasa de crimen `y'") 

        graph export "event_study_feoS_123calls_${panel}_`y'.png", replace

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
        export delimited using "paraEventsStudySimpleFE_123calls_${panel}_`y'.csv", replace

    * Recupera el dataset original intacto para la siguiente variable del loop
    restore
}



