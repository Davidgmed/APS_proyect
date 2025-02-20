import os
import pandas as pd
import pyodbc
import csv

# Límite de 12 MB en bytes
SIZE_LIMIT = 12 * 1024 * 1024

# Carpeta de archivos
folder_path = r"G:\Mi unidad\Actividades\Datosp4"

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

    if 'TIPO IDENTIFICACION' in data.columns:
        data.rename(columns={'TIPO IDENTIFICACION': 'NUMERO IDENTIFICACION'}, inplace=True)

    if 'NUMERO TIPO IDENTIFICACION' in data.columns:
        data['RUT'] = data['NUMERO TIPO IDENTIFICACION']
        data['RUT RESPONSABLE'] = data['NUMERO TIPO IDENTIFICACION']

    data.drop(columns=['TIPO IDENTIFICACION', 'NUMERO TIPO IDENTIFICACION'], inplace=True, errors='ignore')

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
    data['FECHA HORA ATENCION'] = data.apply(
        lambda row: (
            f"{row['FECHA ATENCION'].strftime('%d-%m-%Y')} {row['HORA ATENCION']}"
            if pd.notna(row.get('FECHA ATENCION')) and pd.notna(row.get('HORA ATENCION'))
            else None
        ),
        axis=1
    )

    # FECHA CITA -> FECHA HORA CITA
    if 'FECHA CITA' in data.columns:
        data.rename(columns={'FECHA CITA': 'FECHA HORA CITA'}, inplace=True)
        data['FECHA HORA CITA'] = pd.to_datetime(
            data['FECHA HORA CITA'], dayfirst=True, errors='coerce'
        ).dt.strftime('%d-%m-%Y %H:%M')

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
        data['CIE-10_1'] = data['CIE-10'].apply(get_cie10_1)
        data['CIE-10_2'] = data['CIE-10'].apply(get_cie10_2)
        data['CIE-10_3'] = data['CIE-10'].apply(get_cie10_3)
        data['CIE-10_4'] = data['CIE-10'].apply(get_cie10_4)

    # Orden de columnas
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
    for col in new_columns:
        if col not in data.columns:
            data[col] = None

    data_reordered = data[new_columns]

    # Exportar a CSV con separador ~ (puede ser |, pero ~ a veces es menos común en textos)
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
