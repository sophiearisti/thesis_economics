# Cargar librerías
library(haven)   # leer archivos .dta
library(dplyr)   # manipulación de datos
library(ggplot2) # gráficos
library(sf)        # Para manejar datos geoespaciales
library(tidyverse)  # Para manipulación de datos y gráficos

# --- Cargar datos ---

# Cambiar al directorio deseado
setwd("~/Desktop/1 economia/thesis_economics")

####-----Mapa de Oxxos CON estaciones de transmilenio y vias principales-----########
# 1. Cargar los archivos 
upz_shp <- st_read("data/panel/upz-bogota/upz-bogota.shp")
vias_shp <- st_read("data/panel/vias_principales/RedInfraestructuraVialArterial.shp")
estaciones_tm <- st_read("data/panel/estaciones_transmilenio/Estaciones_Troncales_de_TRANSMILENIO.shp")
oxxo_shp <- st_read("data/maps_data/oxxo_points_2025/joined_geometry_tiendas.shp", 
                    options = "ENCODING=WINDOWS-1252")
# 2. ESTANDARIZAR PROYECCIONES (CRÍTICO)
# Para que las capas coincidan espacialmente, todas deben tener el mismo CRS.
# Usaremos Magna-Sirgas (EPSG:4326 o el específico de Bogotá 3116)
upz_shp <- st_transform(upz_shp, 4326)
vias_shp <- st_transform(vias_shp, 4326)
estaciones_tm <- st_transform(estaciones_tm, 4326)
oxxo_shp <- st_transform(oxxo_shp, 4326)


# 3. CREAR EL MAPA
ggplot() +
  # 1. Capa base (UPZ)
  geom_sf(data = upz_shp, fill = "gray95", color = "gray80", size = 0.2) +
  
  # 2. Vías principales - FORZAR LÍNEA EN LEYENDA
  geom_sf(data = vias_shp, aes(color = "Main Roads"), 
          size = 0.5, 
          key_glyph = "path") +
  
  # 3. Estaciones de Transmilenio
  geom_sf(data = estaciones_tm, aes(color = "Transmilenio Stations"), 
          size = 1.5, key_glyph = "point") + 
  
  # 4. Tiendas Oxxo
  geom_sf(data = oxxo_shp, aes(color = "Oxxo Stores"), 
          size = 1.5, shape = 18, key_glyph = "point") +
  
  # 5. Colores con códigos Hexadecimales
  scale_color_manual(values = c(
    "Main Roads" = "#969EB5",       # Gris
    "Transmilenio Stations" = "#6B0F1A", # Rojo TM
    "Oxxo Stores" = "#FF5340"             # Amarillo Oxxo
  )) +
  
  # 6. Zoom y Estética Limpia
  coord_sf(xlim = st_bbox(upz_shp)[c(1,3)], ylim = st_bbox(upz_shp)[c(2,4)], expand = FALSE) +
  labs(color = "Legend") +
  theme_minimal() +
  theme(
    axis.text = element_blank(),
    axis.ticks = element_blank(),
    panel.grid = element_blank(),
    legend.position = "right",
    # Ajuste opcional: hacer las líneas de la leyenda más largas
    legend.key.width = unit(1, "cm") 
  )

#guardar mapa
ggsave("data/controles_results/mapas/mapa_oxxos_transmilenio_vias.png", width = 8, height = 6)
