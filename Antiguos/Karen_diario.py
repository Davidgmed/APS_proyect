import os
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Configurar la opción para evitar downcasting silencioso en futuras versiones
pd.set_option('future.no_silent_downcasting', True)

# Configura las opciones de Chrome para manejar descargas y usar un perfil específico
download_dir = r"C:\Users\Quantum-Malloco\UrgenciaKaren"  # Reemplaza con la ruta del directorio de descargas
profile_path = r"C:\Users\Quantum-Malloco\AppData\Local\Google\Chrome\User Data\Profile 1"  # Ruta del perfil
chromedriver_path = r"C:\Users\Quantum-Malloco\chromedriver.exe"  # Renombrado para evitar conflicto

# Configura las opciones de Chrome
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument(f"user-data-dir={profile_path}")

# Configura el servicio de ChromeDriver
service = Service(executable_path=chromedriver_path)

# Inicia el WebDriver con las opciones y el servicio configurados
driver = webdriver.Chrome(service=service, options=chrome_options)

# Calcula la fecha del día anterior
fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_inicio = fecha_actual - timedelta(days=6)
fecha_fin = fecha_actual - timedelta(days=1)
#fecha_ayer = fecha_actual - timedelta(days=3)
fecha_ayer_str = fecha_ayer.strftime("%Y.%m.%d")
fecha_inicio_str = fecha_inicio.strftime("%Y.%m.%d")
fecha_fin_str = fecha_fin.strftime("%Y.%m.%d")

fecha_ayer_str_simple = fecha_ayer.strftime("%Y%m%d")
fecha_tabla = fecha_ayer.strftime("%d-%m-%Y")

# Construye la URL con la fecha del día anterior
login_url = "https://www.iris-salud.cl/reportportal/login.aspx"  # Reemplaza con la URL de inicio de sesión real
download_url = f"https://www.iris-salud.cl/reportportal/sql/ExportSql.aspx?mode=xls&reportType=2&reportId=541&txt1=S.S.%20Metropolitano%20Sur&txt2=El%20Bosque&txt3=25&txt4={fecha_inicio_str}&txt5={fecha_fin_str}&transpose=0"


try:
    # Navega a la página de inicio de sesión
    driver.get(login_url)

    # Espera a que los campos de entrada y el botón de inicio de sesión estén presentes
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.NAME, 'txtUserName')))
    password_field = wait.until(EC.presence_of_element_located((By.NAME, 'txtPassword')))
    login_button = wait.until(EC.presence_of_element_located((By.NAME, 'btnLogin')))

    # Introduce las credenciales
    username_field.send_keys('COM_EL_BOSQUE')
    password_field.send_keys('CEBosque_2022')

    # Haz clic en el botón de inicio de sesión
    login_button.click()

    # Espera a que la página de inicio de sesión redirija a la página deseada
    time.sleep(5)  # Ajusta el tiempo de espera según sea necesario

    # Navega a la URL de descarga del archivo
   # Abrir una nueva pestaña y navegar a la URL de descarga del archivo
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(download_url)


    # Espera a que se descargue el archivo (puedes ajustar el tiempo de espera)
    time.sleep(10)  # Ajusta el tiempo de espera según sea necesario

    # Captura el nombre del archivo descargado
    files = os.listdir(download_dir)
    downloaded_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)

    print(f"Archivo descargado: {downloaded_file}")

finally:
    # Cierra el navegador
    driver.quit()

# Definir los prefijos de CIE10 que queremos filtrar
cie10_prefixes = ('J09', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18', 'J20', 'J21', 'J22', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J47')

# Cargar y procesar el archivo descargado
df = pd.read_excel(downloaded_file, skiprows=8)

# Filtrar el DataFrame para que solo contenga filas donde CIE10 comience con los prefijos especificados
df_filtered = df[df['CIE10'].str.startswith(cie10_prefixes, na=False)].copy()

# Dividir la columna 'PRESION ARTERIAL' en dos columnas: 'sistolica' y 'diastolica'
df_filtered[['sistolica', 'diastolica']] = df_filtered['PRESION ARTERIAL'].str.split('/', expand=True)

# Convertir las columnas a valores numéricos
df_filtered['sistolica'] = pd.to_numeric(df_filtered['sistolica'], errors='coerce')
df_filtered['diastolica'] = pd.to_numeric(df_filtered['diastolica'], errors='coerce')

