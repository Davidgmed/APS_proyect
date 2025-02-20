# Actividades_newIris.py  (versión adjuntable a sesión existente)
# - Si ATTACH_TO_DEBUGGER=1 y DEBUG_PORT=<puerto> -> se conecta a la sesión de Chrome abierta por el orquestador.
# - Si no, funciona como siempre: crea su propio Chrome, hace login y selecciona licencia.
#
# Uso típico con orquestador:
#   ATTACH_TO_DEBUGGER=1 DEBUG_PORT=9222 python Actividades_newIris.py 01/08/2025 07/08/2025
#
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys

# ========================
# 1) Parámetros de entrada
# ========================
if len(sys.argv) == 3:
    fecha_inicio = sys.argv[1]
    fecha_fin = sys.argv[2]
    print(f"Usando fechas por argumento: {fecha_inicio} - {fecha_fin}")
else:
    # Fallback (puedes quitarlo si siempre vendrán por argv)
    fecha_inicio = "21/07/2025"
    fecha_fin = "02/08/2025"
    print(f"Usando fechas por defecto: {fecha_inicio} - {fecha_fin}")

# ============================
# 2) Modo adjunto a depurador
# ============================
DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))
ATTACH = os.environ.get("ATTACH_TO_DEBUGGER") == "1"

# ================================
# 3) Directorio de descargas (como ya lo usabas)
# ================================
download_dir = r"G:\Mi unidad\Actividades\Datosp4"
if not os.path.exists(download_dir):
    os.makedirs(download_dir, exist_ok=True)

# ===========================
# 4) Configuración del driver
# ===========================
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

# Si estamos adjuntos, conectarnos a la sesión ya abierta por el orquestador:
if ATTACH:
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# ======================================
# 5) Login y selección de licencia (cond)
# ======================================
if not ATTACH:
    # --- Inicio de sesión en la página ---
    driver.get("https://iris.rayenaps.cl/")
    # Ingresar usuario
    username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
    username_input.clear()
    time.sleep(1.5)
    # username_input.send_keys("14092485-7")
    username_input.send_keys("10024485-3")

    # Ingresar contraseña
    password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
    password_input.clear()
    time.sleep(1.0)
    # password_input.send_keys("David.2025")
    password_input.send_keys("Ignavi24")

    # Clic en "Ingresar"
    ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
    time.sleep(1.0)
    ingresar_button.click()
    time.sleep(8)

    # Seleccionar licencia
    try:
        select_div = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
        ))
        time.sleep(1)
        select_div.click()

        menu_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH,
             "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
        ))
        time.sleep(1)
        menu_item.click()

        confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
        time.sleep(0.8)
        confirmar_button.click()
        time.sleep(6)
    except Exception:
        # Si ya había una licencia seleccionada o el layout cambió
        pass
else:
    print("🔗 Sesión existente detectada: se omite login y selección de licencia.")

# =================================
# 6) Helpers que ya usabas (idénticos)
# =================================
def modificar_fechas(driver, wait, nombre_campo, valor):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
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

# ===================
# 7) Catálogo centros
# ===================
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

# =========================
# 8) Descargas de reportes
# =========================
downloaded_files = []

for centro_info in centros:
    # Registra los archivos existentes antes de iniciar la descarga
    archivos_previos = set(os.listdir(download_dir))

    # Abrir nueva pestaña en la MISMA SESIÓN
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=2318', '_blank');"
    )
    driver.switch_to.window(driver.window_handles[-1])

    # Completar fechas y filtros
    modificar_fechas(driver, wait, "txt4", fecha_inicio)
    modificar_fechas(driver, wait, "txt7", fecha_fin)

    # Cerrar overlays (ej. datepicker)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    # Filtros select
    select_element = wait.until(EC.presence_of_element_located((By.NAME, "txt8")))
    Select(select_element).select_by_value("1")

    select_element = wait.until(EC.presence_of_element_located((By.NAME, "txt10")))
    Select(select_element).select_by_value("72")

    select_element_txt11 = wait.until(EC.presence_of_element_located((By.NAME, "txt11")))
    Select(select_element_txt11).select_by_value("2")

    modificar_nombre_centro(driver, wait, centro_info)

    # Ver reporte y exportar
    button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Ver Reporte']")))
    button.click()
    time.sleep(8)

    export_button = wait.until(EC.presence_of_element_located((By.ID, "tdShowExport")))
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
    export_button = wait.until(EC.element_to_be_clickable((By.ID, "tdShowExport")))
    driver.execute_script("arguments[0].click();", export_button)

    menu_item_excel = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@onclick, \"SelectExport('xls')\") and contains(., 'Excel')]")
    ))
    menu_item_excel.click()

    # Espera activa archivo .xlsx nuevo
    timeout = 300
    elapsed = 0
    nuevo_archivo = None
    while elapsed < timeout:
        time.sleep(2)
        elapsed += 2
        archivos_actuales = set(os.listdir(download_dir))
        nuevos_archivos = archivos_actuales - archivos_previos
        xlsx_nuevos = [f for f in nuevos_archivos if f.endswith('.xlsx')]
        if xlsx_nuevos:
            nuevo_archivo = max(
                xlsx_nuevos,
                key=lambda x: os.path.getctime(os.path.join(download_dir, x))
            )
            downloaded_files.append(os.path.join(download_dir, nuevo_archivo))
            break

    if not nuevo_archivo:
        print(f"[{centro_info['nombre']}] No se encontró archivo .xlsx tras la espera.")
        # Cerrar pestaña actual y volver
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        continue

    # Cerrar la pestaña del centro y volver a la principal
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

print("Finalizada descargas...")

# ======================================
# 9) Integración con proceso externo (opcional)
# ======================================
try:
    # OJO: revisa esta ruta; estaba mixta (/, \) en el original.
    with open(r"/Procesos masivos\Cagar base\Actividades_folder_bulk.py") as file:
        exec(file.read())
except Exception as e:
    print("Ha ocurrido un error con folder_bulk:", e)
else:
    print("Ejecución correcta de folder_bulk")

# =====================
# 10) Cierre del driver
# =====================
if ATTACH:
    # No matar la sesión global: limpia pestañas que abriste y deja la ventana base.
    try:
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass
    print("✅ Script finalizado usando sesión compartida (no se cierra Chrome global).")
else:
    driver.quit()
    print("Proceso completado exitosamente (sesión propia cerrada).")
