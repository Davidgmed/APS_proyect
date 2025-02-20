# Urgencia_newIris_poli.py  (versión adjuntable a sesión existente)
# - Si ATTACH_TO_DEBUGGER=1 y DEBUG_PORT=<puerto> -> se conecta a la sesión de Chrome abierta por el orquestador.
# - Si no, funciona como siempre: crea su propio Chrome, hace login y selecciona licencia.
#
# Uso con orquestador:
#   ATTACH_TO_DEBUGGER=1 DEBUG_PORT=9222 python Urgencia_newIris_poli.py 01/08/2025 07/08/2025

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
    os.makedirs(download_dir)

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

    # Ingresar usuario
    username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
    username_input.clear()
    # username_input.send_keys("14092485-7")
    username_input.send_keys("10024485-3")

    # Ingresar contraseña
    password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
    password_input.clear()
    # password_input.send_keys("David.2025")
    password_input.send_keys("Ignavi24")

    # Clic en "Ingresar"
    ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
    time.sleep(1)
    ingresar_button.click()
    time.sleep(8)

    # Seleccionar licencia (si aparece)
    try:
        select_div = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
        ))
        time.sleep(1)
        select_div.click()
        time.sleep(1)

        menu_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
        ))
        time.sleep(1)
        menu_item.click()
        time.sleep(2)

        confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
        confirmar_button.click()
        time.sleep(8)
    except Exception:
        # Ya había licencia seleccionada o el layout cambió
        pass
else:
    print("🔗 Sesión existente detectada: se omite login y selección de licencia.")

# =================================
# 6) Helpers (igual al original)
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
# 7) Reporte y Centros
# ==========================
reportes = [
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=2458", "set": "dispositivo"}
]

centros = [
    {"tipo": "dispositivo", "nombre": "Centro de Salud Familiar Santa Laura"},
    {"tipo": "dispositivo", "nombre": "Centro Comunitario Salud Familiar Santa Laura"},
    {"tipo": "dispositivo", "nombre": "Centro de Salud Familiar Mario Salcedo"},
    {"tipo": "dispositivo", "nombre": "Centro de Salud Familiar Orlando Letelier"},
    {"tipo": "dispositivo", "nombre": "Centro De Salud Familiar Cóndores De Chile"},
    {"tipo": "dispositivo", "nombre": "Centro De Salud Familiar Dr. Carlos Lorca"},
    {"tipo": "dispositivo", "nombre": "Centro de Salud Familiar Dra. Haydeé López Casoou"},
    {"tipo": "dispositivo", "nombre": "Centro Comunitario de Salud Familiar Los Sauces"}
]

# ==========================================
# 8) Descarga: nuevas pestañas en MISMA sesión
# ==========================================
downloaded_files = []

for reporte in reportes:
    tipo_reporte = reporte["set"]
    url_reporte = reporte["url"]

    centros_filtrados = [c for c in centros if c["tipo"] == tipo_reporte]

    for centro in centros_filtrados:
        nombre_centro = centro["nombre"]

        # Abrir nueva pestaña en la MISMA sesión
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            # Ir al reporte
            driver.get(url_reporte)

            # Files previos
            archivos_previos = set(os.listdir(download_dir))

            # IMPORTANTE para este reporte: la 2ª fecha es txt7 (no txt5)
            modificar_fechas(driver, wait, "txt4", fecha_inicio)
            modificar_fechas(driver, wait, "txt7", fecha_fin)

            # Asegurar input del centro presente antes de setear
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='txt3']")))
            modificar_nombre_centro(driver, wait, "txt3", nombre_centro)

            # Generar y exportar
            button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Ver Reporte']")))
            button.click()
            time.sleep(10)

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
            timeout = 120
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
            # Cerrar pestaña del centro y volver a la principal
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

# =====================
# 9) Cierre controlado
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
