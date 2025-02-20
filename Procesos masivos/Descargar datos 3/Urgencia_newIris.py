# Urgencia_newIris.py  (versión adjuntable a sesión existente)
# - Si ATTACH_TO_DEBUGGER=1 y DEBUG_PORT=<puerto> -> se conecta a la sesión de Chrome abierta por el orquestador.
# - Si no, funciona como siempre: crea su propio Chrome, hace login y selecciona licencia.
#
# Uso con orquestador:
#   ATTACH_TO_DEBUGGER=1 DEBUG_PORT=9222 python Urgencia_newIris.py 01/08/2025 07/08/2025

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys

# =========================
# 1) Fechas por argumento
# =========================
if len(sys.argv) != 3:
    print("Uso: script.py <fecha_inicio> <fecha_fin>")
    sys.exit(1)

fecha_inicio = sys.argv[1]
fecha_fin = sys.argv[2]
print(f"Usando fechas: {fecha_inicio} - {fecha_fin}")

# ==================================
# 2) Adjuntarse a depurador si aplica
# ==================================
DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))
ATTACH = os.environ.get("ATTACH_TO_DEBUGGER") == "1"

# =======================================
# 3) Directorio de descargas (sin cambios)
# =======================================
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
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

# Conectarse a la sesión ya abierta por el orquestador (si corresponde)
if ATTACH:
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# ======================================
# 5) Login y selección de licencia (cond)
# ======================================
if not ATTACH:
    driver.get("https://iris.rayenaps.cl/")
    time.sleep(5)

    # Ingresar usuario
    username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
    username_input.clear()
    # username_input.send_keys("14092485-7")
    username_input.send_keys("10024485-3")
    time.sleep(1)

    # Ingresar contraseña
    password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
    password_input.clear()
    # password_input.send_keys("David.2025")
    password_input.send_keys("Ignavi24")
    time.sleep(1)

    # Clic en "Ingresar"
    ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
    ingresar_button.click()
    time.sleep(6)

    # Seleccionar licencia (si aparece)
    try:
        select_div = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
        ))
        select_div.click()
        time.sleep(1)

        menu_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
        ))
        menu_item.click()
        time.sleep(1)

        confirmar_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Confirmar')]")
        ))
        confirmar_button.click()
        time.sleep(6)
    except Exception:
        # Ya había licencia seleccionada o el layout cambió
        pass
else:
    print("🔗 Sesión existente detectada: se omite login y selección de licencia.")

# =================================
# 6) Helpers (idénticos al original)
# =================================
def modificar_fechas(driver, wait, nombre_campo, valor):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor
    )

def modificar_nombre_centro(driver, wait, nombre_campo, valor):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor
    )

# ==========================
# 7) Reportes y Centros
# ==========================
reportes = [
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677", "set": "urgencias"},
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=1110", "set": "urgencias"},
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=673", "set": "urgencias"},  # TIEMPOS
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=520", "set": "urgencias"},  # ADMITIDOS
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=810", "set": "urgencias"}   # GES
]

centros = [
    {"tipo": "urgencias", "nombre": "SAR Haydeé López Casoou"},
    {"tipo": "urgencias", "nombre": "SAPU Dr. Carlos Lorca"},
    {"tipo": "urgencias", "nombre": "SAPU Condores de Chile"},
    {"tipo": "urgencias", "nombre": "SAPU Santa Laura"}
]

# ==========================================
# 8) Descarga: nuevas pestañas en MISMA sesión
# ==========================================
downloaded_files = []

for reporte in reportes:
    tipo_reporte = reporte["set"]
    url_reporte = reporte["url"]

    # Filtrar centros por tipo
    centros_filtrados = [c for c in centros if c["tipo"] == tipo_reporte]
    time.sleep(2)

    for centro in centros_filtrados:
        nombre_centro = centro["nombre"]

        # Abrir nueva pestaña directo a la URL del reporte
        driver.execute_script(f"window.open('{url_reporte}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            # Registro de archivos previos
            archivos_previos = set(os.listdir(download_dir))

            # Parametrizar fechas
            modificar_fechas(driver, wait, "txt4", fecha_inicio)
            modificar_fechas(driver, wait, "txt5", fecha_fin)
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

            # Asegurar input del centro disponible y setear
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='txt3']")))
            modificar_nombre_centro(driver, wait, "txt3", nombre_centro)

            # Ver reporte y exportar a Excel
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

            # Espera activa para detectar el nuevo archivo .xlsx
            timeout = 600
            elapsed = 0
            nuevo_archivo = None
            while elapsed < timeout:
                time.sleep(2)
                elapsed += 2
                actuales = set(os.listdir(download_dir))
                nuevos = actuales - archivos_previos
                xlsx_nuevos = [f for f in nuevos if f.endswith('.xlsx')]
                if xlsx_nuevos:
                    nuevo_archivo = max(
                        xlsx_nuevos,
                        key=lambda x: os.path.getctime(os.path.join(download_dir, x))
                    )
                    downloaded_files.append(os.path.join(download_dir, nuevo_archivo))
                    break

            if not nuevo_archivo:
                print(f"[{nombre_centro}] No se encontró archivo .xlsx tras la espera.")
        finally:
            # Cerrar la pestaña del centro actual y volver a la principal
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

# ======================================
# 9) (Opcional) Procesamiento de archivos
# ======================================
# Aquí podrías abrir/combinar/validar los .xlsx descargados, si aplica.
# for file in downloaded_files:
#     df = pd.read_excel(file)
#     ...

# =====================
# 10) Cierre controlado
# =====================
if ATTACH:
    # No cerrar la sesión global: ya cerramos las pestañas que abrimos.
    try:
        driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass
    print("✅ Script finalizado usando sesión compartida (no se cierra Chrome global).")
else:
    driver.quit()
    print("Proceso completado exitosamente!")
