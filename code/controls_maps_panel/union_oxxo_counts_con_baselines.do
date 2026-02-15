* ------------------------------
* Cargar y limpiar zat_all_controls
* ------------------------------
import delimited "/Users/sophiaaristizabal/Desktop/1 economia/7/econometría avanzada/proyecto_econometria_avanzada/data/buffer_data/zat_all_controls.csv", clear
destring zat, replace   // convertir a numérico si es necesario

* Mantener solo la primera observación por zat
bysort zat: keep if _n==1

* Guardar limpio
save "zat_all_controls_clean.dta", replace

* ------------------------------
* Cargar oxxo_counts
* ------------------------------
import delimited "/Users/sophiaaristizabal/Desktop/1 economia/7/econometría avanzada/proyecto_econometria_avanzada/data/buffer_data/oxxo_counts.csv", clear
destring zat, replace   // convertir a numérico si es necesario
save "oxxo_counts_temp.dta", replace

* ------------------------------
* Hacer el merge
* ------------------------------
use "oxxo_counts_temp.dta", clear
merge m:1 zat using "zat_all_controls_clean.dta"

* Revisar resultados
tab _merge

* Mantener solo observaciones combinadas
keep if _merge==3
drop _merge

* Guardar dataset final
export delimited "../../data/buffer_data/tiendas_and_baselines.csv", replace
