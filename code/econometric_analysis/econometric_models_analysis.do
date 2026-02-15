*********************************************************
*version 2:analisis de controles y var dep
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

***************************************************************
*REGRESIONES PARA LA ENTREGA
***************************************************************

*ssc install outreg2, replace

global panel_controls nivel_educativo_d9 nivel_educativo_d8 nivel_educativo_d7 nivel_educativo_d5 nivel_educativo_d4 nivel_educativo_d3 nivel_educativo_d2 nivel_educativo_d11 tipo_vivienda_d5 tipo_vivienda_d4 tipo_vivienda_d3 tipo_vivienda_d2
 
global controls cantidad_d1 cantidad_ara ingreso total_personas

*********************************************************
*MCO
*********************************************************

reg prop_independiente_total dummy_oxxo //if year==2023

outreg2 using tabla_regresiones.xls, replace label ctitle("MCO") keep(dummy_oxxo) addtext(Tiendas de cadena, NO, Controles variables, NO, Controles fijos, NO, Control spillover, NO) 

reg prop_independiente_total dummy_oxxo $controls $panel_controls //if year==2023

outreg2 using tabla_regresiones.xls, append label ctitle("MCO con controles") keep(dummy_oxxo) addtext(Tiendas de cadena, SI, Controles variables, SI, Controles fijos, SI, Control spillover, SI, Controles por diferencias, SI)  
 
*********************************************************
*TWO WAY FIXED EFFECTS
*********************************************************
xtset zat year

reghdfe prop_independiente_total dummy_oxxo,  absorb(zat i.year) vce(cluster zat)

outreg2 using tabla_regresiones.xls, append label ctitle("TWFE") keep(dummy_oxxo) addtext(Tiendas de cadena, NO, Controles variables, NO, Controles fijos, NO, Control spillover, NO, Controles por diferencias, SI)
 

bacondecomp prop_independiente_total dummy_oxxo, ddetail vce(cluster zat)

reghdfe prop_independiente_total dummy_oxxo $controls , absorb(zat i.year) vce(cluster zat)

outreg2 using tabla_regresiones.xls, append label ctitle("TWFE con controles") keep(dummy_oxxo)addtext(Tiendas de cadena, SI, Controles variables, SI, Controles fijos, NO, Control spillover, SI, Controles por diferencias, SI)  

bacondecomp prop_independiente_total dummy_oxxo $controls $panel_controls, ddetail vce(cluster zat)


*********************************************************
*C&S
*********************************************************

preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para ZATs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	csdid prop_independiente_total $controls $panel_controls, ivar(zat) time(year) gvar(first_treat) vce(cluster zat)

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
    addtext(Método, "CSDID", Controles, "Sí", Cluster, "ZAT")*/


	* Estimar los efectos dinámicos (event study)
	estat all

	* Graficar el event study	
	estat event, estore(cs1)
	csdid_plot, title("ES de CS")
	
	graph export "event_study_csS.png", replace width(1200) height(800)

	
		* 1. Estimar los efectos dinámicos (event study)
	estat event, window(-8 12) estore(cs1)

	* 2. Extraer resultados y transponer
	matrix M = r(table)'
	matrix list M

	* 3. Convertir matriz a dataset sin borrar memoria
	clear
	set obs 6

	* 4. Crear variables
	gen prop_independiente_total1 = .
	gen prop_independiente_total0 = .
	gen exp = .

	* NOTA: Usa la matriz M (no se borra porque la definiste ANTES del clear)
	* Rellena manualmente los 5 periodos (ajusta si son más)
	replace prop_independiente_total1 = M[3,1] in 1
	replace prop_independiente_total1 = M[4,1] in 2
	replace prop_independiente_total1 = M[5,1] in 3
	replace prop_independiente_total1 = M[6,1] in 4
	replace prop_independiente_total1 = M[7,1] in 5

	replace prop_independiente_total0 = M[3,2] in 1
	replace prop_independiente_total0 = M[4,2] in 2
	replace prop_independiente_total0 = M[5,2] in 3
	replace prop_independiente_total0 = M[6,2] in 4
	replace prop_independiente_total0 = M[7,2] in 5

	* 5. Definir los periodos relativos
	replace exp = -3 in 1
	replace exp = -2 in 2
	replace exp = 0  in 3
	replace exp = 1  in 4
	replace exp = 2  in 5

	* 6. Calcular intervalos de confianza
	gen lb = prop_independiente_total1 - 1.96*prop_independiente_total0
	gen ub = prop_independiente_total1 + 1.96*prop_independiente_total0

	* 7. Agregar fila base (exp = -1)
	replace exp = -1 in 6
	replace prop_independiente_total1 = 0 in 6
	replace prop_independiente_total0 = 0 in 6
	replace lb = 0 in 6
	replace ub = 0 in 6

	* 8. Mantener y exportar
	keep exp prop_independiente_total1 prop_independiente_total0 lb ub
	sort exp
	list, noobs

	export delimited using "paraEventsStudyMultipleCS.csv", replace
	
