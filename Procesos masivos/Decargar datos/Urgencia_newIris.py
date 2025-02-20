from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys

# --- Recibir fechas desde argumentos ---
#if len(sys.argv) != 3:
#    print("Uso: script.py <fecha_inicio> <fecha_fin>")
#    sys.exit(1)
#
#fecha_inicio = sys.argv[1]
#fecha_fin = sys.argv[2]
#
#print(f"Usando fechas: {fecha_inicio} - {fecha_fin}")

fecha_inicio = "15/09/2025"
fecha_fin = "21/09/2025"


# --- Configuración del directorio de descargas ---
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Configuración del driver con opciones para establecer el directorio de descargas
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)



# --- Inicio de sesión en la página ---
driver.get("https://iris.rayenaps.cl/")
wait = WebDriverWait(driver, 20)
time.sleep(10)

# Ingresar usuario
username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
username_input.clear()
#username_input.send_keys("14092485-7")
username_input.send_keys("10024485-3")
time.sleep(1)
# Ingresar contraseña
password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
password_input.clear()
#password_input.send_keys("David.2025")
password_input.send_keys("Ignavi24")
time.sleep(1)
# Clic en "Ingresar"
ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
ingresar_button.click()
#time.sleep(10)
# Seleccionar licencia
#select_div = wait.until(EC.element_to_be_clickable(
#    (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
#))
#time.sleep(1)
#select_div.click()
#
#menu_item = wait.until(EC.element_to_be_clickable(
#    (By.XPATH,
#    #"//li[@data-value='1130' and contains(.,'SAPU Condores de Chile S.S. Metropolitano Sur')]")
#    "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
#))
#time.sleep(1)
#menu_item.click()
#time.sleep(1)

#confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
#time.sleep(1)
#confirmar_button.click()

time.sleep(30)

# --- Función para modificar el campos ---

def modificar_fechas(driver, wait, nombre_campo, valor):
    # Espera a que el elemento con el atributo name igual a nombre_campo sea visible
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    # Utiliza execute_script para asignar el nuevo valor al input
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor
    )

def modificar_nombre_centro(driver, wait, nombre_campo, valor):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),  # Corregido aquí
        valor
    )

# --- Variables ---

reportes = [
         {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677", "set" : "urgencias"},
         {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=1110","set" : "urgencias"},
         {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=673","set" : "urgencias"}, # TIEMPOS
         {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=520", "set" : "urgencias"}, #ADMITIDOS
         {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=810","set" : "urgencias"} #GES
]

centros = [
    {"tipo": "urgencias", "nombre": "SAR Haydeé López Casoou"},
    {"tipo": "urgencias", "nombre": "SAPU Dr. Carlos Lorca"},
    {"tipo": "urgencias", "nombre": "SAPU Condores de Chile"},
    {"tipo": "urgencias", "nombre": "SAPU Santa Laura"}
]

# --- Lista para almacenar archivos descargados ---
downloaded_files = []

# --- Descargar todos los archivos primero ---
# Dentro del loop para cada centro
for reporte in reportes:  # Cambiar nombre de variable set -> reporte
    tipo_reporte = reporte["set"]
    url_reporte = reporte["url"]

    # Filtrar centros por tipo
    centros_filtrados = [c for c in centros if c["tipo"] == tipo_reporte]

    time.sleep(5)

    for centro in centros_filtrados:
        nombre_centro = centro["nombre"]

        # Manejo de pestañas
        driver.execute_script(f"window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            # Navegar a la URL

            driver.get(url_reporte)

            # Registro de archivos previos
            archivos_previos = set(os.listdir(download_dir))

            time.sleep(5)

            # Configurar fechas
            modificar_fechas(driver, wait, "txt4", fecha_inicio)
            modificar_fechas(driver, wait, "txt5", fecha_fin)

            # Antes de llamar a modificar_nombre_centro, agregar:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='txt3']"))
            )

            # Configurar centro
            modificar_nombre_centro(driver, wait, "txt3", nombre_centro)

            # Esperar a que se actualicen los posibles elementos dependientes
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
            )

            # Generar reporte y exportar a Excel
            button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Ver Reporte']")))
            button.click()
            time.sleep(10)
            #report_container = wait.until(EC.visibility_of_element_located((By.ID, "idReportContainer")))
            export_button = wait.until(EC.presence_of_element_located((By.ID, "tdShowExport")))
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
            export_button = wait.until(EC.element_to_be_clickable((By.ID, "tdShowExport")))
            driver.execute_script("arguments[0].click();", export_button)
            menu_item_excel = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@onclick, \"SelectExport('xls')\") and contains(., 'Excel')]")
            ))
            menu_item_excel.click()

            # Espera activa para detectar el nuevo archivo .xlsx
            timeout = 600  # segundos de espera máxima
            elapsed = 0
            nuevo_archivo = None
            while elapsed < timeout:
                time.sleep(2)
                elapsed += 2
                archivos_actuales = set(os.listdir(download_dir))
                nuevos_archivos = archivos_actuales - archivos_previos
                # Filtrar solo los archivos con extensión .xlsx
                xlsx_nuevos = [f for f in nuevos_archivos if f.endswith('.xlsx')]
                if xlsx_nuevos:
                    # Se toma el archivo más reciente entre los nuevos
                    nuevo_archivo = max(xlsx_nuevos, key=lambda x: os.path.getctime(os.path.join(download_dir, x)))
                    downloaded_files.append(os.path.join(download_dir, nuevo_archivo))
                    break

            if not nuevo_archivo:
                print("No se encontró ningún archivo .xlsx en el directorio de descargas tras esperar.")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue  # Salta al siguiente centro

        finally:
            #Cerrar la pestaña del centro actual y volver a la principal
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

time.sleep(10)
driver.quit()
print("Proceso completado exitosamente!")