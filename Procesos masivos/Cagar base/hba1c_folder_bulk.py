import os
import pandas as pd
import pyodbc
import csv
import numpy as np

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB, para manejar lotes de archivos grandes
folder_path = r"G:\Mi unidad\ECICEP\newglic"  # Carpeta de entrada
temp_csv_path = r"C:\Users\Quantum-Malloco\Downloads\newglic.csv"  # CSV temporal para BULK INSERT

# Ajusta aquí tu cadena de conexión
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS01;"
    "Database=el_bosque;"
    "Trusted_Connection=yes;"
)

# =============================================================================
# CREACIÓN DE TABLA
# =============================================================================
def crear_tabla_hba1c():
    """
    Crea la tabla hba1c en la BD el_bosque si no existe.
    Ajusta los tipos de datos de ser necesario.
    """
    create_table_sql = """
    CREATE TABLE el_bosque.dbo.hba1c (
        [SERVICIO SALUD] NVARCHAR(255),
        [ESTABLECIMIENTO] NVARCHAR(255),
        [RUT] NVARCHAR(50),
        [CODIGO FAMILIA] NVARCHAR(255),
        [NUMERO DE FICHA RAYEN] NVARCHAR(255),
        [NUMERO DE FICHA CODIGO ANTIGUO] NVARCHAR(255),
        [PACIENTE] NVARCHAR(255),
        [FECHA DE NACIMIENTO] NVARCHAR(255),
        [EDAD PACIENTE] NVARCHAR(255),
        [EDAD AÑO APLICACIÓN FORMULARIO] NVARCHAR(50),
        [EDAD MES APLICACIÓN FORMULARIO] NVARCHAR(50),
        [EDAD DÍAS APLICACIÓN FORMULARIO] NVARCHAR(50),
        [PUEBLO ORIGINARIO] NVARCHAR(255),
        [ALERTAS ADMINISTRATIVAS] NVARCHAR(255),
        [NACIONALIDAD] NVARCHAR(255),
        [SEXO] NVARCHAR(50),
        [SECTOR INSCRIPCION] NVARCHAR(255),
        [SECTOR CITA] NVARCHAR(255),
        [DIRECCIÓN] NVARCHAR(255),
        [COMUNA] NVARCHAR(255),
        [TELEFONO 1] NVARCHAR(50),
        [TELEFONO 2] NVARCHAR(50),
        [PREVISION] NVARCHAR(255),
        [CONVENIO] NVARCHAR(255),
        [SITUACION] NVARCHAR(255),
        [ESTADO] NVARCHAR(255),
        [FUNCIONARIO PASIVADOR] NVARCHAR(255),
        [ATEN ID] NVARCHAR(255),
        [FECHA ATENCION] NVARCHAR(255),
        [FECHA ULTIMO FORMULARIO] NVARCHAR(255),
        [FUNCIONARIO] NVARCHAR(255),
        [INSTRUMENTO] NVARCHAR(255),
        [ESTABLECIMIENTO INSCRIPCION] NVARCHAR(255),
        [57.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)] NVARCHAR(255),
        [58.- HEMOGLOBINA GLICOSILADA (HBA1C)] NVARCHAR(50)
    )
    """

    try:
        with pyodbc.connect(CONN_STR, autocommit=True) as conn:
            cursor = conn.cursor()
            # Verifica si la tabla existe
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'hba1c'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'hba1c' creada exitosamente.")
            else:
                print("Tabla 'hba1c' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise

# =============================================================================
# PROCESAR LOTE DE ARCHIVOS
# =============================================================================
def procesar_lote_hba1c(files_lote, lote_index, temp_csv_path):
    """
    Procesa un lote de archivos Excel, hace las transformaciones
    y realiza un BULK INSERT a la tabla el_bosque.dbo.hba1c.
    """
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")
    df_list = []

    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo: {file_name}")

        try:
            # Ajusta 'header' si la fila de encabezados está en otra posición.
            # En tu ejemplo, puede que necesites header=16 o 17, etc.
            df = pd.read_excel(full_path, header=16)
            df_list.append(df)
        except Exception as e:
            print(f"Error leyendo {file_name}: {str(e)}")
            continue

    if not df_list:
        print("No hay datos válidos para procesar.")
        return

    try:
        print(f"Lote {lote_index} - Transformando datos...")
        data = pd.concat(df_list, ignore_index=True)

        # 1. Limpieza de nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # 2. Combinar RUT y DV en un solo campo "RUT"
        #    (convirtiendo a str para evitar problemas con float)
        if 'DV' in data.columns:
            # Convertir RUT a entero (siempre que no sea nulo) y luego a cadena
            data['RUT'] = data['RUT'].apply(lambda x: str(int(x)) if pd.notnull(x) else '')
            # Finalmente, concatenar RUT y DV
            data['RUT'] = data['RUT'].str.strip() + '-' + data['DV'].astype(str).str.strip()

        # 3. Filtrar filas donde RUT sea nulo o vacío
        #    (por ejemplo, si RUT quedó "nan-")
        data = data[data['RUT'].notna()]
        data = data[~data['RUT'].str.contains('nan', na=False)]
        data = data[data['RUT'] != '-']

        # 4. Reemplazar nulos en "55.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)" con "01-01-2017"
        if '57.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)' in data.columns:
            data['57.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)'] = data['57.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)'].fillna('01-01-2017')

        # 5. Definir el orden de columnas finales (ajusta si tu archivo tiene nombres distintos)
        final_cols = [
            'SERVICIO SALUD',
            'ESTABLECIMIENTO',
            'RUT',
            'CODIGO FAMILIA',
            'NUMERO DE FICHA RAYEN',
            'NUMERO DE FICHA CODIGO ANTIGUO',
            'PACIENTE',
            'FECHA DE NACIMIENTO',
            'EDAD PACIENTE',
            'EDAD AÑO APLICACIÓN FORMULARIO',
            'EDAD MES APLICACIÓN FORMULARIO',
            'EDAD DÍAS APLICACIÓN FORMULARIO',
            'PUEBLO ORIGINARIO',
            'ALERTAS ADMINISTRATIVAS',
            'NACIONALIDAD',
            'SEXO',
            'SECTOR INSCRIPCION',
            'SECTOR CITA',
            'DIRECCIÓN',
            'COMUNA',
            'TELEFONO 1',
            'TELEFONO 2',
            'PREVISION',
            'CONVENIO',
            'SITUACION',
            'ESTADO',
            'FUNCIONARIO PASIVADOR',
            'ATEN ID',
            'FECHA ATENCION',
            'FECHA ULTIMO FORMULARIO',
            'FUNCIONARIO',
            'INSTRUMENTO',
            'ESTABLECIMIENTO INSCRIPCION',
            '57.- FECHA HEMOGLOBINA GLICOSILADA (HBA1C)',
            '58.- HEMOGLOBINA GLICOSILADA (HBA1C)'
        ]

        # Verificamos que todas las columnas existan en el dataframe;
        # si falta alguna, la creamos vacía para evitar errores.
        for col in final_cols:
            if col not in data.columns:
                data[col] = np.nan

        # Reordenar las columnas
        data = data[final_cols]

        # 6. Exportar a CSV temporal (con separador '~')
        data.to_csv(
            temp_csv_path,
            index=False,
            sep='~',
            quoting=csv.QUOTE_ALL,
            encoding='utf-8',
            escapechar='\\'
        )

        # 7. BULK INSERT a SQL Server
        with pyodbc.connect(CONN_STR) as conn:
            cursor = conn.cursor()
            bulk_insert_sql = f"""
            BULK INSERT el_bosque.dbo.hba1c
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

        print(f"¡Lote {lote_index} insertado! ({data.shape[0]} registros)")

    except Exception as e:
        print(f"Error procesando lote {lote_index}: {str(e)}")
    finally:
        # Eliminar CSV temporal
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

# =============================================================================
# PROCESAMIENTO PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    # 1. Listar archivos válidos en la carpeta
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Formularios_Clínicos_Ultimo_Valor") and f.endswith(".xlsx"):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar.")
        exit()

    # 2. Crear tabla si no existe
    crear_tabla_hba1c()

    # 3. Ordenar archivos por tamaño
    files_info.sort(key=lambda x: x[1])
    print(f"Archivos a procesar: {len(files_info)}")

    # 4. Procesar en lotes
    current_lote = []
    current_size = 0
    lote_index = 1

    for file_info in files_info:
        file_name, file_size = file_info

        # Si al agregar un archivo se supera el límite, procesamos el lote actual
        if current_size + file_size > SIZE_LIMIT and current_lote:
            procesar_lote_hba1c(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    # Procesar el último lote pendiente
    if current_lote:
        procesar_lote_hba1c(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")
