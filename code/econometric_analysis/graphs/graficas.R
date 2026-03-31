install.packages("haven")
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

#este es para la intensidad del tratamiento

panelForIntensity <- read_dta("data/controles_results/paraR.dta")

# Ver las primeras filas
head(panelForIntensity)

# Ver nombres de columnas
names(panelForIntensity)

# 1. Año de primera entrada de OXXO por ZAT
panelForIntensity <- panelForIntensity %>%
  group_by(zat) %>%
  mutate(first_treat = if (any(dummy_oxxo == 1)) min(year[dummy_oxxo == 1]) else NA_real_) %>%
  ungroup()

panelForIntensity <- panelForIntensity %>% filter(!is.na(first_treat))

panelForIntensity <- panelForIntensity %>% mutate(rel_time = (year - first_treat) / 4)


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

# 5. Graficar cada cohorte
p <- ggplot(panelForIntensity_summary, 
       aes(x = rel_time, y = cantidad_oxxo,
           color = as.factor(first_treat),
           shape = as.factor(first_treat))) +   # <- aquí asignamos la forma
  geom_line(size = 1) +
  geom_point(size = 3) +                   # <- puntos visibles con forma
  geom_vline(xintercept = 0, linetype = "dashed") +
  scale_x_continuous(breaks = min(panelForIntensity_summary$rel_time):
                       max(panelForIntensity_summary$rel_time)) +
  labs(
    x = "Tiempo relativo (años/4)",
    y = "Promedio cantidad de OXXOs en ZAT",
    color = "Cohorte",
    shape = "Cohorte"
  ) +
  theme_minimal(base_size = 14) +
  scale_color_manual(values = c(
    "2011" = "#D7BDE2",  # lila claro
    "2015" = "#A569BD",  # morado medio
    "2019" = "#F5B7B1",  # rosa suave
    "2023" = "#7D3C98"   # morado intenso
  )) +
  scale_shape_manual(values = c(16,17,8,18))  # círculo, triángulo, estrella, diamante

# Guardar el gráfico
ggsave(filename = "data/controles_results/oxxos_intensidad_tratamiento.png",
       plot = p,
       width = 8, height = 6, dpi = 300)
#title = "Evolución relativa de cantidad de OXXOs por cohorte",



#esta grafica será para hacer el event study bonito con colores lindos en diferentes tinalidades de morado
#es un csv

event_study_data <- read.csv("data/controles_results/paraEventsStudyControls.csv")

head(event_study_data)

# calcular límites de confianza
event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0
  )

# valor del estimador
dd_val <- -0.0022

# calcular rango y marcas del eje y
ymin_data <- min(event_study_data$ymin, na.rm = TRUE)
ymax_data <- max(event_study_data$ymax, na.rm = TRUE)
y_breaks <- pretty(c(ymin_data, ymax_data), n = 5)
y_breaks <- sort(unique(c(y_breaks, dd_val)))
y_labels <- function(x) sprintf("%.4f", x)

# gráfico
events <- event_study_data %>%
  ggplot(aes(x = exp, y = prop_independiente_total1)) +
  
  # banda de confianza rosada
  geom_ribbon(aes(ymin = ymin, ymax = ymax), fill = "#FADBD8", alpha = 0.4) +
  
  # líneas punteadas en los bordes de la banda
  geom_line(aes(y = ymax), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  geom_line(aes(y = ymin), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  
  # línea y puntos principales (morado)
  geom_line(color = "#8E44AD", size = 1) +
  geom_point(color = "#6C3483", size = 2) +
  
  # línea horizontal del estimador DD
  geom_hline(yintercept = dd_val, color = "#E75480", linetype = "dashed", size = 1) +
  
  # eje y con 4 decimales
  scale_y_continuous(breaks = y_breaks, labels = y_labels) +
  
  # ejes y tema
  theme_minimal(base_size = 14) +
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  scale_x_continuous(
    breaks = seq(min(event_study_data$exp, na.rm = TRUE),
                 max(event_study_data$exp, na.rm = TRUE),
                 by = 1)
  ) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA),
    legend.title = element_blank(),
    legend.position = "top"
  )

# guardar imagen
ggsave(
  filename = "data/controles_results/events_study_lindo_controles.png",
  plot = events,
  width = 8, height = 6, dpi = 300
)


event_study_data <- read.csv("data/controles_results/paraEventsStudySimple.csv")

head(event_study_data)

# calcular límites de confianza
event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0
  )

# valor del estimador
dd_val <- -0.0206

# calcular rango y marcas del eje y
ymin_data <- min(event_study_data$ymin, na.rm = TRUE)
ymax_data <- max(event_study_data$ymax, na.rm = TRUE)
y_breaks <- pretty(c(ymin_data, ymax_data), n = 5)
y_breaks <- sort(unique(c(y_breaks, dd_val)))
y_labels <- function(x) sprintf("%.4f", x)

