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

setwd("~/Desktop/1 economia/thesis_economics")

# --- Cargar datos --
#esta grafica será para hacer el event study bonito con colores lindos en diferentes tinalidades de morado
#es un csv
# 1. Tus vectores base
crimes <- c("homicide_area_index", 
            "theft_to_motorbike_area_index",
            "theft_to_people_area_index",
            "theft_to_vehicle_area_index",
            "sexual_area_index")


# 1. Definimos la función de limpieza
clean_names <- function(x) {
  tools::toTitleCase(gsub("_", " ", x))
}

# 3. Creamos el diccionario correctamente aplicando la función a las variables
crime_dict <- setNames(clean_names(crimes), crimes)


# 2. Definimos los componentes por separado para la permutación completa
tipos_metodo   <- c("CS", "FE")
carpetas_specs <- c("simple", "multiple")

# 3. ¡LA CLAVE! expand.grid ahora cruza TODO: 5 crímenes x 2 métodos x 2 especificaciones = 20 combinaciones
file_mapping_master <- expand.grid(
  crime  = crimes, 
  type   = tipos_metodo, 
  folder = carpetas_specs, 
  stringsAsFactors = FALSE
)

# 4. Agregamos de forma dinámica el prefijo de texto (Simple o Multiple) con la primera letra en mayúscula
file_mapping_master <- file_mapping_master %>%
  mutate(
    # Si la carpeta es "simple" -> regType es "Simple". Si es "multiple" -> "Multiple"
    regType = tools::toTitleCase(folder),
    
    # Construcción de la ruta de entrada exacta (Abarca CS Simple, CS Multiple, FE Simple y FE Multiple)
    archivo_entrada = paste0("data/controles_results/events study/", type, "/", folder, 
                             "/paraEventsStudy", regType, type, "_0_", crime, ".csv"),
    
    # Construcción de la ruta de salida exacta para el gráfico individual
    archivo_salida  = paste0("data/controles_results/events study/", type, "/", folder, 
                             "/events_study_lindo_", regType, type, "_0_robustness_", crime, ".png")
  )

for (i in 1:nrow(file_mapping_master)) {
  
  # Extraer datos de la fila actual
  crime_actual   <- file_mapping_master$crime[i]
  type_actual    <- file_mapping_master$type[i]
  regType_actual <- file_mapping_master$regType[i]
  ruta_in        <- file_mapping_master$archivo_entrada[i]
  ruta_out       <- file_mapping_master$archivo_salida[i]
  
  # Verificar si el archivo realmente existe en tu computador antes de abrirlo
  if (!file.exists(ruta_in)) {
    cat("Aviso: El archivo no existe, saltando ->", ruta_in, "\n")
    next
  }
  
  # 1. Leer dataframe dinámico
  event_study_data <- read.csv(ruta_in)
  
  # 2. Columnas dinámicas de Stata
  col_b  <- paste0(crime_actual, "1")
  col_se <- paste0(crime_actual, "0")
  
  # 3. Calcular intervalos si no venían listos
  event_study_data <- event_study_data %>%
    mutate(
      ymin = .data[[col_b]] - 1.96 * .data[[col_se]],
      ymax = .data[[col_b]] + 1.96 * .data[[col_se]]
    )
  
  # Título estético usando el diccionario
  titulo_crimen <- crime_dict[[crime_actual]]
  
  # 4. Calcular cortes del eje Y
  ymin_data <- min(event_study_data$ymin, na.rm = TRUE)
  ymax_data <- max(event_study_data$ymax, na.rm = TRUE)
  y_breaks  <- pretty(c(ymin_data, ymax_data), n = 5)
  y_labels  <- function(x) sprintf("%.4f", x)
  
  # 5. Diseñar el GGPLOT
  events <- event_study_data %>%
    ggplot(aes(x = exp, y = .data[[col_b]])) +
    geom_ribbon(aes(ymin = ymin, ymax = ymax), fill = "#FADBD8", alpha = 0.4) +
    geom_line(aes(y = ymax), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
    geom_line(aes(y = ymin), color = "#E6B0AA", linetype = "dotted", size = 0.8) +
    geom_line(color = "#8E44AD", size = 1) +
    geom_point(color = "#6C3483", size = 1.5) +
    geom_hline(yintercept = 0, color = "black", alpha = 0.5) +
    geom_vline(xintercept = -1, color = "black", linetype = "dashed", alpha = 0.5) +
    scale_y_continuous(breaks = y_breaks, labels = y_labels) +
    scale_x_continuous(breaks = seq(min(event_study_data$exp, na.rm = TRUE),
                                    max(event_study_data$exp, na.rm = TRUE), by = 2)) +
    theme_minimal(base_size = 14) +
    xlab("Time relative to OXXO arrival (Quarters before and after)") +
    ylab(titulo_crimen) +
    labs(title = paste0("Event Study (", type_actual, " - ", regType_actual, ")"),
         subtitle = titulo_crimen) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(color = "gray90"),
      plot.background = element_rect(fill = "white", color = NA)
    )
  
  print(events)
  
  # 6. Guardar el gráfico automáticamente en su carpeta correspondiente
  ggsave(filename = ruta_out, plot = events, width = 8, height = 6, dpi = 300)
  
  cat("¡Gráfico guardado con éxito en:", ruta_out, "!\n")
}


