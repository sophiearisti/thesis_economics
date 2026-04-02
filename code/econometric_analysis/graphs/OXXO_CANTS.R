nstall.packages("haven")
install.packages("sf")
install.packages("ggplot2")
install.packages("dplyr")


# Cargar librerías
library(haven)   # leer archivos .dta
library(dplyr)   # manipulación de datos
library(ggplot2) # gráficos
library(sf)        # Para manejar datos geoespaciales
library(tidyverse)  # Para manipulación de datos y gráficos

# --- Cargar datos ---

# Cambiar al directorio deseado
setwd("~/Desktop/1 economia/thesis_economics")

oxxos <- read_dta("data/chains/bogota/oxxos.dta")

######################EVOLUCION DE LA CANTIDAD DE OXXOS A LO LARGO DE LOS AÑOS######################

# --- Preparar variables ---
oxxos <- oxxos %>%
  mutate(
    fecha_matricula = as.numeric(substr(fechadematrícula, 1, 4)),
    ultimo_ano = últimoañorenovado
  ) %>%
  select(fecha_matricula, ultimo_ano)

# --- Definir rango de años ---
inicio <- 2009
fin <- 2025
anos <- inicio:fin

# --- Contar Oxxos activos por año ---
conteo_oxxos <- sapply(anos, function(y) {
  sum(oxxos$fecha_matricula <= y & oxxos$ultimo_ano >= y, na.rm = TRUE)
})

# --- Crear data frame para graficar ---
df_plot <- data.frame(
  ano = anos,
  conteo = conteo_oxxos
)

#print conteo_oxxos in 2020
print(conteo_oxxos[which(anos == 2020)])
#print conteo_oxxos in 2025
print(conteo_oxxos[which(anos == 2025)])

ggplot(df_plot, aes(x = ano, y = conteo)) +
  geom_line(color = "grey", size = 1.2) +       # línea lila
  geom_point(color = "purple", size = 2) +        # círculos en cada año
  scale_y_continuous(breaks = seq(0, max(df_plot$conteo) + 50, by = 50)) +
  labs(
    title = "Evolucion de la cantidad de Oxxos por año en Bogotá",
    x = "Year",
    y = "Number of Oxxos"
  ) +
  theme_minimal()

ggsave("data/controles_results/graficas/oxxos_por_ano.png", width = 8, height = 5)

#################################### Ahora hacerlo a nivel Colombia ####################
oxxos <- read_csv("data/chains/raw_data/oxxos.csv")

#crear de Fecha de Matrícula una nueva columna con solo el año
oxxos <- oxxos %>%
  mutate(
    fecha_matricula = as.numeric(substr(`Fecha de Matrícula`, 1, 4)),
    ultimo_ano = as.numeric(substr(`Último año renovado`, 1, 4))
  ) %>%
  select(fecha_matricula, ultimo_ano)

head(oxxos)

# --- Contar Oxxos activos por año ---
conteo_oxxos <- sapply(anos, function(y) {
  sum(oxxos$fecha_matricula <= y & oxxos$ultimo_ano >= y, na.rm = TRUE)
})

# --- Crear data frame para graficar ---
df_plot <- data.frame(
  ano = anos,
  conteo = conteo_oxxos
)

ggplot(df_plot, aes(x = ano, y = conteo)) +
  geom_line(color = "grey", size = 1.2) +       # línea lila
  geom_point(color = "purple", size = 2) +        # círculos en cada año
  scale_y_continuous(breaks = seq(0, max(df_plot$conteo) + 50, by = 50)) +
  labs(
    title = "Evolucion de la cantidad de Oxxos por año en Colombia",
    x = "Año",
    y = "Cantidad de Oxxos"
  ) +
  theme_minimal()

ggsave("data/controles_results/graficas/oxxos_por_ano_col.png", width = 8, height = 5)
