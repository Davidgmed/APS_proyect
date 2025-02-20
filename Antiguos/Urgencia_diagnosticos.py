from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os

# --- Configuración del directorio de descargas ---
download_dir = r"G:\Mi unidad\Respiratorias\Descarga"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Configuración del driver con opciones para establecer el directorio de descargas
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

# --- Inicio de sesión en la página ---
driver.get("https://iris.rayenaps.cl/")
wait = WebDriverWait(driver, 10)

# Ingresar usuario
username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
username_input.clear()
#username_input.send_keys("14092485-7")
username_input.send_keys("10024485-3")

# Ingresar contraseña
password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
password_input.clear()
#password_input.send_keys("Gonzalez.2025")
password_input.send_keys("Ignavi24")

# Clic en "Ingresar"
ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
ingresar_button.click()

# Seleccionar licencia
select_div = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
))
select_div.click()

menu_item = wait.until(EC.element_to_be_clickable(
    (By.XPATH,
    #"//li[@data-value='1130' and contains(.,'SAPU Condores de Chile S.S. Metropolitano Sur')]")
    "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
))
menu_item.click()

confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
confirmar_button.click()

time.sleep(10)  # Tiempo para que la sesión se estabilice


# --- Función para modificar el campo "txt3" ---
def modificar_nombre_centro(driver, wait, centro_info):
    """
    Espera a que el input 'txt3' esté visible, lo limpia y asigna el nombre del centro.
    """
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, "txt3")))
    driver.execute_script(
        "document.querySelector('input[name=\"txt3\"]').setAttribute('value', arguments[0]);",
        centro_info['nombre']
    )


# --- Lista de centros ---
centros = [
    {"nombre": "SAPU Dr. Carlos Lorca"},
    {"nombre": "SAR Haydeé López Casoou"},
    {"nombre": "SAPU Condores de Chile"},
    {"nombre": "SAPU Santa Laura"}
]

# --- Iterar sobre cada centro y descargar el Excel ---
for centro_info in centros:
    # Abrir nueva ventana/pestaña con la URL del reporte
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677', '_blank');")
    # Cambiar al nuevo controlador (pestaña)
    driver.switch_to.window(driver.window_handles[-1])

    # Completar el rango de fechas
    fecha_inicio = wait.until(EC.presence_of_element_located((By.ID, "txt4")))
    fecha_inicio.clear()
    fecha_inicio.send_keys("17/03/2025")

    # Enviar ESCAPE para cerrar posibles overlays (como el datepicker)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    fecha_fin = wait.until(EC.presence_of_element_located((By.ID, "txt5")))
    fecha_fin.clear()
    fecha_fin.send_keys("06/04/2025")

    # Enviar ESCAPE para cerrar posibles overlays (como el datepicker)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    time.sleep(5)  # Tiempo para que la sesión se estabilice

    # Modificar el campo txt3 con el nombre del centro actual
    modificar_nombre_centro(driver, wait, centro_info)

    time.sleep(5)

    # Clic en "Ver Reporte"
    button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='button' and @value='Ver Reporte']")
    ))
    button.click()

    # Esperar a que se muestre el contenedor del reporte
    report_container = wait.until(EC.visibility_of_element_located((By.ID, "idReportContainer")))

    # Acceder al botón de exportar
    export_button = wait.until(EC.presence_of_element_located((By.ID, "tdShowExport")))
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
    export_button = wait.until(EC.element_to_be_clickable((By.ID, "tdShowExport")))
    driver.execute_script("arguments[0].click();", export_button)

    # Seleccionar la opción Excel del menú de exportación
    menu_item_excel = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@onclick, \"SelectExport('xls')\") and contains(., 'Excel')]")
    ))
    menu_item_excel.click()

    # Esperar unos segundos para asegurar que la descarga inicie correctamente
    time.sleep(10)

    # Cerrar la pestaña actual y volver a la ventana principal
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

# --- Finalización ---
time.sleep(10)  # Tiempo para revisar o verificar los resultados antes de cerrar el navegador
driver.quit()
