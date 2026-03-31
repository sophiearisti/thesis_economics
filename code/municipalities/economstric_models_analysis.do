//econometric analysis for municipalities (it's almost the same)

*********************************************************
*version 4:analisis de controles y var dep
*********************************************************

*--------------Directorios --------------------------------------------*
global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_BDD_panel "$global_dir/data/municipalities/panel"

global panel 2


global doc_panel "$dir_BDD_panel/panel_final_municipios_anual.csv"

import delimited "$doc_panel", clear

* Declarar el panel
xtset codigo_municipio year


xtdescribe


bysort codigo_municipio: gen anos_total = _N
list codigo_municipio if anos_total < 20

drop if codigo_municipio == 52000



replace crime_rate_per_100k_inhabitants = "0" if crime_rate_per_100k_inhabitants == "n" | crime_rate_per_100k_inhabitants == "inf"

destring crime_rate_per_100k_inhabitants, replace

reg crime_rate_per_100k_inhabitants dummy_oxxo




global harddiscount_controls cantidad_d1 cantidad_ara cantidad_jb 

reg crime_rate_per_100k_inhabitants dummy_oxxo $harddiscount_controls


reghdfe crime_rate_per_100k_inhabitants dummy_oxxo,  absorb(codigo_municipio i.year) vce(cluster codigo_municipio)

reghdfe crime_rate_per_100k_inhabitants dummy_oxxo $harddiscount_controls,  absorb(codigo_municipio i.year) vce(cluster codigo_municipio)

reghdfe crime_rate_per_100k_inhabitants cantidad_oxxo,  absorb(codigo_municipio i.year) vce(cluster codigo_municipio)

reghdfe crime_rate_per_100k_inhabitants cantidad_oxxo $harddiscount_controls,  absorb(codigo_municipio i.year) vce(cluster codigo_municipio)



bacondecomp crime_rate_per_100k_inhabitants dummy_oxxo, ddetail vce(cluster codigo_municipio)

bacondecomp crime_rate_per_100k_inhabitants dummy_oxxo $harddiscount_controls, ddetail vce(cluster codigo_municipio)


bacondecomp crime_rate_per_100k_inhabitants cantidad_oxxo, ddetail vce(cluster codigo_municipio)

bacondecomp crime_rate_per_100k_inhabitants cantidad_oxxo $harddiscount_controls, ddetail vce(cluster codigo_municipio)


preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort codigo_municipio: egen first_treat = min(cond(dummy_oxxo==1, year, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	if $panel == 1 {
		csdid crime_rate_per_100k_inhabitants $harddiscount_controls, ivar(codigo_municipio) time(year) gvar(first_treat) vce(cluster codigo_municipio)

	}
	else {
		csdid crime_rate_per_100k_inhabitants $harddiscount_controls, ivar(codigo_municipio) time(year) gvar(first_treat) vce(cluster codigo_municipio)

	}
	
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

	
restore


preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort codigo_municipio: egen first_treat = min(cond(dummy_oxxo==1, year, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para codigo_upzs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	csdid crime_rate_per_100k_inhabitants, ivar(codigo_municipio) time(year) gvar(first_treat) vce(cluster codigo_municipio)

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

restore


*********************************************************
*ESTUDIO DE EVENTOS
*********************************************************

preserve
	* 1. Año de primera entrada de OXXO
	bysort codigo_municipio: egen first_treat = min(cond(dummy_oxxo==1, year, .))

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
    gen rel_time = year - first_treat

	* Leads (antes del tratamiento)
	forvalues k = 2/20 {
		gen lead`k' = (rel_time == -`k')
	}

	* Lags (después del tratamiento)
	forvalues k = 0/20 {
		gen lag`k' = (rel_time == `k')
	}
	
	* lista de variables para la regresión
	local evlist

	* leads (-15 a -2)
	forvalues k = 20(-1)2 {
		local evlist `evlist' lead`k'
	}

	* lags (0 a 15)
	forvalues k = 0/20 {
		local evlist `evlist' lag`k'
	}

	display "`evlist'"
		

	xtreg crime_rate_per_100k_inhabitants ///
	$harddiscount_controls ///
	`evlist' i.year, fe vce(cluster codigo_municipio)


	
	coefplot, keep(`evlist') ///
		xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
		ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
		mcolor(purple) title("Tasa de crimen") 

restore

preserve
	* 1. Año de primera entrada de OXXO
	bysort codigo_municipio: egen first_treat = min(cond(dummy_oxxo==1, year, .))

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
    gen rel_time = year - first_treat

	* Leads (antes del tratamiento)
	forvalues k = 2/20 {
		gen lead`k' = (rel_time == -`k')
	}

	* Lags (después del tratamiento)
	forvalues k = 0/20 {
		gen lag`k' = (rel_time == `k')
	}
	
	* lista de variables para la regresión
	local evlist

	* leads (-15 a -2)
	forvalues k = 20(-1)2 {
		local evlist `evlist' lead`k'
	}

	* lags (0 a 15)
	forvalues k = 0/20 {
		local evlist `evlist' lag`k'
	}

	display "`evlist'"
		

	xtreg crime_rate_per_100k_inhabitants ///
	`evlist' i.year, fe vce(cluster codigo_municipio)


	
	coefplot, keep(`evlist') ///
		xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
		ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
		mcolor(purple) title("Tasa de crimen") 

restore


preserve

    * 2. Primer trimestre con OXXO por UPZ
    bysort codigo_municipio: egen first_treat = min(cond(dummy_oxxo==1, year, .))

    * 3. Mantener solo tratados
    drop if missing(first_treat)

    * 4. Tiempo relativo en trimestres
    gen rel_time = year - first_treat

    * 5. Colapsar
    collapse (mean)  cantidad_oxxo, by(first_treat rel_time)

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
			
	graph export "difference_in_oxxo_counts_panel_${panel}_over_time.png", replace

restore






