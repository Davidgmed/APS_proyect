# -*- coding: utf-8 -*-
"""
Descarga reportes de hemoglucotest, consolida la nueva estructura (encabezado interno),
conserva por (RUN, FECHA REGISTRO HEMOGLUCOTEST) la medición con mayor VALOR HEMOGLUCOTEST,
y escribe en Google Sheets 'Casos glicemia descompensada' en hojas por ESTABLECIMIENTO.

Requisitos:
- pip install selenium pandas gspread oauth2client openpyxl
- Chromedriver compatible con tu Chrome
- Service account con acceso de edición al Google Sheet
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ============================ CONFIGURACIÓN BÁSICA ============================

# --- Configuración del directorio de descargas ---
download_dir = r"G:\Mi unidad\ECICEP\descompensados"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Configuración del driver con opciones para establecer el directorio de descargas
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
spreadsheet = client.open("Casos glicemia descompensada")

def open_or_create_worksheet(spreadsheet_obj, title: str):
    """Abre una hoja por título o la crea si no existe."""
    try:
        return spreadsheet_obj.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet_obj.add_worksheet(title=title, rows=1000, cols=20)

def append_df_to_sheet(df, sheet_name):
    """Función para agregar datos a una hoja específica en Google Sheets."""
    worksheet = open_or_create_worksheet(spreadsheet, sheet_name)
    existing_data = worksheet.get_all_values()
    if not existing_data:
        worksheet.append_row(list(df.columns))  # si está vacía, escribir encabezados
    start_row = len(existing_data) + 1
    rows = df.values.tolist()
    if rows:
        worksheet.append_rows(rows, table_range=f"A{start_row}")

# ============================ LOGIN Y DESCARGAS ===============================

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
time.sleep(1)

# Seleccionar licencia
select_div = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
))
time.sleep(1)
select_div.click()
time.sleep(1)

menu_item = wait.until(EC.element_to_be_clickable(
    (By.XPATH,
    #"//li[@data-value='1130' and contains(.,'SAPU Condores de Chile S.S. Metropolitano Sur')]")
    "//li[@data-value='1139' and contains(.,'Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur')]")
))
time.sleep(1)
menu_item.click()
time.sleep(2)

confirmar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirmar')]")))
confirmar_button.click()

time.sleep(10)

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
downloaded_files: List[str] = []

# --- Descargar todos los archivos primero ---
for centro_info in centros:
    # Registra los archivos existentes antes de iniciar la descarga
    archivos_previos = set(os.listdir(download_dir))

    # Abrir nueva pestaña y ejecutar la descarga
    driver.execute_script(
        "window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=677', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Completar fechas y demás acciones...
    fecha_inicio = wait.until(EC.presence_of_element_located((By.ID, "txt4")))
    fecha_inicio.clear()
    fecha_inicio.send_keys("30/06/2025")
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    fecha_fin = wait.until(EC.presence_of_element_located((By.ID, "txt5")))
    fecha_fin.clear()
    fecha_fin.send_keys("06/07/2025")
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

    time.sleep(2)
    modificar_nombre_centro(driver, wait, centro_info)
    time.sleep(2)

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
        xlsx_nuevos = [f for f in nuevos_archivos if f.lower().endswith('.xlsx')]
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

# ====================== PROCESAMIENTO & CARGA A GOOGLE SHEETS =================

# --- Clasificación de establecimiento -> hoja de destino ---
ESTABLISHMENT_TO_SHEET: Dict[str, str] = {
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

# Columnas esperadas en el reporte
REQUIRED_COLUMNS = {
    'NOMBRE PACIENTE',
    'PRIMER APELLIDO',
    'SEGUNDO APELLIDO',
    'RUN',
    'DV',
    'SECTOR',
    'FECHA REGISTRO HEMOGLUCOTEST',
    'VALOR HEMOGLUCOTEST',
    'ESTABLECIMIENTO DE INSCRIPCION'
}

# Mapeo de salida solicitado
RENAME_MAP = {
    'NOMBRE PACIENTE': 'Nombre',
    'PRIMER APELLIDO': 'PrimerAp',
    'SEGUNDO APELLIDO': 'SegundoAp',
    'RUN': 'RUN',
    'DV': 'DV',
    'SECTOR': 'Sector',
    'FECHA REGISTRO HEMOGLUCOTEST': 'Fecha',
    'VALOR HEMOGLUCOTEST': 'Valor'
}
OUTPUT_COLUMNS = ['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor']

def list_xlsx_files(folder: str) -> List[str]:
    """Lista archivos .xlsx (no temporales) de un folder."""
    all_files = []
    for f in os.listdir(folder):
        if f.lower().endswith(".xlsx") and not f.startswith("~$"):
            all_files.append(os.path.join(folder, f))
    return all_files

def read_report_table(path: str, sheet_name=None) -> pd.DataFrame:
    """
    Lee una hoja de reporte donde la tabla real comienza varias filas más abajo.
    Detecta la fila cuyo primer valor sea 'NOMBRE PACIENTE' y usa esa fila como header.
    Devuelve DataFrame con cabecera y sin columnas vacías.
    """
    df_raw = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str)
    header_row_idx = None
    for i in range(min(80, len(df_raw))):
        first_cell = str(df_raw.iloc[i, 0]).strip() if pd.notna(df_raw.iloc[i, 0]) else ""
        if first_cell.upper() == "NOMBRE PACIENTE":
            header_row_idx = i
            break

    if header_row_idx is None:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    else:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row_idx, dtype=str)

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how='all', axis=1)
    df = df.dropna(how='all', axis=0)
    return df

def read_all_reports_from_file(xlsx_path: str) -> List[pd.DataFrame]:
    """Lee todas las hojas válidas de un .xlsx siguiendo la estructura de reporte."""
    out = []
    try:
        xls = pd.ExcelFile(xlsx_path)
        for sh in xls.sheet_names:
            try:
                df_sh = read_report_table(xlsx_path, sheet_name=sh)
                if REQUIRED_COLUMNS.issubset(set(df_sh.columns)):
                    out.append(df_sh.copy())
            except Exception:
                continue
    except Exception as e:
        print(f"[WARN] No se pudo abrir {xlsx_path}: {e}")
    return out

def consolidate_and_pick_max(all_frames: List[pd.DataFrame]) -> pd.DataFrame:
    """Consolida frames, normaliza, y mantiene máximo Valor por (RUN, Fecha)."""
    if not all_frames:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    df_all = pd.concat(all_frames, ignore_index=True)

    # Normalizar espacios y tipos básicos
    for col in [
        'RUN', 'DV', 'SECTOR', 'FECHA REGISTRO HEMOGLUCOTEST', 'VALOR HEMOGLUCOTEST',
        'NOMBRE PACIENTE', 'PRIMER APELLIDO', 'SEGUNDO APELLIDO', 'ESTABLECIMIENTO DE INSCRIPCION'
    ]:
        if col in df_all.columns:
            df_all[col] = df_all[col].astype(str).str.strip()

    df_all['VALOR HEMOGLUCOTEST'] = pd.to_numeric(df_all.get('VALOR HEMOGLUCOTEST', pd.NA), errors='coerce')

    # Filtrar filas válidas para criterio
    df_valid = df_all.dropna(subset=['RUN', 'FECHA REGISTRO HEMOGLUCOTEST', 'VALOR HEMOGLUCOTEST']).copy()

    # Conservar máximo por (RUN, FECHA)
    idx_max = df_valid.groupby(['RUN', 'FECHA REGISTRO HEMOGLUCOTEST'])['VALOR HEMOGLUCOTEST'].idxmax()
    df_max = df_valid.loc[idx_max].copy()

    return df_max

def build_output(df_max: pd.DataFrame) -> pd.DataFrame:
    """Recorta/renombra a las columnas de salida y mantiene ESTABLECIMIENTO para roteo."""
    missing = REQUIRED_COLUMNS - set(df_max.columns)
    if missing:
        raise ValueError(f"Faltan columnas esperadas en los datos consolidados: {missing}")

    df_out = df_max[list(RENAME_MAP.keys()) + ['ESTABLECIMIENTO DE INSCRIPCION']].rename(columns=RENAME_MAP)
    df_out = df_out[['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor', 'ESTABLECIMIENTO DE INSCRIPCION']]
    return df_out

# --- Leer/validar descargas ---
if not downloaded_files:
    # Si por alguna razón no se pobló la lista (o quieres reusar el procesamiento solo),
    # buscamos todos los .xlsx en download_dir.
    downloaded_files = list_xlsx_files(download_dir)

dfs_validas: List[pd.DataFrame] = []
for file in downloaded_files:
    try:
        dfs_validas.extend(read_all_reports_from_file(file))
    except Exception as e:
        print(f"Error leyendo {file}: {str(e)}")

if not dfs_validas:
    print("No se encontraron archivos válidos para procesar")
    driver.quit()
    raise SystemExit

# --- Consolidar y quedarnos con la medición máxima por RUN+Fecha ---
df_max = consolidate_and_pick_max(dfs_validas)

# --- Preparar DataFrame final con columnas solicitadas ---
df_out = build_output(df_max)

# --- Escribir por ESTABLECIMIENTO DE INSCRIPCION usando la clasificación ---
total_escritos = 0

# 1) Mapeables (van a la hoja/sector correspondiente)
for est, hoja in ESTABLISHMENT_TO_SHEET.items():
    block = df_out[df_out['ESTABLECIMIENTO DE INSCRIPCION'] == est].drop(columns=['ESTABLECIMIENTO DE INSCRIPCION'])
    if not block.empty:
        block = block[['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor']]
        append_df_to_sheet(block, hoja)
        total_escritos += len(block)
        print(f"Agregados {len(block)} registros a hoja '{hoja}'")

# 2) No mapeables (Externos)
externos = df_out[~df_out['ESTABLECIMIENTO DE INSCRIPCION'].isin(ESTABLISHMENT_TO_SHEET.keys())] \
          .drop(columns=['ESTABLECIMIENTO DE INSCRIPCION'])
if not externos.empty:
    externos = externos[['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor']]
    append_df_to_sheet(externos, 'Externos')
    total_escritos += len(externos)
    print(f"Agregados {len(externos)} registros a hoja 'Externos'")

# --- Limpieza opcional: eliminar archivos descargados tras procesar ---
for file in downloaded_files:
    try:
        os.remove(file)
        print(f"Archivo eliminado: {file}")
    except Exception:
        pass

# --- Finalizar ---
driver.quit()
print(f"Proceso completado exitosamente. Registros escritos: {total_escritos}")
