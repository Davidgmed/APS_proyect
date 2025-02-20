import os
import pandas as pd
import pyodbc
import csv

# Límite de 12 MB en bytes
SIZE_LIMIT = 12 * 1024 * 1024

# Carpeta de archivos
folder_path = r"G:\Mi unidad\Actividades\Datosp4"

def crear_tabla():
    """Crea la tabla si no existe con la nueva estructura"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Script para crear la tabla con la nueva estructura
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='actividades' AND xtype='U')
    CREATE TABLE actividades (
        [ATEN ID] VARCHAR(50),
        [ACTIVIDAD_PROCEDIMIENTO] NVARCHAR(MAX),
        [N] VARCHAR(10),
        [ESTADO] NVARCHAR(50),
        [FECHA_HORA_CITA] DATETIME,
        [FECHA_HORA_ATENCION] DATETIME,
        [RENDIMIENTO] INT,
        [DURACION] INT,
        [TIPO_ATENCION] NVARCHAR(100),
        [TELECONSULTA] NVARCHAR(10),
        [SECTOR] NVARCHAR(100),
        [SECTOR_CITA] NVARCHAR(100),
        [FUNCIONARIO] NVARCHAR(255),
        [INSTRUMENTO] NVARCHAR(100),
        [RUT] VARCHAR(20),
        [FECHA_NACIMIENTO] DATE,
        [NUMERO_IDENTIFICACION] VARCHAR(20),
        [FICHAS] NVARCHAR(100),
        [PACIENTE] NVARCHAR(255),
        [CICLO_VITAL] NVARCHAR(50),
        [ANNOS] INT,
        [MESES] INT,
        [DIAS] INT,
        [SEXO] NVARCHAR(20),
        [PREVISION] NVARCHAR(100),
        [TRAMO] NVARCHAR(50),
        [ALERTAS_ADMINISTRATIVAS] NVARCHAR(255),
        [PUEBLO_ORIGINARIO] NVARCHAR(100),
        [PAIS_ORIGEN] NVARCHAR(100),
        [NACIONALIDAD] NVARCHAR(100),
        [ESTRATIFICACION_RIESGO] NVARCHAR(50),
        [CANTIDAD_ACT] INT,
        [CIE_10] NVARCHAR(20),
        [DIAGNOSTICO] NVARCHAR(MAX),
        [INCIDENCIA] NVARCHAR(50),
        [ESTADO_DIAG] NVARCHAR(50),
        [ES_AUGE] NVARCHAR(10),
        [PSAL_DESC] NVARCHAR(MAX),
        [CENTRO_INSCRIPCION] NVARCHAR(255),
        [TELEFONOS] NVARCHAR(100),
        [TELEFONO_MOVIL] NVARCHAR(100),
        [ESTABLECIMIENTO_ATENCION] NVARCHAR(255),
        [CIE_10_1] NVARCHAR(5),
        [CIE_10_2] NVARCHAR(5),
        [CIE_10_3] NVARCHAR(10),
        [CIE_10_4] NVARCHAR(15)
    )
    """
    cursor.execute(create_table_sql)
    conn.commit()
    
    # Limpiar tabla si ya existe
    cursor.execute("DELETE FROM actividades")
    conn.commit()
    
    cursor.close()
    conn.close()
    print("Tabla 'actividades' creada o limpiada exitosamente.")

