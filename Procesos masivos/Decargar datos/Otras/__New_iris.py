from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys
from datetime import datetime, date
import calendar

# =========================
# 1) PARÁMETROS DE FECHA
# =========================
# Puedes mantener los argumentos por línea de comandos si quieres.
# Si prefieres hardcodear, deja estas dos líneas con tus fechas.
fecha_inicio = "01/01/2023"
fecha_fin = "31/12/2023"

# =========================
# 2) FUNCIÓN: PERIODOS MENSUALES
# =========================
def generar_periodos_mensuales(fi_str: str, ff_str: str, fmt="%d/%m/%Y"):
    """
    Devuelve una lista de tuplas (inicio_str, fin_str) en formato dd/mm/yyyy,
    donde cada tupla representa un periodo máximo de un mes completo
    dentro del rango [fi, ff].
    """
    fi = datetime.strptime(fi_str, fmt).date()
    ff = datetime.strptime(ff_str, fmt).date()
    if fi > ff:
        raise ValueError("fecha_inicio es posterior a fecha_fin")

    periodos = []
    anio, mes = fi.year, fi.month

    while True:
        # primer día del mes actual (o fi si empieza al medio del mes)
        inicio_mes = date(anio, mes, 1)
        inicio_periodo = fi if fi > inicio_mes else inicio_mes

        # último día del mes actual
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        fin_mes = date(anio, mes, ultimo_dia)
        fin_periodo = ff if ff < fin_mes else fin_mes

        # solo agregamos si hay intersección válida
        if inicio_periodo <= fin_periodo:
            periodos.append((
                inicio_periodo.strftime(fmt),
                fin_periodo.strftime(fmt)
            ))

        # avanzar al mes siguiente
        if (anio, mes) >= (ff.year, ff.month):
            break
        if mes == 12:
            anio += 1
            mes = 1
        else:
            mes += 1

    return periodos

# =========================
# 3) CONFIG DESCARGAS / DRIVER (igual que tu script)
# =========================
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

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

# =========================
# 4) LOGIN (igual que tu script)
# =========================
driver.get("https://iris.rayenaps.cl/")
wait = WebDriverWait(driver, 1500)
time.sleep(10)

username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
username_input.clear()
username_input.send_keys("10024485-3")
time.sleep(1)

password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
password_input.clear()
password_input.send_keys("Ignavi24")
time.sleep(1)

ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
ingresar_button.click()
time.sleep(30)

# =========================
# 5) HELPERS (igual que tu script)
# =========================
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

# =========================
# 6) VARIABLES (igual que tu script)
# =========================
reportes = [
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677", "set" : "urgencias"},
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=1110","set" : "urgencias"},
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=673","set" : "urgencias"}, # TIEMPOS
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=520", "set" : "urgencias"}, # ADMITIDOS
    {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=810","set" : "urgencias"} # GES
]

centros = [
    {"tipo": "urgencias", "nombre": "SAR Haydeé López Casoou"},
    {"tipo": "urgencias", "nombre": "SAPU Dr. Carlos Lorca"},
    {"tipo": "urgencias", "nombre": "SAPU Condores de Chile"},
    {"tipo": "urgencias", "nombre": "SAPU Santa Laura"}
]

downloaded_files = []

# =========================
# 7) LOOP POR PERIODOS MENSUALES
# =========================
periodos = generar_periodos_mensuales(fecha_inicio, fecha_fin)  # p.ej. [("01/01/2023","31/01/2023"), ..., ("01/06/2023","30/06/2023")]

for (fi_mes, ff_mes) in periodos:
    print(f"=== Procesando periodo {fi_mes} a {ff_mes} ===")
    time.sleep(2)

    for reporte in reportes:
        tipo_reporte = reporte["set"]
        url_reporte = reporte["url"]

        centros_filtrados = [c for c in centros if c["tipo"] == tipo_reporte]
        time.sleep(5)

        for centro in centros_filtrados:
            nombre_centro = centro["nombre"]

            # Abrir pestaña nueva
            driver.execute_script("window.open('about:blank', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])

            try:
                # Navegar al reporte
                driver.get(url_reporte)

                # Registrar archivos previos para detectar nuevos .xlsx
                archivos_previos = set(os.listdir(download_dir))
                time.sleep(3)

                # *** AQUI USAMOS LAS FECHAS DEL PERIODO ***
                modificar_fechas(driver, wait, "txt4", fi_mes)
                modificar_fechas(driver, wait, "txt5", ff_mes)

                WebDriverWait(driver, 3000).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='txt3']"))
                )

                modificar_nombre_centro(driver, wait, "txt3", nombre_centro)

                WebDriverWait(driver, 3000).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
                )

                # Ver reporte y exportar a Excel
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

                # Espera activa por nuevo .xlsx
                timeout = 3000
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
                    print(f"[ADVERTENCIA] No se encontró archivo .xlsx para {nombre_centro} en {fi_mes}-{ff_mes}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

# Cerrar navegador
time.sleep(10)
driver.quit()
print("Proceso completado exitosamente!")
