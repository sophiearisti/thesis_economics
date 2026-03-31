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

##########################-----Mapa de Oxxos en Bogotá POR AÑO-----##########################

plot_oxxo_map <- function(year, geometry) {
  # Leer layer correspondiente al año
  gdf <- st_read(paste0("data/maps_data/gpkg_all_years/joined_all_",geometry,"_years.gpkg"),
                 layer = paste0("joined_", year))
  
  # Quitar ZAT 796 y 798 porque nunca son tratado y la verdad no se ve nada
  if (geometry == "zat") {
    # delete all zats that have codigo_upz as NA
    gdf <- gdf %>%
      filter(!is.na(codigo_upz))
    
    gdf <- gdf %>%
      filter(!ZAT %in% c(796, 798, 824, 822, 821, 820, 819, 812, 1845, 801, 811, 800, 810, 795, 791, 823,808))
    
  }
  
  # Crear columna para presencia/ausencia de Oxxo
  gdf <- gdf %>%
    mutate(presencia_oxxo = ifelse(cantidad_oxxo_x > 0, 1, 0))
  
  # Graficar mapa coroplético
  
  ggplot(gdf) +
    geom_sf(aes(fill = cantidad_oxxo_x), color = "white") +
    scale_fill_gradient(
      low = "#E2EEF3", high = "#28536B", 
      na.value = "grey90", 
      name = "Number of Oxxos"
    ) +
    guides(fill = guide_colorbar(barwidth = 15, barheight = 1)) +
    labs(title = paste0("Presence of Oxxos by ", geometry," in ", year)) +
    theme_void() +
    theme(
      legend.position = "bottom",
      plot.title = element_text(hjust = 0.5)
    )
}

#"Se quitaron ZAT 796 y 798 (zonas rurales o reservas naturales)

anos <- c(2009, 2011, 2015, 2019,2023, 2025)
geometries <- c("zat", "upz")

# Mapas por año
for (geometry in geometries) {
  for (y in anos) {
    print(plot_oxxo_map(y, geometry))
    ggsave(paste0("data/controles_results/mapas/mapa_oxxos_", geometry, "_", y, ".png"), width = 8, height = 6)
  }
}

plot_oxxo_binary_map <- function(year, geometry) {
  # Leer layer correspondiente al año
  gdf <- st_read(paste0("data/maps_data/gpkg_all_years/joined_all_", geometry, "_years.gpkg"),
                 layer = paste0("joined_", year), quiet = TRUE)
  
  # Filtros específicos para ZAT
  if (geometry == "zat") {
    gdf <- gdf %>% filter(!is.na(codigo_upz))
    excluded <- c(796, 798, 824, 822, 821, 820, 819, 812, 1845, 801, 811, 800, 810, 795, 791, 823, 808)
    gdf <- gdf %>% filter(!ZAT %in% excluded)
  }
  
  # 1. Crear columna FACTOR con etiquetas claras
  gdf <- gdf %>%
    mutate(presencia_oxxo = ifelse(cantidad_oxxo_x > 0, "Yes", "No"),
           presencia_oxxo = factor(presencia_oxxo, levels = c("Yes", "No")))
  
  # 2. Graficar con escala manual
  ggplot(gdf) +
    geom_sf(aes(fill = presencia_oxxo), color = "white", size = 0.1) +
    scale_fill_manual(
      values = c("Yes" = "#28536B", "No" = "#C5DCE7"), # Azul oscuro para presencia, claro para ausencia
      name = "Has Oxxo?",
      labels = c("Yes" = "Presence", "No" = "Absence")
    ) +
    labs(title = paste0("Presence of Oxxos by ", toupper(geometry), " in ", year)) +
    theme_void() +
    theme(
      legend.position = "bottom",
      plot.title = element_text(hjust = 0.5, face = "bold"),
      legend.title = element_text(size = 10),
      legend.text = element_text(size = 9)
    )
}

# Ejemplo: generar mapa binario para 2015
for (geometry in geometries) {
  for (y in anos) {
    print(plot_oxxo_binary_map(y, geometry))
    ggsave(paste0("data/controles_results/mapas/mapa_oxxos_binary_", geometry, "_", y, ".png"), width = 8, height = 6)
  }
}


plot_dep_map <- function(year, geometry, folder, depVar) {
  # Leer layer correspondiente al año
  gdf <- st_read(paste0("data/maps_data/",folder,"/joined_all_",geometry,"_years.gpkg"),
                 layer = paste0("joined_", year))
  
  # Quitar ZAT 796 y 798 porque nunca son tratados
  if (geometry == "zat") {
    # delete all zats that have codigo_upz as NA
    gdf <- gdf %>%
      filter(!is.na(codigo_upz))
    
    gdf <- gdf %>%
      filter(!ZAT %in% c(796, 798, 824, 822, 821, 820, 819, 812, 1845, 801, 811, 800, 810, 795, 791, 823,808))
    
  }
  
  #print columns
  print(colnames(gdf))
  # Convertir la columna a número
  # Usamos [[depVar]] para acceder al nombre contenido en la variable
  gdf$valor_mapa <- as.numeric(gdf[[depVar]])
  
  # Graficar mapa coroplético
  ggplot(gdf) +
    geom_sf(aes(fill = valor_mapa), color = "white") +
    scale_fill_gradient(
      low = "#C3D5C6", high = "#55775A", 
      na.value = "grey90", 
      name = "Crime rate per 10k inhabitants"
    ) +
    guides(fill = guide_colorbar(barwidth = 15, barheight = 1)) +
    labs(title = paste("Crime rate per 10k inhabitants by ", geometry, " in ", year)) +
    theme_void() +
    theme(
      legend.position = "bottom",
      plot.title = element_text(hjust = 0.5)
    )
}

periodos <- list(
  list(folder = "gpkg_2018_2023", anos = 2018:2023),
  list(folder = "gpkg_2015_2018", anos = 2015:2018, depVar = "crime_index")
)

geometries <- list(
  list(name = "upz", depVar = "crime_index"),
  list(name = "zat", depVar = "theft_to_people")
)

# 2. Recorremos con un bucle triple (Geometría -> Bloque -> Año)
for (geom in geometries) {
  for (periodo in periodos) {
    current_folder <- periodo$folder
    depVar <- geom$depVar
    
    for (y in periodo$anos) {
      # Generamos el mapa
      p <- plot_dep_map(y, geom$name, current_folder,depVar)
      print(p)
      
      # Guardamos con nombre dinámico para no sobrescribir
      file_name <- paste0("data/controles_results/mapas/mapa_", geom, "_", current_folder, "_", y, ".png")
      ggsave(file_name, plot = p, width = 8, height = 6)
    }
  }
}