def procesar_lote(files_lote, lote_index, temp_csv_path):
    """Lee y concatena archivos del lote, hace transformaciones, exporta CSV y ejecuta BULK INSERT."""
    if not files_lote:
        return  # Evita procesar si no hay archivos

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")

    df_list = []
    for file_info in files_lote:
        file_name, _ = file_info  # file_info = (nombre, tamaño)
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo archivo: {file_name}")

        # Lee con skiprows si es necesario
        df = pd.read_excel(full_path, skiprows=12)
        df_list.append(df)

    print(f"Lote {lote_index} - Concatenando DataFrames...")
    atenciones_df = pd.concat(df_list, ignore_index=True)

    # ------------------- Transformaciones -------------------------
    data = atenciones_df

    # FECHA ATENCION
    if 'FECHA ATENCION' in data.columns:
        data['FECHA ATENCION'] = pd.to_datetime(
            data['FECHA ATENCION'], format='%d/%m/%Y', dayfirst=True, errors='coerce'
        )

    # HORA ATENCION
    if 'HORA ATENCION' in data.columns:
        data['HORA ATENCION'] = pd.to_datetime(
            data['HORA ATENCION'], format='%H:%M:%S', errors='coerce'
        ).dt.time

    # Combinar FECHA + HORA en FECHA HORA ATENCION
    data['FECHA_HORA_ATENCION'] = data.apply(
        lambda row: (
            pd.to_datetime(f"{row['FECHA ATENCION'].strftime('%Y-%m-%d')} {row['HORA ATENCION']}")
            if pd.notna(row.get('FECHA ATENCION')) and pd.notna(row.get('HORA ATENCION'))
            else None
        ),
        axis=1
    )

    # FECHA CITA -> FECHA HORA CITA
    if 'FECHA CITA' in data.columns:
        data.rename(columns={'FECHA CITA': 'FECHA_HORA_CITA'}, inplace=True)
        data['FECHA_HORA_CITA'] = pd.to_datetime(
            data['FECHA_HORA_CITA'], dayfirst=True, errors='coerce'
        )

    # FECHA DE NACIMIENTO
    if 'FECHA DE NACIMIENTO' in data.columns:
        data['FECHA DE NACIMIENTO'] = pd.to_datetime(
            data['FECHA DE NACIMIENTO'], dayfirst=True, errors='coerce'
        )

    # Columnas numéricas (ANNOS, MESES, DIAS)
    numeric_cols = ["ANNOS", "MESES", "DIAS"]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0).astype(int)

    # CIE-10
    def get_cie10_1(code):
        return code[0] if pd.notna(code) and code else None

    def get_cie10_2(code):
        return code[:2] if pd.notna(code) and len(code) > 1 else None

    def get_cie10_3(code):
        return code.split('.')[0] if pd.notna(code) and code else None

    def get_cie10_4(code):
        return code if pd.notna(code) and code else None

    if 'CIE-10' in data.columns:
        data['CIE_10_1'] = data['CIE-10'].apply(get_cie10_1)
        data['CIE_10_2'] = data['CIE-10'].apply(get_cie10_2)
        data['CIE_10_3'] = data['CIE-10'].apply(get_cie10_3)
        data['CIE_10_4'] = data['CIE-10'].apply(get_cie10_4)

    # Mapeo de columnas según la nueva estructura
    column_mapping = {
        'RUT FUNCIONARIO': 'RUT',
        'NUMERO TIPO IDENTIFICACION': 'NUMERO_IDENTIFICACION',
        'MOTIVO DE INSCRIPCION': 'MOTIVO_INSCRIPCION',
        'TIPO DE ATENCION': 'TIPO_ATENCION',
        'FECHA DE NACIMIENTO': 'FECHA_NACIMIENTO',
        'ALERTAS ADMINISTRATIVAS': 'ALERTAS_ADMINISTRATIVAS',
        'PUEBLO ORIGINARIO': 'PUEBLO_ORIGINARIO',
        'PAIS DE ORIGEN': 'PAIS_ORIGEN',
        'ESTRATIFICACION DE RIESGO': 'ESTRATIFICACION_RIESGO',
        'ACTIVIDAD Y O PROCEDIMIENTO': 'ACTIVIDAD_PROCEDIMIENTO',
        'CANTIDAD ACT': 'CANTIDAD_ACT',
        'ESTADO DIAG': 'ESTADO_DIAG',
        'ES AUGE': 'ES_AUGE',
        'PSAL DESC': 'PSAL_DESC',
        'CENTRO INSCRIPCION PACIENTE': 'CENTRO_INSCRIPCION',
        'TELEFONO MOVIL': 'TELEFONO_MOVIL',
        'ESTABLECIMIENTO DE ATENCION': 'ESTABLECIMIENTO_ATENCION',
        'CIE-10': 'CIE_10'
    }
    
    data.rename(columns=column_mapping, inplace=True)

    # Orden de columnas (ajustado a la nueva estructura)
    new_columns = [
        "ATEN ID", "ACTIVIDAD_PROCEDIMIENTO", "N", "ESTADO", "FECHA_HORA_CITA",
        "FECHA_HORA_ATENCION", "RENDIMIENTO", "DURACION", "TIPO_ATENCION", "TELECONSULTA",
        "SECTOR", "SECTOR CITA", "FUNCIONARIO", "INSTRUMENTO", "RUT",
        "FECHA_NACIMIENTO", "NUMERO_IDENTIFICACION", "FICHAS",
        "PACIENTE", "CICLO VITAL", "ANNOS", "MESES", "DIAS", "SEXO", "PREVISION", "TRAMO",
        "ALERTAS_ADMINISTRATIVAS", "PUEBLO_ORIGINARIO", "PAIS_ORIGEN",
        "NACIONALIDAD", "ESTRATIFICACION_RIESGO", "CANTIDAD_ACT", "CIE_10",
        "DIAGNOSTICO", "INCIDENCIA", "ESTADO_DIAG", "ES_AUGE", "PSAL_DESC",
        "CENTRO_INSCRIPCION", "TELEFONOS", "TELEFONO_MOVIL",
        "ESTABLECIMIENTO_ATENCION", "CIE_10_1", "CIE_10_2", "CIE_10_3", "CIE_10_4"
    ]
    
    # Asegurar que todas las columnas existan
    for col in new_columns:
        if col not in data.columns:
            data[col] = None

    data_reordered = data[new_columns]

    # Exportar a CSV con separador ~
    data_reordered.to_csv(
        temp_csv_path,
        index=False,
        sep='~',
        quoting=csv.QUOTE_ALL,
        escapechar='\\',
        encoding='utf-8'
    )

    # BULK INSERT
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Usando SQL Server 2022+ con FORMAT='CSV' y separador ~
    bulk_insert_sql = f"""
    BULK INSERT el_bosque.dbo.actividades
    FROM '{temp_csv_path}'
    WITH (
        FORMAT = 'CSV',
        FIELDTERMINATOR = '~',
        ROWTERMINATOR = '\\n',
        FIRSTROW = 2,
        CODEPAGE = '65001',
        TABLOCK
    );
    """
    cursor.execute(bulk_insert_sql)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"¡Datos del lote {lote_index} cargados con BULK INSERT!")

    # Eliminar CSV temporal para no llenar disco
    if os.path.exists(temp_csv_path):
        os.remove(temp_csv_path)
        print(f"Archivo temporal {temp_csv_path} eliminado.")


