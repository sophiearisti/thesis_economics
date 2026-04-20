install.packages("tidyverse")
install.packages("readxl")

library(tidyverse)
library(readxl)

# Función para limpiar los strings (quita paréntesis, asteriscos y espacios)
clean_num <- function(x) {
  as.numeric(gsub("[\\(\\)*[:space:]]", "", x))
}

# Diccionario de variables a procesar
variables_tesis <- c("theft_to_vehicle_index", "theft_to_people_index", 
                     "crime_index", "theft_to_motorbike_index", 
                     "sexual_index", "homicide_index", 
                     "male_index", "female_index")

# Modificamos ligeramente la función para que acepte la variable como parámetro
extraer_datos_v2 <- function(ruta, target_var) {
  df <- read_excel(ruta, col_names = FALSE, col_types = "text")
  fila_idx <- which(df[[1]] == target_var)
  
  if(length(fila_idx) == 0) return(NULL)
  
  # Limpieza de números
  clean <- function(x) as.numeric(gsub("[^0-9.-]", "", as.character(x)))
  
  val_diff <- clean(df[fila_idx, 7])
  val_se0  <- clean(df[fila_idx + 1, 3])
  val_se1  <- clean(df[fila_idx + 1, 5])
  
  # Extraer periodo
  year <- str_extract(basename(ruta), "(?<=_)20\\d{2}(?=_)")
  trim <- str_extract(basename(ruta), "(?<=_)T\\d(?=_)")
  periodo_label <- paste0(year, "_", trim)
  
  return(data.frame(
    periodo = periodo_label,
    diff = val_diff,
    lower = val_diff - (1.96 * sqrt(val_se0^2 + val_se1^2)),
    upper = val_diff + (1.96 * sqrt(val_se0^2 + val_se1^2)),
    variable = target_var
  ))
}

# --- BUCLE DE AUTOMATIZACIÓN ---

for (v in variables_tesis) {
  
  # 1. Extraer datos para la variable actual de TODOS los archivos
  dataset_temp <- map_df(archivos, ~extraer_datos_v2(.x, v)) %>% 
    arrange(periodo)
  
  if(nrow(dataset_temp) > 0) {
    
    # 2. Crear la gráfica
    p <- ggplot(dataset_temp, aes(x = periodo, y = diff, group = 1)) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "#F0544F") +
      geom_point(size = 3, color = "#9FC490") +
      geom_errorbar(aes(ymin = lower, ymax = upper), width = 0.2) +
      labs(title = paste("Means difference:", v),
           subtitle = "95% Confidence Interval",
           x = "Quarter", y = "Difference (Treated - Control)") +
      theme_minimal() +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
    
    # 3. Guardar con nombre dinámico
    nombre_archivo <- paste0("diff_means_", v, ".png")
    ruta_final <- file.path("~/Desktop/1 economia/thesis_economics/data/controles_results/graficas", nombre_archivo)
    
    ggsave(ruta_final, plot = p, width = 10, height = 6, dpi = 300, bg = "white")
    
    print(paste("Guardada:", nombre_archivo))
  }
}