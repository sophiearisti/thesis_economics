from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
import os

#lista de nombres válidos para discriminar
nombres_valido_ara = ["TIENDA ARA","ARA", "TI4ENDA ARA", "TIENDA 0441 ARA"]
nombres_validos_d1 = ["D1", "MINI MERCADO D1", "MINIMERCADO", "TIENDA D1", "TIENDAS D1"]
nombres_validos_justo_y_bueno = ["JUSTO Y BUENO"]
nombres_validos_oxxo = ["OXXO"]
nombre_valido_lista = [nombres_valido_ara, nombres_validos_d1, nombres_validos_justo_y_bueno, nombres_validos_oxxo]

url_establecimiento_lista = [
    "https://rues.org.co/detalle/04/2161982",  # TIENDA ARA
    "https://rues.org.co/detalle/04/2305280",  # D1
    "https://rues.org.co/detalle/04/2608019",  # JUSTO Y BUENO
    "https://rues.org.co/detalle/04/1830322"   # OXXO
]

csv_file_establecimiento_lista = [
    "../../data/chains/raw_data/tienda_ara.csv",
    "../../data/chains/raw_data/d1.csv",
    "../../data/chains/raw_data/justo_y_bueno.csv",
    "../../data/chains/raw_data/oxxos.csv"
]


def webScrappingCadenas(url_establecimiento, csv_file_establecimiento,  nombre_valido_lista):
    print("Iniciando web scraping de cadenas...")
    
    # Configure Selenium
    options = Options()
    #options.add_argument("--headless")  
    # If you want to run in headless mode, uncomment the above line
    driver = webdriver.Chrome(options=options)

    url = url_establecimiento
    driver.get(url)

    # wait for the page to load
    wait = WebDriverWait(driver, 10)
    # click on the option "Establecimientos", this is a tab that shows the establishments
    # that the chain has
    tab = wait.until(EC.element_to_be_clickable((By.ID, "detail-tabs-tab-pestana_establecimientos")))
    driver.execute_script("arguments[0].click();", tab)

    time.sleep(3)  # wait for the dynamic content to load

    # Extract the page source after JavaScript has rendered the content
    soup = BeautifulSoup(driver.page_source, "html.parser")
    print(soup.prettify()[:1000])  # show the first 1000 characters for debugging

    # CSV file to save data
    csv_file = csv_file_establecimiento

    # if the csv file does not exist, create it and write the header
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Nombre", "Cámara de Comercio", "Número de Matrícula", "Fecha de Matrícula", 
                "Estado de la matrícula", "Fecha de renovación", "Último año renovado"
            ])

    # After showing that window, we must get all the information of the establishments
    while True:
        # obtain the accordion of the establishments
        accordion = wait.until(EC.presence_of_element_located((By.ID, "acordionEstablecimientos")))

        # Find all accordion buttons
        #the idea is to iterate over each of the accordion buttons
        buttons = accordion.find_elements(By.CLASS_NAME, "accordion-button")

        # Open CSV for saving data
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
                    
            # Go through each button to expand and extract data
            for i, button in enumerate(buttons):
                
                # Scroll hasta until the button and click
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1.5)  # esperar que abra el acordeón
                
                panel_id = button.get_attribute("data-bs-target").lstrip("#")
                wait.until(EC.visibility_of_element_located((By.ID, panel_id)))

                # Parse with BeautifulSoup the already expanded HTML
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Find the corresponding accordion
                acc = soup.find("div", id=panel_id)
                if not acc:
                    continue

                # Verify if the name is valid with base in the provided list
                # only check if the name contains any of the valid names
                if not any(valid_name in button.text.strip().upper() for valid_name in nombre_valido_lista):
                    continue  # skip this establishment if it's not valid

                # otherwise, if it's valid, extract the information
                nombre = button.text.strip()

                datos = {}
                for bloque in acc.select("div.registroapi"):
                    lab = bloque.select_one("p.registroapi__etiqueta")
                    val = bloque.select_one("p.registroapi__valor")
                    if lab and val:
                        datos[lab.get_text(strip=True)] = val.get_text(strip=True)

                camara          = datos.get("Cámara de Comercio", "-")
                matricula       = datos.get("Número de Matrícula", "-")
                fecha_matricula = datos.get("Fecha de Matrícula", "-")
                estado          = datos.get("Estado de la matrícula", "-")
                renovacion      = datos.get("Fecha de renovación", "-")
                ultimo          = datos.get("Último año renovado", "-")

                # Save the line in the CSV
                writer.writerow([nombre, camara, matricula, fecha_matricula, estado, renovacion, ultimo])
        # Try to go to the next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.page-link i.bi-chevron-right.green-color")
            parent_link = next_button.find_element(By.XPATH, "..")  # subir al <a>

            # Review if it's disabled (its <li> has class "disabled")
            li_parent = parent_link.find_element(By.XPATH, "..")
            if "disabled" in li_parent.get_attribute("class"):
                break  # we have reached the last page
            
            driver.execute_script("arguments[0].click();", parent_link)
            time.sleep(1)  # wait for the next page to load
        except:
            break


    driver.quit()

    print("Datos guardados en csv")
    
# Iterate over the lists to process each establishment
for url_establecimiento, csv_file_establecimiento, nombres_validos in zip(url_establecimiento_lista, csv_file_establecimiento_lista, nombre_valido_lista):
    
    webScrappingCadenas(url_establecimiento, csv_file_establecimiento,  nombres_validos)