restore

preserve
	* Let's first install drdid
	*ssc install drdid, all replace
	* Now let's install csdid
	*ssc install csdid, all replace

	* Asegúrate de tener la variable del año de tratamiento
	bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))
	replace first_treat = 0 if missing(first_treat)  // 0 para ZATs nunca tratadas

	* Ejecutar el método de Callaway & Sant'Anna
	csdid prop_independiente_total, ivar(zat) time(year) gvar(first_treat) vce(cluster zat)

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
    addtext(Método, "CSDID", Controles, "Sí", Cluster, "ZAT")*/
	
	estat all

	* Graficar el event study	
	estat event, estore(cs1)
	csdid_plot, title("ES de CS")
	
	graph export "event_study_csM.png", replace width(1200) height(800)

	
	* 1. Estimar los efectos dinámicos (event study)
	estat event, window(-8 12) estore(cs1)

	* 2. Extraer resultados y transponer
	matrix M = r(table)'
	matrix list M

	* 3. Convertir matriz a dataset sin borrar memoria
	clear
	set obs 6

	* 4. Crear variables
	gen prop_independiente_total1 = .
	gen prop_independiente_total0 = .
	gen exp = .

	* NOTA: Usa la matriz M (no se borra porque la definiste ANTES del clear)
	* Rellena manualmente los 5 periodos (ajusta si son más)
	replace prop_independiente_total1 = M[3,1] in 1
	replace prop_independiente_total1 = M[4,1] in 2
	replace prop_independiente_total1 = M[5,1] in 3
	replace prop_independiente_total1 = M[6,1] in 4
	replace prop_independiente_total1 = M[7,1] in 5

	replace prop_independiente_total0 = M[3,2] in 1
	replace prop_independiente_total0 = M[4,2] in 2
	replace prop_independiente_total0 = M[5,2] in 3
	replace prop_independiente_total0 = M[6,2] in 4
	replace prop_independiente_total0 = M[7,2] in 5

	* 5. Definir los periodos relativos
	replace exp = -3 in 1
	replace exp = -2 in 2
	replace exp = 0  in 3
	replace exp = 1  in 4
	replace exp = 2  in 5

	* 6. Calcular intervalos de confianza
	gen lb = prop_independiente_total1 - 1.96*prop_independiente_total0
	gen ub = prop_independiente_total1 + 1.96*prop_independiente_total0

	* 7. Agregar fila base (exp = -1)
	replace exp = -1 in 6
	replace prop_independiente_total1 = 0 in 6
	replace prop_independiente_total0 = 0 in 6
	replace lb = 0 in 6
	replace ub = 0 in 6

	* 8. Mantener y exportar
	keep exp prop_independiente_total1 prop_independiente_total0 lb ub
	sort exp
	list, noobs

	export delimited using "paraEventsStudySimpleCS.csv", replace