# gráfico
events <- event_study_data %>%
  ggplot(aes(x = exp, y = prop_independiente_total1)) +
  
  # banda de confianza rosada
  geom_ribbon(aes(ymin = ymin, ymax = ymax), fill = "#FADBD8", alpha = 0.4) +
  
  # líneas punteadas en los bordes de la banda
  geom_line(aes(y = ymax), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  geom_line(aes(y = ymin), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  
  # línea y puntos principales (morado)
  geom_line(color = "#8E44AD", size = 1) +
  geom_point(color = "#6C3483", size = 2) +
  
  # línea horizontal del estimador DD
  geom_hline(yintercept = dd_val, color = "#E75480", linetype = "dashed", size = 1) +
  
  # eje y con 4 decimales
  scale_y_continuous(breaks = y_breaks, labels = y_labels) +
  
  # ejes y tema
  theme_minimal(base_size = 14) +
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  scale_x_continuous(
    breaks = seq(min(event_study_data$exp, na.rm = TRUE),
                 max(event_study_data$exp, na.rm = TRUE),
                 by = 1)
  ) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA),
    legend.title = element_blank(),
    legend.position = "top"
  )

# guardar imagen
ggsave(
  filename = "data/controles_results/events_study_lindo_simple.png",
  plot = events,
  width = 8, height = 6, dpi = 300
)


# hacer el estudio de eventos bonito para CS

event_study_data <- read.csv("data/controles_results/paraEventsStudyMultipleCS.csv")

head(event_study_data)

# calcular límites de confianza
event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0
  )

# valor del estimador
dd_val <- 0.0014346

# calcular rango y marcas del eje y
ymin_data <- min(event_study_data$ymin, na.rm = TRUE)
ymax_data <- max(event_study_data$ymax, na.rm = TRUE)
y_breaks <- pretty(c(ymin_data, ymax_data), n = 5)
y_breaks <- sort(unique(c(y_breaks, dd_val)))
y_labels <- function(x) sprintf("%.4f", x)

# gráfico
events <- event_study_data %>%
  ggplot(aes(x = exp, y = prop_independiente_total1)) +
  
  # banda de confianza rosada
  geom_ribbon(aes(ymin = ymin, ymax = ymax), fill = "#FADBD8", alpha = 0.4) +
  
  # líneas punteadas en los bordes de la banda
  geom_line(aes(y = ymax), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  geom_line(aes(y = ymin), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  
  # línea y puntos principales (morado)
  geom_line(color = "#8E44AD", size = 1) +
  geom_point(color = "#6C3483", size = 2) +
  
  # línea horizontal del estimador DD
  geom_hline(yintercept = dd_val, color = "#E75480", linetype = "dashed", size = 1) +
  
  # eje y con 4 decimales
  scale_y_continuous(breaks = y_breaks, labels = y_labels) +
  
  # ejes y tema
  theme_minimal(base_size = 14) +
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  scale_x_continuous(
    breaks = seq(min(event_study_data$exp, na.rm = TRUE),
                 max(event_study_data$exp, na.rm = TRUE),
                 by = 1)
  ) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA),
    legend.title = element_blank(),
    legend.position = "top"
  )

# guardar imagen
ggsave(
  filename = "data/controles_results/events_study_lindo_controles_CS.png",
  plot = events,
  width = 8, height = 6, dpi = 300
)

# hacer el estudio de eventos bonito para CS sin controles

event_study_data <- read.csv("data/controles_results/paraEventsStudySimpleCS.csv")

head(event_study_data)

# calcular límites de confianza
event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0
  )

# valor del estimador
dd_val <- -0.0214422 

# calcular rango y marcas del eje y
ymin_data <- min(event_study_data$ymin, na.rm = TRUE)
ymax_data <- max(event_study_data$ymax, na.rm = TRUE)
y_breaks <- pretty(c(ymin_data, ymax_data), n = 5)
y_breaks <- sort(unique(c(y_breaks, dd_val)))
y_labels <- function(x) sprintf("%.4f", x)

