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
  
  "~/Desktop/1 economia/thesis_economics/data/maps_data/gpkg_all_years/joined_all_stores_years_upz.gpkg"
  
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
geometries <- c("upz")

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
    title= "Total crimes "
  }
  else 
  {
    title= crime_dict[[depVar]]
    #codigo_upz 63 o 117 asignarles al depVar zero porque son valores muy extremos
    # 2. ASIGNAR CERO A VALORES EXTREMOS (UPZ 63 y 117)
    # Usamos sym(depVar) para que dplyr entienda que es el nombre de una columna dinámica
    gdf <- gdf %>%
      mutate(!!sym(depVar) := ifelse(codigo_upz %in% c(63, 117), 0, !!sym(depVar)))
    
  }

  gdf$valor_mapa <- as.numeric(gdf[[depVar]])
  
  print(paste("Plotting", depVar, "for", geometry, "in", year))
  #print head valor_mapa
  print(head(gdf$valor_mapa))
  
  # Graficar mapa coroplético
  ggplot(gdf) +
    geom_sf(aes(fill = valor_mapa), color = "white") +
    scale_fill_gradient(
      low = "#DAF1D0", high = "#DF2935", 
      na.value = "grey90", 
      name =""
    ) +
    guides(fill = guide_colorbar(barwidth = 15, barheight = 1)) +
    labs(title = paste(title," by ", geometry, " in ", year)) +
    theme_void() +
    theme(
      legend.position = "bottom",
      plot.title = element_text(hjust = 0.5)
    )
}

periodos <- list(
  list(folder = "gpkg_all_years", anos = 2015:2023)
)

geometries <- list(
  list(name = "upz", depVar = "theft_to_people_index_eb"),
  list(name = "upz", depVar = "theft_to_vehicle_index_eb"),
  list(name = "upz", depVar = "theft_to_motorbike_index_eb"),
  list(name = "upz", depVar = "sexual_index_eb"),
  list(name = "upz", depVar = "homicide_index_eb")
)

crimes <- c("theft_to_vehicle_index_eb", 
            "theft_to_people_index_eb", 
            "theft_to_motorbike_index_eb", 
            "sexual_index_eb", 
            "homicide_index_eb")

# 1. Diccionario estético para gráficos
clean_names <- tools::toTitleCase(gsub("_", " ", gsub("_eb", "", crimes)))
crime_dict  <- setNames(clean_names, crimes)

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
        file_name <- paste0("data/controles_results/mapas/mapa_", geom, "_", current_folder, "_", y,"_",depVar,".png")
        ggsave(file_name, plot = p, width = 8, height = 6)
        
      }
      

  }
  
}





oxxo_shp <- st_read("data/maps_data/oxxo_points_2025/joined_geometry_tiendas.shp", 
                    options = "ENCODING=WINDOWS-1252")
oxxo_shp <- st_transform(oxxo_shp, 4326)

#print head
print(head(oxxo_shp))
print (colnames(oxxo_shp))


plot_dep_map <- function(year, geometry, folder, depVar, oxxo_data) {
  # 1. Leer layer del año
  gdf <- st_read(paste0("data/maps_data/", folder, "/joined_all_", geometry, "_years.gpkg"),
                 layer = paste0("joined_", year), quiet = TRUE)
  
  # 2. Estandarizar Proyecciones
  gdf <- st_transform(gdf, 4326)
  oxxo_data <- st_transform(oxxo_data, 4326) # Asegurar misma proyección
  
  # 3. Filtros de ZAT y Títulos
  if (geometry == "zat") {
    gdf <- gdf %>% filter(!is.na(codigo_upz)) %>%
      filter(!ZAT %in% c(796, 798, 824, 822, 821, 820, 819, 812, 1845, 801, 811, 800, 810, 795, 791, 823, 808))
    main_title <- "Total crimes"
  } else if (depVar == "theft_to_people_index") {
    main_title <- "Theft to people crime rate per 10k inhabitants"
  } else {
    main_title <- "Crime rate per 10k inhabitants"
  }
  
  gdf$valor_mapa <- as.numeric(gdf[[depVar]])
  
  # 4. FILTRAR PUNTOS DE OXXO POR AÑO
  oxxos_current <- oxxo_data %>% 
    filter(lubridate::year(`Fecha.de.M`) <= year)
  
  # --- TRUCO DE ZOOM ---
  # Extraemos los límites de los polígonos (UPZ o ZAT)
  limites <- st_bbox(gdf)
  
  # 5. GRAFICAR
  ggplot() +
    # Capa de polígonos
    geom_sf(data = gdf, aes(fill = valor_mapa), color = "white", size = 0.1) +
    scale_fill_gradient(
      low = "#DAF1D0", high = "#DF2935", 
      na.value = "grey90", 
      name = main_title
    ) +
    # Capa de puntos
    geom_sf(data = oxxos_current, color = "#CA9502", size = 0.8, alpha = 0.8) + 
    
    # FORZAR EL ZOOM al área de los polígonos
    coord_sf(xlim = c(limites["xmin"], limites["xmax"]), 
             ylim = c(limites["ymin"], limites["ymax"]), 
             expand = FALSE) + # expand = FALSE evita márgenes extras
    
    guides(fill = guide_colorbar(barwidth = 15, barheight = 1)) +
    labs(title = paste(main_title, "by", toupper(geometry), "in", year),
         subtitle = "Yellow dots represent active Oxxo stores within the study area") +
    theme_void() +
    theme(
      legend.position = "bottom",
      plot.title = element_text(hjust = 0.5, face = "bold")
    )
}
# 2. Recorremos con un bucle triple (Geometría -> Bloque -> Año)
for (geom in geometries) {
  
  for (periodo in periodos) {
    
    current_folder <- periodo$folder
    depVar <- geom$depVar
    
    if(!(current_folder == "gpkg_2018_2023" & depVar == "crime_index"))
    {
      
      for (y in periodo$anos) {
        
        # Generamos el mapa
        p <- plot_dep_map(y, geom$name, current_folder,depVar, oxxo_shp)
        print(p)
        
        # Guardamos con nombre dinámico para no sobrescribir
        file_name <- paste0("data/controles_results/mapas/mapa_", geom, "_", current_folder, "_", y,"_",depVar,"_withoxxo",".png")
        ggsave(file_name, plot = p, width = 8, height = 6)
        
      }
      
    }
    
  }
  
}

