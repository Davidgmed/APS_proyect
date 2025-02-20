import os
import pandas as pd
from sqlalchemy import create_engine

# 1. Carpeta local con los archivos
folder_path = r"G:\Mi unidad\Actividades\Datosp4"

# 2. Leer todos los archivos Excel en la carpeta
excel_files = [f for f in os.listdir(folder_path) if f.endswith(('.xls', '.xlsx'))]

df_list = []
for file_name in excel_files:
    full_path = os.path.join(folder_path, file_name)
    # Ajusta skiprows según corresponda
    df = pd.read_excel(full_path, skiprows=12)
    df_list.append(df)
    print(file_name)

# 3. Concatenar todos los DataFrames en uno solo
print("Concatenando...")
atenciones_df = pd.concat(df_list, ignore_index=True)

# 4. Transformaciones iniciales
print(atenciones_df.head())
data = atenciones_df
print("Convirtiendo...")

# -- Convertir 'FECHA ATENCION' a datetime
if 'FECHA ATENCION' in data.columns:
    data['FECHA ATENCION'] = pd.to_datetime(
        data['FECHA ATENCION'], format='%d/%m/%Y', dayfirst=True, errors='coerce'
    )

# -- Convertir 'HORA ATENCION' a time
if 'HORA ATENCION' in data.columns:
    data['HORA ATENCION'] = pd.to_datetime(
        data['HORA ATENCION'], format='%H:%M:%S', errors='coerce'
    ).dt.time

# -- Combinar fecha+hora en 'FECHA HORA ATENCION' (como texto)
data['FECHA HORA ATENCION'] = data.apply(
    lambda row: (
        f"{row['FECHA ATENCION'].strftime('%d-%m-%Y')} {row['HORA ATENCION']}"
        if pd.notna(row.get('FECHA ATENCION')) and pd.notna(row.get('HORA ATENCION'))
        else None
    ),
    axis=1
)

# -- Renombrar 'FECHA CITA' a 'FECHA HORA CITA' (texto con formato)
if 'FECHA CITA' in data.columns:
    data.rename(columns={'FECHA CITA': 'FECHA HORA CITA'}, inplace=True)
    data['FECHA HORA CITA'] = pd.to_datetime(
        data['FECHA HORA CITA'], dayfirst=True, errors='coerce'
    ).dt.strftime('%d-%m-%Y %H:%M')

# -- Funciones para CIE-10
def get_cie10_1(code):
    return code[0] if pd.notna(code) and code else None

def get_cie10_2(code):
    return code[:2] if pd.notna(code) and len(code) > 1 else None

def get_cie10_3(code):
    return code.split('.')[0] if pd.notna(code) and code else None

def get_cie10_4(code):
    return code if pd.notna(code) and code else None

if 'CIE-10' in data.columns:
    data['CIE-10_1'] = data['CIE-10'].apply(get_cie10_1)
    data['CIE-10_2'] = data['CIE-10'].apply(get_cie10_2)
    data['CIE-10_3'] = data['CIE-10'].apply(get_cie10_3)
    data['CIE-10_4'] = data['CIE-10'].apply(get_cie10_4)

# Definir el orden de las columnas
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

# Crear columnas faltantes con None
for column in new_columns:
    if column not in data.columns:
        data[column] = None

# Reordenar
data_reordered = data[new_columns].copy()

# 1) Columnas que deben ser INT
int_cols = ["ANNOS", "MESES", "DIAS", "CANTIDAD ACT"]
for col in int_cols:
    if col in data_reordered.columns:
        data_reordered[col] = pd.to_numeric(data_reordered[col], errors="coerce").fillna(0).astype(int)

# 2) Diccionario de tipos finales
dict_types = {}
for c in data_reordered.columns:
    if c in int_cols:
        dict_types[c] = "int64"            # INT en SQL
    elif c == "FECHA ATENCION":
        dict_types[c] = "datetime64[ns]"  # DATETIME en SQL
    else:
        dict_types[c] = "string"          # VARCHAR en SQL

# 3) Aplica los tipos en un solo paso
data_final = data_reordered.astype(dict_types)

# 5. Subir los datos a SQL Server
print("Cargando a DB...")

engine = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS01/el_bosque?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

with engine.begin() as conn:
    data_final.to_sql(
        name='actividades',
        con=conn,
        if_exists='replace',
        index=False
    )

print("Datos cargados en la tabla 'actividades' de la base de datos 'el_bosque' en SQL Server.")
