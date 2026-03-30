gen t = yq(year, quarter)
format t %tq

gen first_oxxo = t if dummy_oxxo==1
bys codigo_upz: egen first_oxxo_upz = min(first_oxxo)
format first_oxxo_upz %tq

gen treated_after2015q1 = first_oxxo_upz > yq(2015,1)

bys codigo_upz: keep if _n==1
list codigo_upz first_oxxo_upz if treated_after2015q1==1

count if first_oxxo_upz == yq(2015,1)