# Creamos las combinaciones de especificación (Simple con Simple, Multiple con Multiple)
especificaciones <- data.frame(
  regType = c("Simple", "Multiple"),
  folder  = c("simple", "multiple"),
  stringsAsFactors = FALSE
)

# Cruzamos cada crimen con cada nivel de especificación
grid_comparacion <- expand.grid(crime = crimes, folder = c("simple", "multiple"), stringsAsFactors = FALSE)

# Acoplamos el regType y armamos las rutas de archivos exactas
comparison_mapping <- grid_comparacion %>%
  left_join(especificaciones, by = "folder") %>%
  mutate(
    # Ruta CS: Usa su respectiva carpeta (simple o multiple) y su respectivo prefijo (SimpleCS o MultipleCS)
    ruta_cs = paste0("data/controles_results/events study/CS/", folder, "/paraEventsStudy", regType, "CS_0_", crime, ".csv"),
    
    # Ruta FE: Lo mismo, apuntando a su carpeta y prefijo correspondiente
    ruta_fe = paste0("data/controles_results/events study/FE/", folder, "/paraEventsStudy", regType, "FE_0_", crime, ".csv"),
    
    # Ruta del gráfico final comparado
    ruta_grafico_out = paste0("data/controles_results/events study/events_study_comparado_", folder, "_0_robustness_", crime, ".png")
  )


# Colores unificados
colores_metodo <- c("TWFE" = "#E75480", 
                    "CS" = "#8E44AD")

