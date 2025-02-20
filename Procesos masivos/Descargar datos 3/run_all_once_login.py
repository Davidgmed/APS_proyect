# run_all_once_login.py
import os, sys, time, subprocess, shutil
from datetime import date, timedelta
from pathlib import Path

DEBUG_PORT = os.environ.get("DEBUG_PORT", "9222")
PROFILE_DIR = os.environ.get("SELENIUM_PROFILE_DIR", r"C:\selenium\chrome_profile_iris")

# ---------- 1) Fechas (semana anterior, L-D) ----------
hoy = date.today()
weekday = hoy.weekday()               # lunes=0
lunes_actual = hoy - timedelta(days=weekday)
fecha_inicio = lunes_actual - timedelta(days=7)
fecha_fin    = fecha_inicio + timedelta(days=6)
fi_str = fecha_inicio.strftime("%d/%m/%Y")
ff_str = fecha_fin.strftime("%d/%m/%Y")
print(f"📅 Rango: {fi_str} → {ff_str}")

# ---------- 2) Lanzar Chrome con remote debugging ----------
Path(PROFILE_DIR).mkdir(parents=True, exist_ok=True)

# Intenta ubicar Chrome en rutas típicas (ajusta si usas otra)
chrome_candidates = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
]
chrome_path = next((p for p in chrome_candidates if Path(p).exists()), None)
if not chrome_path:
    raise FileNotFoundError("No encontré chrome.exe en rutas típicas. Ajusta chrome_candidates.")

chrome_cmd = [
    chrome_path,
    f"--remote-debugging-port={DEBUG_PORT}",
    f"--user-data-dir={PROFILE_DIR}",
    "--start-maximized",
]
# Lanza Chrome (quedará abierto toda la corrida)
chrome_proc = subprocess.Popen(chrome_cmd)

# ---------- 3) Conectar Selenium a esa sesión para login 1 vez ----------
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

def login_y_licencia():
    driver.get("https://iris.rayenaps.cl/")
    try:
        # Si ya está logueado, estas cajas no aparecen: caemos en except y seguimos.
        user = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "mui-1")))
        pwd  = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
        user.clear(); user.send_keys("10024485-3")
        pwd.clear();  pwd.send_keys("Ignavi24")
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]"))).click()
        time.sleep(5)
    except:
        pass

    # Selección de licencia (si aún no está seleccionada)
    try:
        sel = WebDriverWait(driver, 8).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(.,'Seleccionar')]")
        ))
        sel.click()
        lic = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
        ))
        lic.click()
        time.sleep(5)
        #wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]"))).click()
        time.sleep(3)
    except:
        # Ya había licencia elegida
        pass

login_y_licencia()
print("✅ Sesión iniciada y licencia seleccionada (si era necesario).")

# ---------- 4) Ejecutar tus scripts adjuntándose a la sesión ----------
# Importante: ATTACH_TO_DEBUGGER=1 hace que los scripts usen debuggerAddress en lugar de crear un Chrome nuevo.
env = os.environ.copy()
env["ATTACH_TO_DEBUGGER"] = "1"
env["DEBUG_PORT"] = DEBUG_PORT

# Lista de scripts y su orden (ajústala a tu preferencia)
scripts = [
    #"Atenciones_respiratorias.py",
    "Actividades_newIris.py",
    "Urgencia_newIris.py",
    "Urgencia_newIris_poli.py",
    "Glicosiladas_newIris.py",
    "SaludMental_newIris.py"
]

for script in scripts:
    print(f"🚀 Ejecutando {script} con sesión compartida…")
    subprocess.run([sys.executable, script, fi_str, ff_str], check=True, env=env)

print("🎉 Fin del pipeline. Dejo Chrome abierto por si quieres inspeccionar.")
# Si prefieres cerrarlo automáticamente, descomenta:
# driver.quit()
# chrome_proc.terminate()
