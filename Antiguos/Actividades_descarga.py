import os
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine

# Configurar la opción para evitar downcasting silencioso en futuras versiones
# pd.set_option('future.no_silent_downcasting', True)


# Configura las opciones de Chrome para manejar descargas y usar un perfil específico
download_dir = r"G:\Mi unidad\Actividades\Datosp4"  # Reemplaza con la ruta del directorio de descargas
profile_path = r"C:\Users\Quantum-Malloco\AppData\Local\Google\Chrome\User Data\Profile 1"  # Ruta del perfil 11

chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument(f"user-data-dir={profile_path}")

# Listas de valores
centros = [
    2027, 4161, 4185, 4210, 4240, 4242, 4244, 4246, 4247, 4253, 4254, 4255, 4258, 4271, 4691
]
# centros = [
#    2027, 4161
# ]


# Profesionales (según lo que necesites, ajusta esta lista si es necesario)
profs = [72]

# Fechas
inicio_fecha = datetime.strptime("08-07-2024", "%d-%m-%Y")
fin_fecha = datetime.strptime("14-07-2024", "%d-%m-%Y")

# Formato de fechas en la URL
inicio_txt4 = inicio_fecha.strftime("%Y.%m.%d")
fin_txt7 = fin_fecha.strftime("%Y.%m.%d")

# Generar URLs
base_url = "https://www.iris-salud.cl/reportportal/sql/ExportSql.aspx?mode=xls&reportType=2&reportId=2314&txt1=S.S.%20Metropolitano%20Sur&txt2=El%20Bosque"

urls = []

for centro in centros:
    for prof in profs:
        url = f"{base_url}&txt3={centro}&txt4={inicio_txt4}&txt7={fin_txt7}&txt8=1&txt10={prof}&txt11=3&transpose=0"
        urls.append(url)

# Inicia el WebDriver con las opciones configuradas
driver = webdriver.Chrome(options=chrome_options)

# Construye la URL con la fecha del día anterior
login_url = "https://www.iris-salud.cl/reportportal/login.aspx"  # Reemplaza con la URL de inicio de sesión real

downloaded_files = []

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
    time.sleep(1)  # Ajusta el tiempo de espera según sea necesario

    # Abrir una nueva pestaña y navegar a cada URL de descarga
    for url in urls:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(url)
        time.sleep(5)  # Ajusta el tiempo de espera según sea necesario
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # Captura el nombre del archivo descargado
        files = os.listdir(download_dir)
        downloaded_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
        downloaded_files.append(downloaded_file)
        print(f"Archivo descargado: {downloaded_file}")

    # Espera a que se descarguen todos los archivos (puedes ajustar el tiempo de espera)
    time.sleep(10)  # Ajusta el tiempo de espera según sea necesario
finally:
    # Cierra el navegador
    driver.quit()

# Cargar archivos descargados en un DataFrame
atenciones = []
for file in downloaded_files:
    df = pd.read_excel(file, skiprows=12)
    atenciones.append(df)

# Concatenar todos los DataFrames en uno solo
atenciones_df = pd.concat(atenciones, ignore_index=True)

# Ahora puedes realizar las transformaciones necesarias en atenciones_df o guardarlo en una base de datos
print(atenciones_df.head())

# Cargar los datos usando la fila 12 como cabecera
data = atenciones_df

# Convertir las columnas de fechas y horas al formato deseado
data['FECHA ATENCION'] = pd.to_datetime(data['FECHA ATENCION'], format='%d/%m/%Y', dayfirst=True)
data['HORA ATENCION'] = pd.to_datetime(data['HORA ATENCION'], format='%H:%M:%S').dt.time

# Combinar "FECHA ATENCION" y "HORA ATENCION" en "FECHA HORA ATENCION" con el formato correcto
data['FECHA HORA ATENCION'] = data.apply(
    lambda row: f"{row['FECHA ATENCION'].strftime('%d-%m-%Y')} {row['HORA ATENCION']}", axis=1)

# Renombrar "FECHA CITA" a "FECHA HORA CITA" y asegurarse del formato correcto
if 'FECHA CITA' in data.columns:
    data.rename(columns={'FECHA CITA': 'FECHA HORA CITA'}, inplace=True)
    data['FECHA HORA CITA'] = pd.to_datetime(data['FECHA HORA CITA'], dayfirst=True).dt.strftime('%d-%m-%Y %H:%M')


def get_cie10_1(code):
    return code[0] if pd.notna(code) and code else None


def get_cie10_2(code):
    return code[:2] if pd.notna(code) and len(code) > 1 else None


def get_cie10_3(code):
    return code.split('.')[0] if pd.notna(code) and code else None


def get_cie10_4(code):
    return code if pd.notna(code) and code else None


# Aplicar las funciones para crear las nuevas columnas
data['CIE-10_1'] = data['CIE-10'].apply(get_cie10_1)
data['CIE-10_2'] = data['CIE-10'].apply(get_cie10_2)
data['CIE-10_3'] = data['CIE-10'].apply(get_cie10_3)
data['CIE-10_4'] = data['CIE-10'].apply(get_cie10_4)

# Definir el nuevo orden de las columnas
new_columns = [
    "ATEN ID", "ACTIVIDAD Y O PROCEDIMIENTO", "N", "ESTADO", "FECHA HORA CITA",
    "FECHA HORA ATENCION", "RENDIMIENTO", "DURACION", "TIPO DE ATENCION", "TELECONSULTA",
    "SECTOR", "SECTOR CITA", "FUNCIONARIO", "INSTRUMENTO", "RUT",
    "FECHA DE NACIMIENTO", "NUMERO IDENTIFICACION", "RUT RESPONSABLE", "FICHAS",
    "PACIENTE", "CICLO VITAL", "ANNOS", "MESES", "DIAS", "SEXO", "PREVISION", "TRAMO",
    "ALERTAS ADMINISTRATIVAS", "PUEBLO ORIGINARIO", "PAIS DE ORIGEN",
    "NACIONALIDAD", "ESTRATIFICACION DE RIESGO", "CANTIDAD ACT", "CIE-10",
    "DIAGNOSTICO", "INCIDENCIA", "ESTADO DIAG", "ES AUGE", "PSAL_DESC",
    "CENTRO INSCRIPCION PACIENTE", "TELEFONOS", "TELEFONO MOVIL",
    "ESTABLECIMIENTO DE ATENCION", "CIE-10_1", "CIE-10_2", "CIE-10_3", "CIE-10_4"
]

# Agregar cualquier columna faltante con valores None por defecto
for column in new_columns:
    if column not in data.columns:
        data[column] = None

# Reordenar el DataFrame según el nuevo orden de las columnas
data_reordered = data[new_columns]


table = 'actividades'
database = 'el_bosque'


# Cadena de conexión con la base 'el_bosque' y trusted_connection
engine = create_engine(
    "mssql+pyodbc://localhost/el_bosque?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes"
)

data_reordered.to_sql(
    name=table,
    con=engine,
    if_exists='append',
    index=False
)
print(f"Datos cargados en la tabla {table} de la base de datos {database} en SQL Server.")