for (i in 1:nrow(comparison_mapping)) {
  
  crime_actual   <- comparison_mapping$crime[i]
  folder_actual  <- comparison_mapping$folder[i]
  regType_actual <- comparison_mapping$regType[i]
  file_cs        <- comparison_mapping$ruta_cs[i]
  file_fe        <- comparison_mapping$ruta_fe[i]
  file_out       <- comparison_mapping$ruta_grafico_out[i]
  
  # Verificación por si acaso algún modelo no se ha corrido en Stata
  if (!file.exists(file_cs) | !file.exists(file_fe)) {
    cat("Saltando:", crime_actual, "(", regType_actual, ") - Falta uno de los archivos CSV.\n")
    next
  }
  
  # 1. Cargar datos de la especificación actual
  data_cs <- read.csv(file_cs)
  data_fe <- read.csv(file_fe)
  
  col_b  <- paste0(crime_actual, "1")
  col_se <- paste0(crime_actual, "0")
  
  # 2. Estandarizar CS
  data_cs_clean <- data_cs %>%
    mutate(
      b      = .data[[col_b]],
      se     = .data[[col_se]],
      ymin   = b - 1.96 * se,
      ymax   = b + 1.96 * se,
      metodo = "CS"
    ) %>%
    select(exp, b, se, ymin, ymax, metodo)
  
  # 3. Estandarizar FE (Misma carpeta y especificación)
  data_fe_clean <- data_fe %>%
    mutate(
      b      = .data[[col_b]],
      se     = .data[[col_se]],
      ymin   = b - 1.96 * se,
      ymax   = b + 1.96 * se,
      metodo = "TWFE"
    ) %>%
    select(exp, b, se, ymin, ymax, metodo)
  
  # 4. Unir los datos para el gráfico espejo
  event_both <- bind_rows(data_cs_clean, data_fe_clean)
  
  # Título estético del crimen
  titulo_limpio <- crime_dict[[crime_actual]]
  
  # 5. Calcular límites del eje Y dinámicos combinados
  ymin_global <- min(event_both$ymin, na.rm = TRUE)
  ymax_global <- max(event_both$ymax, na.rm = TRUE)
  y_breaks    <- pretty(c(ymin_global, ymax_global), n = 5)
  y_labels    <- function(x) sprintf("%.4f", x)
  
  # 6. Construir el gráfico
  comparative_plot <- ggplot(event_both, aes(x = exp, y = b, color = metodo)) +
    geom_hline(yintercept = 0, color = "gray50", size = 0.6) +
    geom_vline(xintercept = -1, color = "black", linetype = "dashed", alpha = 0.7) +
    
    # Intervalos de confianza con Dodge para que no se pisen
    geom_errorbar(aes(ymin = ymin, ymax = ymax), width = 0.3, size = 0.8, 
                  position = position_dodge(width = 0.4)) +
    geom_point(size = 2, position = position_dodge(width = 0.4)) +
    geom_line(aes(group = metodo), size = 0.4, alpha = 0.4,
              position = position_dodge(width = 0.4)) +
    
    # Ejes
    scale_y_continuous(breaks = y_breaks, labels = y_labels) +
    scale_x_continuous(breaks = seq(min(event_both$exp, na.rm = TRUE),
                                    max(event_both$exp, na.rm = TRUE), by = 2)) +
    scale_color_manual(values = colores_metodo) +
    
    theme_minimal(base_size = 14) +
    xlab("Time relative to OXXO arrival (Quarters before and after)") +
    ylab(titulo_limpio) +
    labs(
      title = paste0("Methodology Comparison: ", titulo_limpio),
      subtitle = paste0("Specification type: ", regType_actual, " (", folder_actual, ")")
    ) +
    theme(
      legend.title = element_blank(),
      legend.position = "top",
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(color = "gray93"),
      plot.background = element_rect(fill = "white", color = NA)
    )
  
  print(comparative_plot)
  
  # 7. Guardar la imagen en su respectivo destino comparado
  ggsave(filename = file_out, plot = comparative_plot, width = 9, height = 6, dpi = 300)
  
  cat("¡Gráfico comparado guardado con éxito (", regType_actual, ") para:", crime_actual, "!\n")
}