# gráfico
events <- event_study_data %>%
  ggplot(aes(x = exp, y = prop_independiente_total1)) +
  
  # banda de confianza rosada
  geom_ribbon(aes(ymin = ymin, ymax = ymax), fill = "#FADBD8", alpha = 0.4) +
  
  # líneas punteadas en los bordes de la banda
  geom_line(aes(y = ymax), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  geom_line(aes(y = ymin), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
  
  # línea y puntos principales (morado)
  geom_line(color = "#8E44AD", size = 1) +
  geom_point(color = "#6C3483", size = 2) +
  
  # línea horizontal del estimador DD
  geom_hline(yintercept = dd_val, color = "#E75480", linetype = "dashed", size = 1) +
  
  # eje y con 4 decimales
  scale_y_continuous(breaks = y_breaks, labels = y_labels) +
  
  # ejes y tema
  theme_minimal(base_size = 14) +
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  scale_x_continuous(
    breaks = seq(min(event_study_data$exp, na.rm = TRUE),
                 max(event_study_data$exp, na.rm = TRUE),
                 by = 1)
  ) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA),
    legend.title = element_blank(),
    legend.position = "top"
  )

# guardar imagen
ggsave(
  filename = "data/controles_results/events_study_lindo_simple_CS.png",
  plot = events,
  width = 8, height = 6, dpi = 300
)



#unir los estudios de eventos en un solo grafico twfe y cs sin controles
event_study_dataCS <- read.csv("data/controles_results/paraEventsStudySimpleCS.csv")
event_study_data <- read.csv("data/controles_results/paraEventsStudySimple.csv")

# --- Cargar los datos
event_study_dataCS <- read.csv("data/controles_results/paraEventsStudySimpleCS.csv")
event_study_data   <- read.csv("data/controles_results/paraEventsStudySimple.csv")

# --- Calcular los límites de confianza para cada dataset
event_study_dataCS <- event_study_dataCS %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0,
    metodo = "Callaway & Sant’Anna (CS-DID)"
  )

event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0,
    metodo = "TWFE tradicional"
  )

# --- Unir ambos datasets
event_both <- bind_rows(event_study_data, event_study_dataCS)

# --- Elegir colores
colores <- c("TWFE tradicional" = "#E75480",          # rosado fuerte
             "Callaway & Sant’Anna (CS-DID)" = "#8E44AD")  # morado

# --- Crear gráfico con barras de error
ggplot(event_both, aes(x = exp, y = prop_independiente_total1, color = metodo)) +
  
  # Barras de error
  geom_errorbar(aes(ymin = ymin, ymax = ymax), width = 0.2, size = 0.8, position = position_dodge(width = 0.3)) +
  
  # Línea y puntos
  geom_point(size = 2, position = position_dodge(width = 0.3)) +
  
  # Ejes y etiquetas
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  
  # Línea base
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  
  # Colores personalizados
  scale_color_manual(values = colores) +
  
  # Tema
  theme_minimal(base_size = 14) +
  theme(
    legend.title = element_blank(),
    legend.position = "top",
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA)
  )

ggsave("data/controles_results/events_study_comparadoS.png",
       width = 8, height = 6, dpi = 300)


#unir los estudios de eventos en un solo grafico twfe y cs con controles

# --- Cargar los datos
event_study_dataCS <- read.csv("data/controles_results/paraEventsStudyMultipleCS.csv")
event_study_data   <- read.csv("data/controles_results/paraEventsStudyControls.csv")

# --- Calcular los límites de confianza para cada dataset
event_study_dataCS <- event_study_dataCS %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0,
    metodo = "Callaway & Sant’Anna (CS-DID)"
  )

event_study_data <- event_study_data %>%
  mutate(
    ymin = prop_independiente_total1 - 1.96 * prop_independiente_total0,
    ymax = prop_independiente_total1 + 1.96 * prop_independiente_total0,
    metodo = "TWFE tradicional"
  )

# --- Unir ambos datasets
event_both <- bind_rows(event_study_data, event_study_dataCS)

# --- Elegir colores
colores <- c("TWFE tradicional" = "#E75480",          # rosado fuerte
             "Callaway & Sant’Anna (CS-DID)" = "#8E44AD")  # morado

# --- Crear gráfico con barras de error
ggplot(event_both, aes(x = exp, y = prop_independiente_total1, color = metodo)) +
  
  # Barras de error
  geom_errorbar(aes(ymin = ymin, ymax = ymax), width = 0.2, size = 0.8, position = position_dodge(width = 0.3)) +
  
  # Línea y puntos
  geom_point(size = 2, position = position_dodge(width = 0.3)) +
  
  # Ejes y etiquetas
  xlab("Años relativos (año/4) antes y después de la llegada de OXXO a un ZAT") +
  ylab("Proporción de independientes en el ZAT") +
  
  # Línea base
  geom_hline(yintercept = 0, color = "black") +
  geom_vline(xintercept = -1, color = "black") +
  
  # Colores personalizados
  scale_color_manual(values = colores) +
  
  # Tema
  theme_minimal(base_size = 14) +
  theme(
    legend.title = element_blank(),
    legend.position = "top",
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA)
  )

ggsave("data/controles_results/events_study_comparadoM.png",
       width = 8, height = 6, dpi = 300)

