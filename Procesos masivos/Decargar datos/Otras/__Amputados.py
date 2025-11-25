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

# --- Recibir fechas desde argumentos ---
#if len(sys.argv) != 3:
#    print("Uso: script.py <fecha_inicio> <fecha_fin>")
#    sys.exit(1)
#
#fecha_inicio = sys.argv[1]
#fecha_fin = sys.argv[2]
#
#print(f"Usando fechas: {fecha_inicio} - {fecha_fin}")

fecha_inicio = "10/11/2025"
fecha_fin = "16/11/2025"

print(f"Usando fechas: {fecha_inicio} - {fecha_fin}")

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
    "safebrowsing.enabled": True,
    # Desactiva el gestor de contraseñas y el pop-up
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
}
options.add_experimental_option("prefs", prefs)

# Opciones para evitar pop-ups y automatización
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-save-password-bubble")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(options=options)

# --- Configuración de fechas ---
fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_tabla = fecha_ayer.strftime("%Y-%m-%d")
fecha_ayer_str_simple = fecha_ayer.strftime("%Y%m%d")

# --- Configuración de Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r'G:\Mi unidad\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Casos respiratorios red de urgencia 2025")

# Diccionario de asignación de establecimientos a sectores
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
    """Función para agregar datos a una hoja específica en Google Sheets."""
    worksheet = spreadsheet.worksheet(sheet_name)
    existing_data = worksheet.get_all_values()
    start_row = len(existing_data) + 1
    rows = df.values.tolist()
    worksheet.append_rows(rows, table_range=f"A{start_row}")

# --- Inicio de sesión en la página ---
driver.get("https://iris.rayenaps.cl/")
wait = WebDriverWait(driver, 20)

# Ingresar usuario
username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
username_input.clear()
#username_input.send_keys("14092485-7")
username_input.send_keys("10024485-3")

# Ingresar contraseña
password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
password_input.clear()
#password_input.send_keys("David.2025")
password_input.send_keys("Ignavi24")


# Clic en "Ingresar"
ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
time.sleep(1)
ingresar_button.click()
time.sleep(5)

# Seleccionar licencia
#select_div = wait.until(EC.element_to_be_clickable(
#    (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
#))
#time.sleep(5)
#select_div.click()
#time.sleep(1)


#menu_item = wait.until(EC.element_to_be_clickable(
#    (By.XPATH,
    #"//li[@data-value='1130' and contains(.,'SAPU Condores de Chile S.S. Metropolitano Sur')]")
#    "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
#))
#time.sleep(1)
#menu_item.click()
#time.sleep(2)

#confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
#confirmar_button.click()

time.sleep(20)

def modificar_fechas(driver, wait, nombre_campo, valor):
    # Espera a que el elemento con el atributo name igual a nombre_campo sea visible
    input_element = wait.until(EC.visibility_of_element_located((By.NAME, nombre_campo)))
    # Utiliza execute_script para asignar el nuevo valor al input
    driver.execute_script(
        "document.querySelector('input[name=\"{}\"]').setAttribute('value', arguments[0]);".format(nombre_campo),
        valor
    )


# --- Función para modificar el campo "txt3" ---
def modificar_nombre_centro(driver, wait, centro_info):
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

# --- Lista para almacenar archivos descargados ---
downloaded_files = []

# --- Descargar todos los archivos primero ---
# Dentro del loop para cada centro
for centro_info in centros:
    # Registra los archivos existentes antes de iniciar la descarga
    archivos_previos = set(os.listdir(download_dir))

    # Abrir nueva pestaña y ejecutar la descarga
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=2522', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Completar fechas y demás acciones...
    modificar_fechas(driver, wait, "txt4", fecha_inicio)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    modificar_fechas(driver, wait, "txt5", fecha_fin)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    # Enviar Escape adicional para cerrar posibles overlays (por ejemplo, un datepicker abierto)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    # Marcar checkbox principal
    checkbox = wait.until(
        EC.element_to_be_clickable((By.ID, "txt7"))
    )
    checkbox.click()

    # Situación
    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, "txt9"))
    )
    select = Select(select_element)
    select.select_by_value("1")

    # Inscripción
    select_element = wait.until(
        EC.presence_of_element_located((By.NAME, "txt10"))
    )
    select = Select(select_element)
    select.select_by_value("1")

    time.sleep(2)
    modificar_nombre_centro(driver, wait, centro_info)
    time.sleep(2)

    # Seleccionar tipo/programa en txt6
    select_element = wait.until(
        EC.element_to_be_clickable((By.NAME, "txt6"))
    )
    dropdown = Select(select_element)
    dropdown.select_by_value("818")

    time.sleep(5)

    # Generar reporte y exportar a Excel
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
    timeout = 600  # segundos de espera máxima
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

# --- Procesamiento único de todos los archivos ---
cie10_prefixes = ('J09', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18',
                 'J20', 'J21', 'J22', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J47')

# Leer y combinar todos los archivos
dfs = []
for file in downloaded_files:
    try:
        df = pd.read_excel(file, skiprows=8)
        dfs.append(df)
    except Exception as e:
        print(f"Error leyendo {file}: {str(e)}")

if not dfs:
    print("No se encontraron archivos válidos para procesar")
    driver.quit()
    exit()

df_combined = pd.concat(dfs, ignore_index=True)

# Procesamiento de datos
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

# --- Finalizar ---
driver.quit()
print("Proceso completado exitosamente!")