for (i in 1:nrow(comparison_mapping)) {
  
  # Extraer datos de la fila actual del mapeo de comparación
  crime_actual   <- comparison_mapping$crime[i]
  folder_actual  <- comparison_mapping$folder[i]
  regType_actual <- comparison_mapping$regType[i]
  file_cs        <- comparison_mapping$ruta_cs[i]
  file_fe        <- comparison_mapping$ruta_fe[i]
  file_out       <- comparison_mapping$ruta_grafico_out[i]
  
  # Verificación por si acaso algún modelo no se ha corrido en Stata
  if (!file.exists(file_cs) | !file.exists(file_fe)) {
    cat("Saltando:", crime_actual, "(", regType_actual, ") - Falta uno de los archivos CSV.\n")
    next
  }
  
  # 1. Cargar datos de la especificación actual
  data_cs <- read.csv(file_cs)
  data_fe <- read.csv(file_fe)
  
  col_b  <- paste0(crime_actual, "1")
  col_se <- paste0(crime_actual, "0")
  
  # 2. Estandarizar CS con cálculo de intervalos planos
  data_cs_clean <- data_cs %>%
    mutate(
      b      = .data[[col_b]],
      se     = .data[[col_se]],
      ymin   = b - 1.96 * se,
      ymax   = b + 1.96 * se,
      metodo = "CS"
    ) %>%
    select(exp, b, se, ymin, ymax, metodo)
  
  # 3. Estandarizar FE (Misma carpeta y especificación)
  data_fe_clean <- data_fe %>%
    mutate(
      b      = .data[[col_b]],
      se     = .data[[col_se]],
      ymin   = b - 1.96 * se,
      ymax   = b + 1.96 * se,
      metodo = "TWFE"
    ) %>%
    select(exp, b, se, ymin, ymax, metodo)
  
  # 4. Unir los datos para el gráfico espejo
  event_both <- bind_rows(data_cs_clean, data_fe_clean)
  
  # Título estético del crimen usando tu diccionario
  titulo_limpio <- crime_dict[[crime_actual]]
  
  # 5. Calcular límites del eje Y dinámicos combinados
  ymin_global <- min(event_both$ymin, na.rm = TRUE)
  ymax_global <- max(event_both$ymax, na.rm = TRUE)
  y_breaks    <- pretty(c(ymin_global, ymax_global), n = 5)
  y_labels    <- function(x) sprintf("%.4f", x)
  
  # 6. Construir el gráfico con la estética exacta de la gráfica morada
  comparative_plot <- ggplot(event_both, aes(x = exp, y = b, color = metodo, fill = metodo)) +
    
    # Capa de sombreado (Ribbon) heredando el color del método con transparencia
    geom_ribbon(aes(ymin = ymin, ymax = ymax, group = metodo), alpha = 0.15, color = NA) +
    
    # Bordes superiores e inferiores punteados del intervalo (Dotted)
    geom_line(aes(y = ymax, group = metodo), linetype = "dotted", size = 0.6, alpha = 0.7) +
    geom_line(aes(y = ymin, group = metodo), linetype = "dotted", size = 0.6, alpha = 0.7) +
    
    # Líneas base de referencia macro
    geom_hline(yintercept = 0, color = "black", alpha = 0.5) +
    geom_vline(xintercept = -1, color = "black", linetype = "dashed", alpha = 0.5) +
    
    # Línea principal y puntos estimados
    geom_line(aes(group = metodo), size = 0.9) +
    geom_point(size = 1.8) +
    
    # Configuración de Ejes y Escalas
    scale_y_continuous(breaks = y_breaks, labels = y_labels) +
    scale_x_continuous(breaks = seq(min(event_both$exp, na.rm = TRUE),
                                    max(event_both$exp, na.rm = TRUE), by = 2)) +
    
    # Paletas de color personalizadas de tu script maestro
    scale_color_manual(values = colores_metodo) +
    scale_fill_manual(values = colores_metodo) +
    
    # Configuración del Tema Limpio (Igual al de tu ejemplo)
    theme_minimal(base_size = 14) +
    xlab("Time relative to OXXO arrival (Quarters before and after)") +
    ylab(titulo_limpio) +
    labs(
      title = paste0("Methodology Comparison: ", titulo_limpio),
      subtitle = paste0("Specification type: ", regType_actual, " (", folder_actual, ")")
    ) +
    theme(
      legend.title = element_blank(),
      legend.position = "top",
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(color = "gray90"),
      plot.background = element_rect(fill = "white", color = NA)
    )
  
  print(comparative_plot)
  
  # 7. Guardar la imagen con las dimensiones de tu setup anterior
  ggsave(filename = file_out, plot = comparative_plot, width = 9, height = 6, dpi = 300)
  
  cat("¡Gráfico comparado guardado con éxito estilo Ribbon (", regType_actual, ") para:", crime_actual, "!\n")
}