# -----------------------------------------------------------------------------
# Crear la tabla primero
crear_tabla()

# Listar archivos y obtener su tamaño. Ordenar de menor a mayor (para agrupar mejor).
files_info = []
for f in os.listdir(folder_path):
    if f.endswith(('.xls', '.xlsx')):
        full_path = os.path.join(folder_path, f)
        size_bytes = os.path.getsize(full_path)
        files_info.append((f, size_bytes))

# Ordenar de menor a mayor
files_info.sort(key=lambda x: x[1])

print(f"Total de archivos: {len(files_info)}")

current_lote = []
current_size = 0
lote_index = 1

# Ruta de CSV temporal (siempre la misma, se va reciclando)
temp_csv_path = r"G:\Mi unidad\Actividades\actividades_temp.csv"

for file_info in files_info:
    file_name, file_size = file_info

    # Si agregar este archivo excede el límite y el lote actual no está vacío, procesar lote
    if current_size + file_size > SIZE_LIMIT and current_lote:
        procesar_lote(current_lote, lote_index, temp_csv_path)
        lote_index += 1
        current_lote = []
        current_size = 0

    # Agregar el archivo al lote actual
    current_lote.append(file_info)
    current_size += file_size

# Procesar el último lote si quedan archivos pendientes
if current_lote:
    procesar_lote(current_lote, lote_index, temp_csv_path)

print("\nProceso completado. Archivos ordenados por tamaño y agrupados en lotes de hasta 12 MB.")