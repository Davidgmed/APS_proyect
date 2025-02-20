import os
import pandas as pd
import pyodbc
import numpy as np
import re
import tempfile

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"


def crear_tabla_dm():
    """Crea la tabla dm si no existe y agrega columnas faltantes"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dm')
    BEGIN
        CREATE TABLE el_bosque.dbo.dm (
            [NOMBRE PACIENTE] NVARCHAR(255),
            [PRIMER APELLIDO] NVARCHAR(255),
            [SEGUNDO APELLIDO] NVARCHAR(255),
            [RUN] NVARCHAR(255),
            [DV] NVARCHAR(255),
            [RUT] NVARCHAR(255),
            [AlertaDM] NVARCHAR(255),
            [HGT] NVARCHAR(255),
            [ESTABLECIMIENTO DE INSCRIPCION] NVARCHAR(255),
            [SECTOR] NVARCHAR(255),
            [LLAVE_GES] NVARCHAR(255),
            [FECHA REGISTRO HEMOGLUCOTEST] NVARCHAR(255),
            [HORA REGISTRO HEMOGLUCOTEST] NVARCHAR(255),
            [VALOR HEMOGLUCOTEST] NVARCHAR(255)
        )
    END
    """
    required_columns = [
        ('ESTABLECIMIENTO DE INSCRIPCION', 'NVARCHAR(255)'),
        ('SECTOR', 'NVARCHAR(255)'),
        ('FECHA REGISTRO HEMOGLUCOTEST', 'NVARCHAR(255)'),
        ('Llave_GES', 'NVARCHAR(255)'),
        ('AlertaDM', 'NVARCHAR(255)'),
        ('HGT', 'NVARCHAR(255)'),
        ('RUT', 'NVARCHAR(255)')
    ]


    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dm'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'dm' creada exitosamente.")
            else:
                print("Tabla 'dm' ya existe.")
                # Verificar y agregar columnas faltantes
                for col_name, col_type in required_columns:
                    cursor.execute(
                        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'dm' AND COLUMN_NAME = ?",
                        col_name
                    )
                    if cursor.fetchone()[0] == 0:
                        alter_sql = f"ALTER TABLE dm ADD [{col_name}] {col_type}"
                        cursor.execute(alter_sql)
                        print(f"Columna '{col_name}' agregada.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_dm(files_lote, lote_index):
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")
    df_list = []
    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo: {file_name}")

        try:
            df = pd.read_excel(full_path, header=8)
            print(f"  Registros en {file_name}: {len(df)}")
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

        # Limpieza de nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # Renombrar columnas críticas si es necesario
        required_cols = ['FECHA REGISTRO HEMOGLUCOTEST', 'RUN', 'DV', 'VALOR HEMOGLUCOTEST']
        for col in required_cols:
            if col not in data.columns:
                candidates = [c for c in data.columns if col.split()[-1] in c]
                if candidates:
                    data.rename(columns={candidates[0]: col}, inplace=True)

        # Procesar RUT
        #data['RUN'] = data['RUN'].apply(
        #    lambda x: str(int(x)) if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else ''
        #)
        data['RUT'] = data['RUN'].astype(str).str.strip() + '-' + data['DV'].astype(str).str.strip()

        # Filtrar RUTs inválidos
        data = data[data['RUT'].notna() & (data['RUT'] != '') & (data['RUT'] != '-')]

        # Procesar valores HGT
        data['HGT'] = data['VALOR HEMOGLUCOTEST'].replace({'Hi': '600', 'hi': '600', 'HI': '600'})
        data['HGT'] = pd.to_numeric(data['HGT'], errors='coerce').fillna(0).astype(int)

        # Agrupar por RUT
        grouped = data.groupby('RUT').agg({
            'FECHA REGISTRO HEMOGLUCOTEST': 'first',
            'HGT': 'max'
        }).reset_index()

        # Limitar valores al rango de INT de SQL Server
        int_max = 2147483647
        int_min = -2147483648

        grouped['HGT'] = grouped['HGT'].clip(int_min, int_max).astype(np.int32)

        # Generar alertas y Llave_GES
        grouped['AlertaDM'] = np.where(grouped['HGT'] >= 200, 'Alerta 200+', None)

        # Generar alertas y Llave_GES
        grouped['AlertaDM'] = np.where(grouped['HGT'] >= 200, 'Alerta 200+', None)
        grouped['Llave_GES'] = (
                pd.to_datetime(grouped['FECHA REGISTRO HEMOGLUCOTEST'], errors='coerce')
                .dt.strftime('%d-%m-%Y') + '-' + grouped['RUT']
        )
        grouped = grouped[['Llave_GES', 'AlertaDM', 'HGT', 'RUT']]
        print(grouped)


        # Insertar en SQL
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=localhost\\SQLEXPRESS01;"
            "Database=el_bosque;"
            "Trusted_Connection=yes;"
        )
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(
                "INSERT INTO dm (Llave_GES, AlertaDM, HGT, RUT) VALUES (?, CAST(? AS VARCHAR(255)), CAST(? AS VARCHAR(255)), ?)",
                [tuple(x) for x in grouped.values]
            )
            conn.commit()

        print(f"¡Lote {lote_index} insertado! ({len(grouped)} registros)")

    except Exception as e:
        print(f"Error procesando lote {lote_index}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Informe_Pacientes_Con_Hemoglucotest") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    crear_tabla_dm()
    files_info.sort(key=lambda x: x[1])
    print(f"Archivos a procesar: {len(files_info)}")

    current_lote = []
    current_size = 0
    lote_index = 1

    for file_info in files_info:
        file_name, file_size = file_info
        if current_size + file_size > SIZE_LIMIT and current_lote:
            procesar_lote_dm(current_lote, lote_index)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_dm(current_lote, lote_index)

    print("\nProceso completado exitosamente!")