# Reemplazar los valores NaN en 'sistolica' con 0
df_filtered['sistolica'] = df_filtered['sistolica'].fillna(0)

# Definir una función para manejar duplicados en 'sistolica'
def handle_duplicates(group):
    if len(group) > 1 and (group['sistolica'] == 0).all():
        return group.drop_duplicates(subset=['CIE10'])
    return group

# Aplicar la función al DataFrame agrupado por 'ID', excluyendo las columnas de agrupación
df_filtered = df_filtered.groupby('ID', group_keys=False).apply(handle_duplicates).reset_index(drop=True)

# Agrupar por ID y seleccionar el registro con la mayor presión sistólica
df_result = df_filtered.loc[df_filtered.groupby('ID')['sistolica'].idxmax()]

# Reemplazar valores fuera de rango en df_result
df_result.replace([np.inf, -np.inf, np.nan], None, inplace=True)

# Definir las columnas a mantener
columns_to_keep = [
    'RUN', 'DV', 'NOMBRE', 'PRIMER APELLIDO', 'SEGUNDO APELLIDO',
    'SECTOR PACIENTE', 'ESTABLECIMIENTO', 'DIAGNOSTICO', 'CIE10',
    'FECHA ATENCION', 'PROFESIONAL RESPONSABLE', 'ULTIMA CATEGORIZACION',
    'SEXO', 'EDAD AÑOS'
]

# Seleccionar las columnas a mantener
df_result = df_result[columns_to_keep]

# Agrega la columna 'RUT'
df_result = df_result.dropna(subset=['RUN'])
df_result['RUN'] = df_result['RUN'].astype(int)
df_result['RUT'] = df_result['RUN'].astype(str) + '-' + df_result['DV'].astype(str)

# Elimina las columnas 'RUN' y 'DV'
df_result = df_result.drop(columns=['RUN', 'DV'])

# Agrega la columna 'fecha'
df_result['fecha'] = fecha_tabla

# Ordena las columnas, asegurando que 'RUT' esté en la posición deseada
columns_order = ['fecha', 'RUT'] + [col for col in columns_to_keep if col not in ['RUN', 'DV']]

df_result = df_result[columns_order]

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

# Genera el nombre del archivo de salida usando la fecha
output_filename = f'archivo_procesado_{fecha_ayer_str_simple}.xlsx'
output_filepath = os.path.join(download_dir, output_filename)

# Crear un nuevo archivo Excel con diferentes hojas para cada sector
with pd.ExcelWriter(output_filepath) as writer:
    for establishment, sector in establishment_to_sector.items():
        df_sector = df_result[df_result['ESTABLECIMIENTO'] == establishment]
        df_sector.to_excel(writer, sheet_name=sector, index=False)

    # Filtrar y guardar los registros que no coinciden con ningún establecimiento especificado
    df_externos = df_result[~df_result['ESTABLECIMIENTO'].isin(establishment_to_sector.keys())]
    df_externos.to_excel(writer, sheet_name='Externos', index=False)

print(output_filepath)

# Autenticación y conexión a Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\Hp\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)

# Abre la hoja de cálculo
spreadsheet = client.open("Casos respiratorios red de urgencia 2024")

# Función para agregar DataFrame a una hoja específica
def append_df_to_sheet(df, sheet_name):
    worksheet = spreadsheet.worksheet(sheet_name)
    existing_data = worksheet.get_all_values()
    existing_df = pd.DataFrame(existing_data)
    start_row = len(existing_df) + 1

    rows = df.values.tolist()
    worksheet.append_rows(rows, table_range=f"A{start_row}")

# Agregar los datos procesados a las hojas correspondientes en Google Sheets
for establishment, sector in establishment_to_sector.items():
    df_sector = df_result[df_result['ESTABLECIMIENTO'] == establishment]
    if not df_sector.empty:
        append_df_to_sheet(df_sector, sector)
        print (sector , "actualizado")

# Filtrar y guardar los registros que no coinciden con ningún establecimiento especificado
df_externos = df_result[~df_result['ESTABLECIMIENTO'].isin(establishment_to_sector.keys())]
if not df_externos.empty:
    append_df_to_sheet(df_externos, 'Externos')

print("Actualización exitosa!")