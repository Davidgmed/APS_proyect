
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys

#--- Recibir fechas desde argumentos ---
if len(sys.argv) != 3:
    print("Uso: script.py <fecha_inicio> <fecha_fin>")
    sys.exit(1)

fecha_inicio = sys.argv[1]
fecha_fin = sys.argv[2]

print(f"Usando fechas: {fecha_inicio} - {fecha_fin}")


# --- Configuración del directorio de descargas ---
download_dir = r"G:\Mi unidad\Actividades\Datosp4"
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
wait = WebDriverWait(driver, 20)



# --- Función para modificar el campos ---

def modificar_fechas(driver, wait, nombre_campo, valor):
    # Espera a que el elemento con el atributo name igual a nombre_campo sea visible
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    # Utiliza execute_script para asignar el nuevo valor al input
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor
    )


def modificar_nombre_centro(driver, wait, centro_info):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, "txt3")))
    driver.execute_script(
        "document.querySelector('input[name=\"txt3\"]').setAttribute('value', arguments[0]);",
        centro_info['nombre']
    )

# --- Lista de centros ---
centros = [
    {"nombre": "Centro de Salud Familiar Santa Laura"},
    {"nombre": "Centro Comunitario Salud Familiar Santa Laura"},
    {"nombre": "Centro de Salud Familiar Mario Salcedo"},
    {"nombre": "Centro de Salud Familiar Orlando Letelier"},
    {"nombre": "Centro De Salud Familiar Cóndores De Chile"},
    {"nombre": "Centro De Salud Familiar Dr. Carlos Lorca"},
    {"nombre": "Centro de Salud Familiar Dra. Haydeé López Casoou"},
    {"nombre": "Centro Comunitario de Salud Familiar Los Sauces"},
    {"nombre": "Centro Salud Adolescente"},
    {"nombre": "Centro Especialidad el Bosque"},
    {"nombre": "COSAM El Bosque"},
    {"nombre": "Direccion de Salud Municipal"}
]

# --- Lista para almacenar archivos descargados ---
downloaded_files = []

# --- Descargar todos los archivos primero ---
# Dentro del loop para cada centro
for centro_info in centros:
    # Registra los archivos existentes antes de iniciar la descarga
    archivos_previos = set(os.listdir(download_dir))

    # Abrir nueva pestaña y ejecutar la descarga
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=2318', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Completar fechas y demás acciones...
    modificar_fechas(driver, wait, "txt4", fecha_inicio)
    modificar_fechas(driver, wait, "txt7", fecha_fin)

    # Enviar Escape para cerrar overlays (por ejemplo, un datepicker abierto)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    # Esperar a que el elemento select esté presente
    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, "txt8"))
    )
    select = Select(select_element)
    select.select_by_value("1")

    # Esperar a que el elemento select esté presente
    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, "txt10"))
    )
    select = Select(select_element)
    select.select_by_value("72")

    # Esperar a que el elemento <select> esté presente
    select_element_txt11 = wait.until(
        EC.presence_of_element_located((By.NAME, "txt11"))
    )
    select_txt11 = Select(select_element_txt11)
    select_txt11.select_by_value("2")

    modificar_nombre_centro(driver, wait, centro_info)


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
    timeout = 300  # segundos de espera máxima
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

    # Cerrar la pestaña del centro actual y volver a la principal
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

# Leer y combinar todos los archivos
#dfs = []
#for file in downloaded_files:
#    try:
#        df = pd.read_excel(file, skiprows=8)
#        dfs.append(df)
#    except Exception as e:
#        print(f"Error leyendo {file}: {str(e)}")
#
#if not dfs:
#    print("No se encontraron archivos válidos para procesar")
#    driver.quit()
#    exit()
#df_combined = pd.concat(dfs, ignore_index=True)

print("Finalizada descargas...")
time.sleep(10)
print("Finalizada descargas...")

# --- Finalizar ---
print("Proceso completado exitosamente!")