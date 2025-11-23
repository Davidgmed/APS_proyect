import os
import sys
import time
from typing import List, Optional

import pandas as pd  # Kept for compatibility with legacy imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DOWNLOAD_DIR = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
USERNAME = "10024485-3"
PASSWORD = "Ignavi24"


def create_driver(download_dir: str = DOWNLOAD_DIR) -> webdriver.Chrome:
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)


def login(driver: webdriver.Chrome, wait: WebDriverWait, username: str, password: str) -> None:
    driver.get("https://iris.rayenaps.cl/")
    time.sleep(10)

    username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
    username_input.clear()
    username_input.send_keys(username)

    password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
    password_input.clear()
    password_input.send_keys(password)

    ingresar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')"]))
    )
    ingresar_button.click()
    time.sleep(30)


def modificar_fechas(driver: webdriver.Chrome, wait: WebDriverWait, nombre_campo: str, valor: str) -> None:
    wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor,
    )


def modificar_nombre_centro(driver: webdriver.Chrome, wait: WebDriverWait, nombre_campo: str, valor: str) -> None:
    wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);",
        valor,
    )


def download_reports(driver: webdriver.Chrome, wait: WebDriverWait, fecha_inicio: str, fecha_fin: str) -> List[str]:
    reportes = [
        {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677", "set": "urgencias"},
        {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=1110", "set": "urgencias"},
        {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=673", "set": "urgencias"},
        {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=520", "set": "urgencias"},
        {"url": "https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=810", "set": "urgencias"},
    ]

    centros = [
        {"tipo": "urgencias", "nombre": "SAR Haydeé López Casoou"},
        {"tipo": "urgencias", "nombre": "SAPU Dr. Carlos Lorca"},
        {"tipo": "urgencias", "nombre": "SAPU Condores de Chile"},
        {"tipo": "urgencias", "nombre": "SAPU Santa Laura"},
    ]

    downloaded_files: List[str] = []

    for reporte in reportes:
        centros_filtrados = [c for c in centros if c["tipo"] == reporte["set"]]
        time.sleep(5)

        for centro in centros_filtrados:
            driver.execute_script("window.open('about:blank', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])

            try:
                driver.get(reporte["url"])
                archivos_previos = set(os.listdir(DOWNLOAD_DIR))

                time.sleep(30)
                modificar_fechas(driver, wait, "txt4", fecha_inicio)
                modificar_fechas(driver, wait, "txt5", fecha_fin)

                WebDriverWait(driver, 3000).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='txt3']"))
                )
                modificar_nombre_centro(driver, wait, "txt3", centro["nombre"])
                WebDriverWait(driver, 3000).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
                )

                button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Ver Reporte']"))
                )
                button.click()
                time.sleep(10)

                export_button = wait.until(EC.presence_of_element_located((By.ID, "tdShowExport")))
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                export_button = wait.until(EC.element_to_be_clickable((By.ID, "tdShowExport")))
                driver.execute_script("arguments[0].click();", export_button)

                menu_item_excel = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//div[contains(@onclick, \"SelectExport('xls')\") and contains(., 'Excel')]")
                    )
                )
                menu_item_excel.click()

                timeout = 3000
                elapsed = 0
                nuevo_archivo: Optional[str] = None
                while elapsed < timeout:
                    time.sleep(2)
                    elapsed += 2
                    archivos_actuales = set(os.listdir(DOWNLOAD_DIR))
                    nuevos_archivos = archivos_actuales - archivos_previos
                    xlsx_nuevos = [f for f in nuevos_archivos if f.endswith('.xlsx')]
                    if xlsx_nuevos:
                        nuevo_archivo = max(
                            xlsx_nuevos,
                            key=lambda x: os.path.getctime(os.path.join(DOWNLOAD_DIR, x)),
                        )
                        downloaded_files.append(os.path.join(DOWNLOAD_DIR, nuevo_archivo))
                        break

                if not nuevo_archivo:
                    print("No se encontró ningún archivo .xlsx en el directorio de descargas tras esperar.")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

    return downloaded_files


def run(fecha_inicio: str, fecha_fin: str, driver: Optional[webdriver.Chrome] = None) -> List[str]:
    close_driver = False
    if driver is None:
        driver = create_driver()
        close_driver = True
        wait = WebDriverWait(driver, 150)
        login(driver, wait, USERNAME, PASSWORD)
    else:
        wait = WebDriverWait(driver, 150)

    try:
        return download_reports(driver, wait, fecha_inicio, fecha_fin)
    finally:
        if close_driver:
            time.sleep(10)
            driver.quit()


def main():
    if len(sys.argv) != 3:
        print("Uso: python Urgencia_newIris.py <fecha_inicio> <fecha_fin>")
        sys.exit(1)

    fecha_inicio = sys.argv[1]
    fecha_fin = sys.argv[2]
    archivos = run(fecha_inicio, fecha_fin)
    print("Proceso completado exitosamente!")
    for archivo in archivos:
        print(f"Archivo descargado: {archivo}")


if __name__ == "__main__":
    main()