restore
		
*********************************************************
*ESTUDIO DE EVENTOS
*********************************************************

preserve
	* 1. Año de primera entrada de OXXO
	bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)

	* 3. Crear tiempo relativo (en períodos de 4 años)
	gen rel_time = (year - first_treat)/4

	* Leads: periodos antes del tratamiento
	gen lead3 = (rel_time == -3)
	gen lead2 = (rel_time == -2)
	* Omitimos -1 como base

	* Lags: periodos después del tratamiento
	gen lag0 = (rel_time == 0)
	gen lag1 = (rel_time == 1)
	gen lag2 = (rel_time == 2)
	gen lag3 = (rel_time == 3)

	xtreg prop_independiente_total ///
		$controls $panel_controls ///
		lead3 lead2 lag0 lag1 lag2 lag3 i.year, fe vce(cluster zat)

	coefplot, keep(lead3 lead2 lag0 lag1 lag2 lag3) ///
		xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
		ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
		mcolor(purple) title("Prop. Trabajadores Independientes") 

restore



preserve
	* 1. Año de primera entrada de OXXO
	bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))
	
	summarize prop_independiente_total if first_treat==2023 

	* 2. Quedarse solo con cohortes tratadas
	drop if missing(first_treat)


	* 3. Crear tiempo relativo (en períodos de 4 años)
	gen rel_time = (year - first_treat)/4
	
	* Leads: periodos antes del tratamiento
	gen lead3 = (rel_time==-3)
	gen lead2 = (rel_time==-2)
	* Omitimos -1 como base

	* Lags: periodos después del tratamiento
	gen lag0 = (rel_time == 0)
	gen lag1 = (rel_time == 1)
	gen lag2 = (rel_time == 2)
	gen lag3 = (rel_time == 3)

	xtreg prop_independiente_total ///
		lead3 lead2 lag0 lag1 lag2 lag3 i.year, fe vce(cluster zat)

	*ssc install coefplot


* Plot the coefficients using coefplot


coefplot, keep(lead3 lead2 lag0 lag1 lag2 lag3) ///
	xlabel(, angle(vertical)) yline(0) vertical msymbol(E) mfcolor(white) ///
	ciopts(lwidth(*3) lcolor(purple*0.3)) mlabel format(%9.3f) ///
	mcolor(purple) title("Prop. Trabajadores Independientes") 
	
	
 graph export "event_study_feoS.png", replace

