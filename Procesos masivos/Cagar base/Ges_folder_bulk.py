import os
import pandas as pd
import pyodbc
import csv
import re
from datetime import datetime

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\ges_temp.csv"


def crear_tabla_ges():
    """Crea la tabla ges si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )

    create_table_sql = """
    CREATE TABLE el_bosque.dbo.ges (
        [ESTABLECIMIENTO ATENCION] NVARCHAR(255),
        [RUN] NVARCHAR(20),
        [DV] NVARCHAR(2),
        [FICHA] NVARCHAR(50),
        [NUMERO DE FICHA] NVARCHAR(100),
        [ESTABLECIMIENTO INSCRIPCION] NVARCHAR(255),
        [NOMBRES] NVARCHAR(255),
        [PRIMER APELLIDO] NVARCHAR(255),
        [SEGUNDO APELLIDO] NVARCHAR(255),
        [FECHA ATENCION] DATE,
        [FECHA DE NACIMIENTO] DATE,
        [SEXO] NVARCHAR(20),
        [EDAD] NVARCHAR(50),
        [DIRECCION] NVARCHAR(500),
        [TELEFONO 1] NVARCHAR(20),
        [TELEFONO 2] NVARCHAR(20),
        [CELULAR] NVARCHAR(20),
        [SECTOR] NVARCHAR(50),
        [PREVISION] NVARCHAR(50),
        [CLASIFICACIÓN BENEFICIARIO FONASA] NVARCHAR(100),
        [NOMBRE FUNCIONARIO] NVARCHAR(255),
        [PRIMER APELLIDO FUNCIONARIO] NVARCHAR(255),
        [SEGUNO APELLIDO FUNCIONARIO] NVARCHAR(255),
        [PROFESIONAL O TECNICO] NVARCHAR(100),
        [PROBLEMA DE SALUD] NVARCHAR(255),
        [CIE 10] NVARCHAR(20),
        [ESTADO DIAGNOSTICO] NVARCHAR(50),
        [DIAGNOSTICO] NVARCHAR(500),
        [INCIDENCIA] NVARCHAR(50),
        [LlaveGES2] NVARCHAR(255)
    )
    """

    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ges'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'ges' creada exitosamente.")
            else:
                print("Tabla 'ges' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_ges(files_lote, lote_index, temp_csv_path):
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")

    df_list = []
    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo: {file_name}")

        try:
            df = pd.read_excel(full_path, header=8)  # Los encabezados están en la fila 9 (0-indexed)
            df_list.append(df)
        except Exception as e:
            print(f"Error leyendo {file_name}: {str(e)}")
            continue

    if not df_list:
        print("No hay datos válidos para procesar")
        return

    try:
        print(f"Lote {lote_index} - Transformando datos...")
        data = pd.concat(df_list, ignore_index=True)

        # Limpiar nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # Limpieza de campos clave
        data['RUN'] = (
            data['RUN']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)  # quita el ".0" final típico de los floats
            .str.replace(r'\D', '', regex=True)  # luego elimina lo no numérico
        )
        data['DV'] = data['DV'].astype(str).str.replace(r'[^0-9Kk]', '', regex=True).str.upper()
        data['DV'] = data['DV'].replace({'': 'null', 'nan': 'null'})

        # Formateo de fechas
        date_columns = ['FECHA ATENCION', 'FECHA DE NACIMIENTO']
        for col in date_columns:
            data[col] = pd.to_datetime(data[col], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

        # Generar LlaveGES2
        def generar_llave(row):
            try:
                primer_nombre = row['NOMBRES'].split()[0]
                cie10 = str(row['CIE 10'])[:3]
                fecha = datetime.strptime(row['FECHA ATENCION'], '%Y-%m-%d').strftime('%d-%m-%Y')
                return f"{primer_nombre}_{cie10}_{fecha}_{row['RUN']}-{row['DV']}"
            except:
                return 'null'

        data['LlaveGES2'] = data.apply(generar_llave, axis=1)

        # Manejo de valores nulos
        text_columns = [col for col in data.columns if data[col].dtype == 'object']
        for col in text_columns:
            data[col] = data[col].replace(r'^\s*$', 'null', regex=True).fillna('null')
            data[col] = data[col].astype(str)

        # Orden de columnas requerido
        column_order = [
            'ESTABLECIMIENTO ATENCION', 'RUN', 'DV', 'FICHA', 'NUMERO DE FICHA',
            'ESTABLECIMIENTO INSCRIPCION', 'NOMBRES', 'PRIMER APELLIDO',
            'SEGUNDO APELLIDO', 'FECHA ATENCION', 'FECHA DE NACIMIENTO', 'SEXO',
            'EDAD', 'DIRECCION', 'TELEFONO 1', 'TELEFONO 2', 'CELULAR', 'SECTOR',
            'PREVISION', 'CLASIFICACIÓN BENEFICIARIO FONASA', 'NOMBRE FUNCIONARIO',
            'PRIMER APELLIDO FUNCIONARIO', 'SEGUNO APELLIDO FUNCIONARIO',
            'PROFESIONAL O TECNICO', 'PROBLEMA DE SALUD', 'CIE 10',
            'ESTADO DIAGNOSTICO', 'DIAGNOSTICO', 'INCIDENCIA', 'LlaveGES2'
        ]

        data = data[column_order]

        # Después de procesar los datos, antes de exportar a CSV:

        # A. Validar valores problemáticos en DV
        dv_invalidos = data[
            (data['DV'] != 'null') &
            (~data['DV'].str.match(r'^[0-9Kk]?$', na=True))
            ]

        #if not dv_invalidos.empty:
        #    print(f"\n⚠️ Valores inválidos en DV (Total: {len(dv_invalidos)}):")
        #    print(dv_invalidos[['RUN', 'DV']].head(10))  # Muestra los primeros 10

        # B. Limpieza adicional para DV
        data['DV'] = (
            data['DV']
            .str.upper()  # Convertir 'k' a 'K'
            .str.strip()  # Eliminar espacios
            .replace({
                'nan': 'null',
                '': 'null',
                ' ': 'null',
                '[^0-9K]': 'null'  # Eliminar caracteres no válidos
            }, regex=True)
            .str[:1]  # Tomar solo el primer carácter
        )

        # Exportar a CSV
        data.to_csv(
            temp_csv_path,
            index=False,
            sep='~',
            quoting=csv.QUOTE_ALL,
            encoding='utf-8',
            escapechar='\\'
        )

        # BULK INSERT
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=localhost\\SQLEXPRESS01;"
            "Database=el_bosque;"
            "Trusted_Connection=yes;"
        )

        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            bulk_insert_sql = f"""
            BULK INSERT el_bosque.dbo.ges
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
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


# Procesamiento principal
if __name__ == "__main__":
    # Listar archivos válidos
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Pacientes_GES_de_Urgencia") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_ges()

    # Ordenar por tamaño
    files_info.sort(key=lambda x: x[1])
    print(f"Archivos a procesar: {len(files_info)}")

    # Procesar en lotes
    current_lote = []
    current_size = 0
    lote_index = 1

    for file_info in files_info:
        file_name, file_size = file_info

        if current_size + file_size > SIZE_LIMIT and current_lote:
            procesar_lote_ges(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_ges(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")