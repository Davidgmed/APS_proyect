# Atenciones_respiratorias.py  (versión adjuntable a sesión existente)
# - Si ATTACH_TO_DEBUGGER=1 y DEBUG_PORT=<puerto> -> se conecta a la sesión de Chrome abierta por el orquestador.
# - Si no, funciona como siempre: crea su propio Chrome, hace login y selecciona licencia.
#
# Uso típico con orquestador:
#   ATTACH_TO_DEBUGGER=1 DEBUG_PORT=9222 python Atenciones_respiratorias.py 01/08/2025 07/08/2025

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import sys
from selenium.common.exceptions import TimeoutException

# --- Recibir fechas desde argumentos (igual que tu original) ---
if len(sys.argv) != 3:
    print("Uso: script.py <fecha_inicio> <fecha_fin>")
    sys.exit(1)

fecha_inicio_str = sys.argv[1]
fecha_fin_str = sys.argv[2]
print(f"Usando fechas: {fecha_inicio_str} - {fecha_fin_str}")

# ============================
# Modo adjunto a depurador
# ============================
DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))
ATTACH = os.environ.get("ATTACH_TO_DEBUGGER") == "1"

# --- Configuración del directorio de descargas ---
download_dir = r"G:\Mi unidad\Respiratorias\Descarga"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# --- Configuración del driver con opciones ---
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    # Desactiva gestor de contraseñas y pop-up
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
}
options.add_experimental_option("prefs", prefs)

# Opciones para evitar pop-ups y automatización
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-save-password-bubble")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")

# Si estamos adjuntos, conectarnos a la sesión ya abierta por el orquestador
if ATTACH:
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# --- Configuración de fechas auxiliares (sin cambios) ---
fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_tabla = fecha_ayer.strftime("%Y-%m-%d")
fecha_ayer_str_simple = fecha_ayer.strftime("%Y%m%d")

# --- Configuración de Google Sheets (sin cambios) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r'G:\Mi unidad\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Casos respiratorios red de urgencia 2024")

# Diccionario de asignación de establecimientos a sectores (sin cambios)
establishment_to_sector = {
    'Centro de Salud Familiar Mario Salcedo': 'Mario Salcedo',
    'Centro de Salud Familiar Dra. Haydeé López Casoou': 'Haydeé López',
    'Centro De Salud Familiar Dr. Carlos Lorca': 'Carlos Lorca',
    'Centro Comunitario de Salud Familiar Los Sauces': 'Carlos Lorca',
    'Centro De Salud Familiar Cóndores De Chile': 'Cóndores de Chile',
    'Centro de Salud Familiar Santa Laura': 'Santa Laura',
    'Centro Comunitario Salud Familiar Santa Laura': 'Santa Laura',
    'Centro de Salud Familiar Orlando Letelier': 'Orlando Letelier',
    'COSAM El Bosque': 'Sector 0',
    'UAPO El Bosque': 'Sector 0',
    'UAPORRINO El Bosque': 'Sector 0',
    'Centro Salud Adolescente': 'Sector 0',
    'Direccion de Salud Municipal': 'Sector 0',
    'Centro de Atencion Integral en Salud': 'Sector 0',
    'Centro Comunitario de Rehabilitación El Bosque': 'Sector 0',
    'Centro Especialidad el Bosque': 'Sector 0'
}

def append_df_to_sheet(df, sheet_name):
    """Agrega datos a una hoja específica en Google Sheets."""
    worksheet = spreadsheet.worksheet(sheet_name)
    existing_data = worksheet.get_all_values()
    start_row = len(existing_data) + 1
    rows = df.values.tolist()
    worksheet.append_rows(rows, table_range=f"A{start_row}")

# ================================
# Login y selección de licencia
# (solo si NO está adjunto)
# ================================
if not ATTACH:
    driver.get("https://iris.rayenaps.cl/")

    # Ingresar usuario
    username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
    username_input.clear()
    username_input.send_keys("10024485-3")

    # Ingresar contraseña
    password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
    password_input.clear()
    password_input.send_keys("Ignavi24")

    # Clic en "Ingresar"
    ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
    time.sleep(1)
    ingresar_button.click()
    time.sleep(5)

    # Seleccionar licencia (si aplica)
    try:
        select_div = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
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
        time.sleep(10)
    except Exception:
        # Ya había licencia o el layout cambió
        pass
else:
    print("🔗 Sesión existente detectada: se omite login y selección de licencia.")

# --- Función para modificar el campo "txt3" (igual) ---
def modificar_nombre_centro(driver, wait, centro_info):
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, "txt3")))
    driver.execute_script(
        "document.querySelector('input[name=\"txt3\"]').setAttribute('value', arguments[0]);",
        centro_info['nombre']
    )

# --- Lista de centros (igual) ---
centros = [
    {"nombre": "SAPU Dr. Carlos Lorca"},
    {"nombre": "SAR Haydeé López Casoou"},
    {"nombre": "SAPU Condores de Chile"},
    {"nombre": "SAPU Santa Laura"}
]

# --- Lista para almacenar archivos descargados ---
downloaded_files = []

