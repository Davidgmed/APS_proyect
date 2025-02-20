import subprocess
import sys
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import sys



hoy = date.today()
weekday = hoy.weekday()  # lunes=0, martes=1, ...

# Lunes de la semana actual
lunes_actual = hoy - timedelta(days=weekday)

# Lunes de la semana anterior
fecha_inicio = lunes_actual - timedelta(days=7)

# Domingo de la semana anterior
fecha_fin = fecha_inicio + timedelta(days=6)

# Formato DD/MM/YYYY
fecha_inicio_str = fecha_inicio.strftime("%d/%m/%Y")
fecha_fin_str = fecha_fin.strftime("%d/%m/%Y")

print(f"📅 Fecha inicio: {fecha_inicio_str}")
print(f"📅 Fecha fin: {fecha_fin_str}")



# Configuración del driver con opciones para establecer el directorio de descargas
options = webdriver.ChromeOptions()
prefs = {
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
time.sleep(10)
# Seleccionar licencia
select_div = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
))
time.sleep(1)
select_div.click()

menu_item = wait.until(EC.element_to_be_clickable(
    (By.XPATH,
    #"//li[@data-value='1130' and contains(.,'SAPU Condores de Chile S.S. Metropolitano Sur')]")
    "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
))
time.sleep(1)
menu_item.click()
time.sleep(1)

confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
time.sleep(1)
confirmar_button.click()

time.sleep(10)

scripts = [
    #"Atenciones_respiratorias.py",
    "Actividades_newIris.py",
    "Glicosiladas_newIris.py",
    "SaludMental_newIris.py",
    "Urgencia_newIris.py",
    "Urgencia_newIris_poli.py"
]


for script in scripts:
    print(f"🚀 Ejecutando {script}…")
    subprocess.run(
        [sys.executable, script, fecha_inicio_str, fecha_fin_str],
        check=True
    )

print("✅ Todos los scripts han terminado sin errores.")