restore

	preserve
	*hacer el events study bonito

		* 1. Año de primera entrada de OXXO
		bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))

		* 2. Quedarse solo con cohortes tratadas
		drop if missing(first_treat)

		* 3. Crear tiempo relativo (en períodos de 4 años)
		gen rel_time = (year - first_treat)/4
		
		* Leads: periodos despues del tratamiento
		gen lead3 = (rel_time==3)
		gen lead2 = (rel_time==2)
		gen lead1 = (rel_time==1)
		gen lead0 = (rel_time==0)

		* Lags: periodos antes del tratamiento
		*gen lag1 = (rel_time==-1)
		gen lag2 = (rel_time==-2)
		gen lag3 = (rel_time==-3)

		xtset zat year
		
		xtreg prop_independiente_total i.year dummy_oxxo, fe vce(cluster zat)
		
		bacondecomp prop_independiente_total dummy_oxxo, ddetail vce(cluster zat)

		
		outreg2 using tabla_regresiones.xls, append label ctitle("ES TWFE") keep(dummy_oxxo) addtext(Tiendas de cadena, NO, Controles variables, NO, Controles fijos, NO, Control spillover, NO, Controles por diferencias, SI) 

		local DDL = _b[dummy_oxxo]
		local DD : display _b[dummy_oxxo]
		local DDSE : display  _se[dummy_oxxo]
		local DD1 = -0.10

		xi: xtreg prop_independiente_total lag3 lag2 lead0 lead1 lead2 lead3 i.year, fe vce(cluster zat)

			outreg2 using "./eventstudy_levels.xls", replace keep(lag3 lag2 lead0 lead1 lead2 lead3) noparen noaster addstat(DD, `DD', DDSE, `DDSE')
			
				outreg2 using "./eventstudy_levels_table.xls", replace label ctitle("ES TWFE") keep(lag3 lag2 lead0 lead1 lead2 lead3) noparen noaster addstat(DD, `DD', DDSE, `DDSE') addtext(Tiendas de cadena, NO, Controles variables, NO, Controles fijos, NO, Control spillover, NO, Controles por diferencias, SI) 


		*Pull in the ES Coefs
		xmluse "./eventstudy_levels.xls", clear cells(A3:B16) first

		replace VARIABLES = subinstr(VARIABLES,"lead","",.) 
		replace VARIABLES = subinstr(VARIABLES,"lag","",.)  
		quietly destring _all, replace ignore(",")

		replace VARIABLES = -3 in 2
		replace VARIABLES = -2 in 4
		replace VARIABLES = 0 in 6
		replace VARIABLES = 1 in 8
		replace VARIABLES = 2 in 10
		replace VARIABLES = 3 in 12

		drop in 1
		compress
		quietly destring _all, replace ignore(",")
		compress

		ren VARIABLES exp
		gen b = exp<.
		replace exp = -3 in 2 
		replace exp = -2 in 4
		replace exp = 0 in 6
		replace exp = 1 in 8
		replace exp = 2 in 10 
		replace exp = 3 in 12

		* Expand the dataset by one more observation so as to include the comparison year
		local obs =_N+1
		set obs `obs'
		for var _all: replace X = 0 in `obs'
		replace b = 1 in `obs'
		replace exp = -1 in `obs'
		keep exp prop_independiente_total b 
		set obs 14
		foreach x of varlist prop_independiente_total b {
			replace `x'= 0 in 14
			}
			
		replace exp= -1 in 14
		reshape wide prop_independiente_total, i(exp) j(b)

		cap drop *lb* *ub*
		gen lb = prop_independiente_total1 - 1.96*prop_independiente_total0 
		gen ub = prop_independiente_total1 + 1.96*prop_independiente_total0 

		* Create the picture
		set scheme s2color
		#delimit ;
		twoway (scatter prop_independiente_total1 ub lb exp , 
				lpattern(solid dash dash dot dot solid solid) 
				lcolor(gray gray gray red blue) 
				lwidth(thick medium medium medium medium thick thick)
				msymbol(i i i i i i i i i i i i i i i) msize(medlarge medlarge)
				mcolor(gray black gray gray red blue) 
				c(l l l l l l l l l l l l l l l) 
				cmissing(n n n n n n n n n n n n n n n n) 
				xline(-1, lcolor(black) lpattern(solid))
				yline(0, lcolor(black)) 
				xlabel(-3 -2 -1 0 1 2 3, labsize(medium))
				ylabel(, nogrid labsize(medium))
				xsize(7.5) ysize(5.5)           
				legend(off)
				xtitle("Años antes y después de la llegada de OXXO a un ZAT", size(medium))
				ytitle("proporción de independientes en el ZAT ", size(medium))
				graphregion(fcolor(white) color(white) icolor(white) margin(zero))
				yline(`DDL', lcolor(red) lwidth(thick)) text(`DD1' -0.10 "DD Coefficient = `DD' (s.e. = `DDSE')")
				)
		;

		#delimit cr;

		graph export "figura_eventsStudyS.png", replace width(2000)

		export delimited using "paraEventsStudySimple.csv", replace
	restore

preserve
	*hacer el events study bonito

		* 1. Año de primera entrada de OXXO
		bysort zat: egen first_treat = min(cond(dummy_oxxo==1, year, .))

		* 2. Quedarse solo con cohortes tratadas
		drop if missing(first_treat)

		* 3. Crear tiempo relativo (en períodos de 4 años)
		gen rel_time = (year - first_treat)/4
		
		* Leads: periodos despues del tratamiento
		gen lead3 = (rel_time==3)
		gen lead2 = (rel_time==2)
		gen lead1 = (rel_time==1)
		gen lead0 = (rel_time==0)

		* Lags: periodos antes del tratamiento
		*gen lag1 = (rel_time==-1)
		gen lag2 = (rel_time==-2)
		gen lag3 = (rel_time==-3)

		xtset zat year
		
		xtreg prop_independiente_total i.year $controls $panel_controls dummy_oxxo, fe vce(cluster zat)
		
		bacondecomp prop_independiente_total dummy_oxxo $controls $panel_controls, ddetail vce(cluster zat)
		
		outreg2 using tabla_regresiones.xls, append label ctitle("ES con controles TWFE") keep(dummy_oxxo) addtext(Tiendas de cadena, SI, Controles variables, SI, Controles fijos, NO, Control spillover, SI, Controles por diferencias, SI)

		local DDL = _b[dummy_oxxo]
		local DD : display _b[dummy_oxxo]
		local DDSE : display  _se[dummy_oxxo]
		local DD1 = -0.10

		xi: xtreg prop_independiente_total $controls $panel_controls lag3 lag2 lead0 lead1 lead2 lead3 i.year, fe vce(cluster zat)

		outreg2 using "./eventstudy_levels.xls", replace keep(lag3 lag2 lead0 lead1 lead2 lead3) noparen noaster addstat(DD, `DD', DDSE, `DDSE')
		
		outreg2 using "./eventstudy_levels_table.xls", append label ctitle("ES controles") keep(lag3 lag2 lead0 lead1 lead2 lead3) noparen noaster addstat(DD, `DD', DDSE, `DDSE') addtext(Tiendas de cadena, SI, Controles variables, SI, Controles fijos, NO, Control spillover, SI, Controles por diferencias, SI)


	*Pull in the ES Coefs
	xmluse "./eventstudy_levels.xls", clear cells(A3:B16) first

	replace VARIABLES = subinstr(VARIABLES,"lead","",.) 
	replace VARIABLES = subinstr(VARIABLES,"lag","",.)  
	quietly destring _all, replace ignore(",")

	replace VARIABLES = -3 in 2
	replace VARIABLES = -2 in 4
	replace VARIABLES = 0 in 6
	replace VARIABLES = 1 in 8
	replace VARIABLES = 2 in 10
	replace VARIABLES = 3 in 12

	drop in 1
	compress
	quietly destring _all, replace ignore(",")
	compress

	ren VARIABLES exp
	gen b = exp<.
	replace exp = -3 in 2 
	replace exp = -2 in 4
	replace exp = 0 in 6
	replace exp = 1 in 8
	replace exp = 2 in 10 
	replace exp = 3 in 12

	* Expand the dataset by one more observation so as to include the comparison year
	local obs =_N+1
	set obs `obs'
	for var _all: replace X = 0 in `obs'
	replace b = 1 in `obs'
	replace exp = -1 in `obs'
	keep exp prop_independiente_total b 
	set obs 14
	foreach x of varlist prop_independiente_total b {
		replace `x'= 0 in 14
		}
		
	replace exp= -1 in 14
	reshape wide prop_independiente_total, i(exp) j(b)

	cap drop *lb* *ub*
	gen lb = prop_independiente_total1 - 1.96*prop_independiente_total0 
	gen ub = prop_independiente_total1 + 1.96*prop_independiente_total0 

	* Create the picture
	set scheme s2color
	#delimit ;
	twoway (scatter prop_independiente_total1 ub lb exp , 
			lpattern(solid dash dash dot dot solid solid) 
			lcolor(gray gray gray red blue) 
			lwidth(thick medium medium medium medium thick thick)
			msymbol(i i i i i i i i i i i i i i i) msize(medlarge medlarge)
			mcolor(gray black gray gray red blue) 
			c(l l l l l l l l l l l l l l l) 
			cmissing(n n n n n n n n n n n n n n n n) 
			xline(-1, lcolor(black) lpattern(solid))
			yline(0, lcolor(black)) 
			xlabel(-3 -2 -1 0 1 2 3, labsize(medium))
			ylabel(, nogrid labsize(medium))
			xsize(7.5) ysize(5.5)           
			legend(off)
			xtitle("Años antes y después de la llegada de OXXO a un ZAT", size(medium))
			ytitle("proporción de independientes en el ZAT ", size(medium))
			graphregion(fcolor(white) color(white) icolor(white) margin(zero))
			yline(`DDL', lcolor(red) lwidth(thick)) text(`DD1' -0.10 "DD Coefficient = `DD' (s.e. = `DDSE')")
			)
	;

	#delimit cr;

	graph export "figura_eventsStudyC.png", replace width(2000)

	export delimited using "paraEventsStudyControls.csv", replace
restore

*********************************************************
*PSM con el ultimo tratado 2023
*********************************************************

/*drop if year != 2023


*mirar si hay diferencias significativas entre tratados y controles por medio de las covariables

global regresores accesibilidad_arterial num_est_transmi mujer limitaciones_fisicas ///
       cantidad_d1 estrato_mean cantidad_ara ingreso total_personas

reg dummy_oxxo $regresores , r

dprobit dummy_oxxo $regresores


sw, pe(.1): probit dummy_oxxo $regresores


global regresores_finales c.ingreso##c.ingreso c.estrato_mean##c.estrato_mean ///
       c.accesibilidad_arterial##c.num_est_transmi ///
       c.estrato_mean##c.cantidad_d1 c.estrato_mean##c.cantidad_ara mujer limitaciones_fisicas

//solo usamos las significativas
probit dummy_oxxo $regresores_finales

//$regresores 

drop propensity_score
predict propensity_score

bysort dummy_oxxo: sum propensity_score

histogram propensity_score, by(dummy_oxxo)


*PENDIENTE HACERLA CON R PARA QUE QUEDE BONITA
twoway ///
    (kdensity propensity_score if dummy_oxxo==0, lcolor(blue) lpattern(solid)) ///
    (kdensity propensity_score if dummy_oxxo==1, lcolor(red) lpattern(dash)), ///
    legend(label(1 "dummy_oxxo = 0") label(2 "dummy_oxxo = 1")) ///
    title("Distribuciones de PS por dummy_oxxo") ///
    xtitle("PS") ytitle("Densidad")
	
count if dummy_oxxo==1 & propensity_score>.8903806
*(SUPER BIEN PORQUE SOLO CON 4)

//todas dan no significativas, entonces muy bien
probit dummy_oxxo accesibilidad_arterial num_est_transmi mujer limitaciones_fisicas ///
       cantidad_d1 estrato_mean cantidad_ara ingreso total_personas propensity_score
	   
probit dummy_oxxo $regresores_finales propensity_score 

*************************************************************************************
*vamos a hacer la opcion 1, que es la basica
*************************************************************************************

set seed 123
drop orden
drawnorm orden
sort orden 

//ssc install psmatch2, replace

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) n(1) com noreplace ai(1)

psgraph

pstest $regresores, both graph


psmatch2 dummy_oxxo $regresores_finales, outcome(prop_independiente_total) n(1) com noreplace ai(1)

psgraph

pstest $regresores_finales, both graph



psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) n(2) com ai(1)

psgraph

pstest $regresores, both graph



psmatch2 dummy_oxxo $regresores_finales, outcome(prop_independiente_total) n(3) com ai(1)

psgraph

pstest $regresores_finales, both graph


*************************************************************************************
*vamos a hacer la opcion 2, que es CALLIPER
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) n(2) com ai(1) caliper(0.003)

psgraph

pstest $regresores, both graph


psmatch2 dummy_oxxo $regresores_finales, outcome(prop_independiente_total) n(2) com ai(1) caliper(0.00018)

psgraph

pstest $regresores_finales, both graph

*************************************************************************************
*vamos a hacer la opcion 3, que es la de RADIUS
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) radius caliper(0.0003) com ai(1)

psgraph

pstest $regresores, both graph

psmatch2 dummy_oxxo $regresores_finales, outcome(prop_independiente_total) radius caliper(0.00022) com ai(1)

psgraph

pstest $regresores_finales, both graph


*************************************************************************************
*vamos a hacer la opcion 4, que es la de KERNEL
*************************************************************************************
	   
*************************************************************************************
*KERNEL epan
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) kernel kerneltype(epan) bw(0.0003) com

psgraph

//estrato mean sigue siendo significativo
pstest $regresores, both graph


********************************* CON ESTA SI *****************************************
psmatch2 dummy_oxxo $regresores_finales, ///
    outcome(prop_independiente_total) kernel kerneltype(epan) bw(0.0001) common

psgraph

//estrato mean sigue siendo significativo
pstest $regresores_finales, both graph

*************************************************************************************
*KERNEL gauss: todo sigue siendo significivo
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) kernel kerneltype(normal) bw(0.0003) com

psgraph

//estrato mean sigue siendo significativo
pstest $regresores, both graph


*************************************************************************************
*KERNEL biweight: todo sigue siendo significivo
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) kernel kerneltype(biweight) bw(0.004) com

psgraph

//estrato mean sigue siendo significativo
pstest $regresores, both graph

********************************* CON ESTA SI *****************************************
psmatch2 dummy_oxxo $regresores_finales, ///
    outcome(prop_independiente_total) kernel kerneltype(biweight) bw(0.000171) common

psgraph

//estrato mean sigue siendo significativo
pstest $regresores_finales, both graph

*************************************************************************************
*KERNEL tricube: 
*************************************************************************************

psmatch2 dummy_oxxo $regresores, outcome(prop_independiente_total) kernel kerneltype( tricube) bw(0.0003) com

psgraph

//estrato mean sigue siendo significativo
pstest $regresores, both graph

********************************* CON ESTA SI *****************************************
psmatch2 dummy_oxxo $regresores_finales, ///
    outcome(prop_independiente_total) kernel kerneltype(tricube) bw(0.000175) common

psgraph

//estrato mean sigue siendo significativo
pstest $regresores_finales, both graph


*************************************************************************************
*vamos a hacer la opcion 4, que es la de IPW
*************************************************************************************

teffects ipw (prop_independiente_total) (dummy_oxxo $regresores, probit), ate vce(robust)

outreg2 using tabla_regresiones.xls, append dec(3) label ctitle("IPW") keep(dummy_oxxo) addtext(Tiendas de cadena, SI, Controles variables, NO, Controles fijos, SI, Control spillover, SI) 

teffects ipw (prop_independiente_total) (dummy_oxxo $regresores, probit), atet vce(robust)

//outreg2 using tabla_regresiones.xls, append dec(3) label ctitle("IPW") keep(dummy_oxxo) addtext(Tiendas de cadena, SI, Controles variables, NO, Controles fijos, SI, Control spillover, SI) 


logit dummy_oxxo $regresores
predict _ps, pr

gen double w_att = cond(dummy_oxxo==1, 1, _ps/(1-_ps))
gen double w_ate = cond(dummy_oxxo==1, 1/_ps, 1/(1-_ps))

reg prop_independiente_total i.dummy_oxxo [pw=w_att], robust
reg prop_independiente_total i.dummy_oxxo [pw=w_ate], robust



//con esta informacion hare literalmente las tablas para latex


*/