# --- Descargar todos los archivos (cada centro abre NUEVA PESTAÑA en la MISMA SESIÓN) ---
for centro_info in centros:
    archivos_previos = set(os.listdir(download_dir))

    # Abrir nueva pestaña y ejecutar la descarga
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Completar fechas
    fecha_inicio = wait.until(EC.presence_of_element_located((By.ID, "txt4")))
    fecha_inicio.clear()
    fecha_inicio.send_keys(fecha_inicio_str)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    fecha_fin = wait.until(EC.presence_of_element_located((By.ID, "txt5")))
    fecha_fin.clear()
    fecha_fin.send_keys(fecha_fin_str)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    time.sleep(2)
    modificar_nombre_centro(driver, wait, centro_info)
    time.sleep(2)

    # Ver reporte y exportar a Excel
    button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Ver Reporte']")))
    button.click()
    report_container = wait.until(EC.visibility_of_element_located((By.ID, "idReportContainer")))
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
        archivos_actuales = set(os.listdir(download_dir))
        nuevos_archivos = archivos_actuales - archivos_previos
        xlsx_nuevos = [f for f in nuevos_archivos if f.endswith('.xlsx')]
        if xlsx_nuevos:
            nuevo_archivo = max(xlsx_nuevos, key=lambda x: os.path.getctime(os.path.join(download_dir, x)))
            downloaded_files.append(os.path.join(download_dir, nuevo_archivo))
            break

    if not nuevo_archivo:
        print(f"[{centro_info['nombre']}] No se encontró archivo .xlsx tras la espera.")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        continue

    # Cerrar la pestaña del centro actual y volver a la principal
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

# --- Procesamiento único de todos los archivos (sin cambios sustantivos) ---
cie10_prefixes = ('J09', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18',
                  'J20', 'J21', 'J22', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J47')

dfs = []
for file in downloaded_files:
    try:
        df = pd.read_excel(file, skiprows=8)
        dfs.append(df)
    except Exception as e:
        print(f"Error leyendo {file}: {str(e)}")

if not dfs:
    print("No se encontraron archivos válidos para procesar")
    # No mates la sesión global si está adjunto
    if ATTACH:
        try:
            while len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            pass
    else:
        driver.quit()
    sys.exit(0)

df_combined = pd.concat(dfs, ignore_index=True)

# Filtrar por CIE10
df_filtered = df_combined[df_combined['CIE10'].str.startswith(cie10_prefixes, na=False)].copy()

# Procesar presión arterial
df_filtered[['sistolica', 'diastolica']] = df_filtered['PRESION ARTERIAL'].str.split('/', expand=True)
df_filtered['sistolica'] = pd.to_numeric(df_filtered['sistolica'], errors='coerce')
df_filtered['diastolica'] = pd.to_numeric(df_filtered['diastolica'], errors='coerce')
df_filtered['sistolica'] = df_filtered['sistolica'].fillna(0)

# Manejar duplicados
def handle_duplicates(group):
    if len(group) > 1 and (group['sistolica'] == 0).all():
        return group.drop_duplicates(subset=['CIE10'])
    return group

df_filtered = df_filtered.groupby('ID', group_keys=False).apply(handle_duplicates).reset_index(drop=True)

# Seleccionar máxima sistólica
df_result = df_filtered.loc[df_filtered.groupby('ID')['sistolica'].idxmax()]

# Limpiar y formatear
df_result.replace([np.inf, -np.inf, np.nan], None, inplace=True)
columns_to_keep = [
    'RUN', 'DV', 'NOMBRE', 'PRIMER APELLIDO', 'SEGUNDO APELLIDO',
    'SECTOR PACIENTE', 'ESTABLECIMIENTO', 'DIAGNOSTICO', 'CIE10',
    'FECHA ATENCION', 'PROFESIONAL RESPONSABLE', 'ULTIMA CATEGORIZACION',
    'SEXO', 'EDAD AÑOS'
]
df_result = df_result[columns_to_keep]

# Crear RUT y fecha
df_result = df_result.dropna(subset=['RUN'])
df_result['RUN'] = df_result['RUN'].astype(int)
df_result['RUT'] = df_result['RUN'].astype(str) + '-' + df_result['DV'].astype(str)
df_result = df_result.drop(columns=['RUN', 'DV'])
df_result['fecha'] = fecha_tabla

# Ordenar columnas
columns_order = ['fecha', 'RUT'] + [col for col in columns_to_keep if col not in ['RUN', 'DV']]
df_result = df_result[columns_order]

# --- Subir a Google Sheets ---
for establishment, sector in establishment_to_sector.items():
    df_sector = df_result[df_result['ESTABLECIMIENTO'] == establishment]
    if not df_sector.empty:
        append_df_to_sheet(df_sector, sector)
        print(f"Datos agregados a {sector}")

# Procesar externos
df_externos = df_result[~df_result['ESTABLECIMIENTO'].isin(establishment_to_sector.keys())]
if not df_externos.empty:
    append_df_to_sheet(df_externos, 'Externos')

# Eliminar archivos descargados
for file in downloaded_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"Archivo eliminado: {file}")

# --- Finalizar: no matar Chrome global si está adjunto ---
if ATTACH:
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
    print("Proceso completado exitosamente!")
