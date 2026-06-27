install.packages("haven")
install.packages("sf")
install.packages("ggplot2")
install.packages("dplyr")
install.packages("wesanderson")
# Cargar librerías
library(haven)   # leer archivos .dta
library(dplyr)   # manipulación de datos
library(ggplot2) # gráficos
library(sf)        # Para manejar datos geoespaciales
library(tidyverse)  # Para manipulación de datos y gráficos
library(wesanderson)

# --- Cargar datos ---

# Cambiar al directorio deseado
setwd("~/Desktop/1 economia/thesis_economics")

#este es para la intensidad del tratamiento

panelForIntensity <- read_dta("data/panel/first_treated_panel_R.dta")

# Ver las primeras filas
head(panelForIntensity)

# Ver nombres de columnas
names(panelForIntensity)

#quitar obseraciones del 2023
panelForIntensity <- panelForIntensity %>% filter(year < 2023)

#drop all observations if codigo_upz is = to any of these numbers 12 19 20 22 24 25 27 29 39 91 93 94 97 100 101 102 116
panelForIntensity <- panelForIntensity %>% filter(!codigo_upz %in% c(12, 19, 20, 22, 24, 25, 27, 29, 39, 91, 93, 94, 97, 100, 101, 102, 116))


panelForIntensity <- panelForIntensity %>%
  group_by(codigo_upz) %>%
  mutate(
    # Primero creamos una variable temporal que combine año y trimestre
    time_combined = year + (quarter - 1) / 4,
    
    # Calculamos el primer momento de tratamiento
    first_treat = if (any(dummy_oxxo == 1)) {
      min(time_combined[dummy_oxxo == 1]) 
    } else {
      NA_real_
    }
  ) %>%
  select(-time_combined) %>% # Borramos la temporal si no la necesitas
  ungroup()

panelForIntensity <- panelForIntensity %>% filter(!is.na(first_treat))


panelForIntensity_summary <- panelForIntensity %>%
  group_by(first_treat, rel_time) %>%
  summarise(
    cantidad_oxxo = mean(cantidad_oxxo, na.rm = TRUE),
    dummy_jb = mean(dummy_jb, na.rm = TRUE),
    dummy_d1 = mean(dummy_d1, na.rm = TRUE),
    dummy_ara = mean(dummy_ara, na.rm = TRUE),
    cantidad_jb = mean(cantidad_jb, na.rm = TRUE),
    cantidad_d1 = mean(cantidad_d1, na.rm = TRUE),
    cantidad_ara = mean(cantidad_ara, na.rm = TRUE)
  ) %>%
  ungroup()

# 5. Graficar con escala automática
p <- ggplot(panelForIntensity_summary, 
            aes(x = rel_time, y = cantidad_oxxo,
                group = first_treat,           # Agrupa para que geom_line sepa qué unir
                color = first_treat)) +        # Color como variable continua/numérica
  geom_line(linewidth = 0.8, alpha = 0.6) +         # alpha ayuda si las líneas se solapan
  geom_vline(xintercept = 0, linetype = "dashed", color = "black") +
  # Usamos una paleta profesional (Viridis es excelente para tesis)
  scale_color_gradientn(colours = wes_palette("Zissou1", 100, type = "continuous"), name = "Cohort")+
  labs(
    x = "Relative time (quarters)",
    y = "Mean quantity of OXXOs",
    title = "Treatment Intensity: Evolution of OXXO Quantity by Cohort",
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "right")

  print(p)

# Nota: Quitamos los 'shape' porque con 40 grupos los símbolos se amontonan

# Guardar el gráfico
ggsave(filename = "data/controles_results/graficas/oxxos_intensidad_tratamiento.png",
       plot = p,
       width = 8, height = 6, dpi = 300)
#title = "Evolución relativa de cantidad de OXXOs por cohorte",