import os
import pandas as pd
import pyodbc
import csv
import numpy as np
import re

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\hemoglucotest_temp.csv"


def crear_tabla_dm():
    """Crea la tabla dm si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    create_table_sql = """
    CREATE TABLE el_bosque.dbo.dm (
        [Llave_GES] NVARCHAR(255),
        [AlertaDM] NVARCHAR(20),
        [HGT] INT,
        [RUT] NVARCHAR(20)
    )
    """
    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dm'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'dm' creada exitosamente.")
            else:
                print("Tabla 'dm' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_dm(files_lote, lote_index, temp_csv_path):
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")
    df_list = []
    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo: {file_name}")

        try:
            # Se asume que la fila de encabezado se encuentra en la posición 8 (como en el ejemplo anterior)
            df = pd.read_excel(full_path, header=8)
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

        # Transformar la fecha: convertir la columna a datetime y re-formatear a dd-mm-yyyy
        data['Combinada'] = pd.to_datetime(
            data['FECHA REGISTRO HEMOGLUCOTEST'],
            format='%m/%d/%Y %I:%M:%S %p',
            errors='coerce'
        ).dt.strftime('%d-%m-%Y')

        # Crear columna RUT (convertir RUN a cadena en caso de que sea numérico)
        # data['RUT'] = data['RUN'].astype(int).astype(str).str.strip() + '-' + data['DV'].astype(str).str.strip()

        if 'DV' in data.columns:
            # Convertir RUT a entero (siempre que no sea nulo) y luego a cadena
            data['RUN'] = data['RUN'].apply(lambda x: str(int(x)) if pd.notnull(x) else '')
            # Finalmente, concatenar RUT y DV
            data['RUT'] = data['RUN'].str.strip() + '-' + data['DV'].astype(str).str.strip()

        # 3. Filtrar filas donde RUT sea nulo o vacío
        #    (por ejemplo, si RUT quedó "nan-")
        data = data[data['RUT'].notna()]
        data = data[~data['RUT'].str.contains('nan', na=False)]
        data = data[data['RUT'] != '-']

        # Crear Llave_GES combinando la fecha y el RUT
        data['Llave_GES'] = data['Combinada'] + '-' + data['RUT']

        # Reemplazar valores en VALOR HEMOGLUCOTEST (cambios en mayúsculas/minúsculas) y convertir a numérico
        data['VALOR HEMOGLUCOTEST'] = data['VALOR HEMOGLUCOTEST'] \
            .replace({'Hi': '600', 'hi': '600', 'HI': '600'})
        data['VALOR HEMOGLUCOTEST'] = pd.to_numeric(data['VALOR HEMOGLUCOTEST'], errors='coerce') \
            .fillna(0).astype(int)

        # Agrupar por Llave_GES y obtener:
        # - El primer RUT (asumiendo que es único para cada llave)
        # - El valor máximo de VALOR HEMOGLUCOTEST (renombrado a HGT)
        grouped = data.groupby('Llave_GES').agg({
            'RUT': 'first',
            'VALOR HEMOGLUCOTEST': 'max'
        }).reset_index().rename(columns={'VALOR HEMOGLUCOTEST': 'HGT'})

        # Generar columna AlertaDM: si HGT >= 200 se asigna "Alerta 200+", de lo contrario None
        grouped['AlertaDM'] = np.where(grouped['HGT'] >= 200, 'Alerta 200+', None)

        # Ordenar columnas finales
        grouped = grouped[['Llave_GES', 'AlertaDM', 'HGT', 'RUT']]

        # Exportar a un CSV temporal (con separador '~')
        grouped.to_csv(
            temp_csv_path,
            index=False,
            sep='~',
            quoting=csv.QUOTE_ALL,
            encoding='utf-8',
            escapechar='\\'
        )

        # BULK INSERT a SQL Server
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=localhost\\SQLEXPRESS01;"
            "Database=el_bosque;"
            "Trusted_Connection=yes;"
        )
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            bulk_insert_sql = f"""
            BULK INSERT el_bosque.dbo.dm
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

        print(f"¡Lote {lote_index} insertado! ({grouped.shape[0]} registros)")

    except Exception as e:
        print(f"Error procesando lote {lote_index}: {str(e)}")
    finally:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


if __name__ == "__main__":
    # Listar archivos válidos
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Informe_Pacientes_Con_Hemoglucotest") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_dm()

    # Ordenar archivos por tamaño
    files_info.sort(key=lambda x: x[1])
    print(f"Archivos a procesar: {len(files_info)}")

    # Procesar en lotes
    current_lote = []
    current_size = 0
    lote_index = 1

    for file_info in files_info:
        file_name, file_size = file_info
        if current_size + file_size > SIZE_LIMIT and current_lote:
            procesar_lote_dm(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_dm(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")
