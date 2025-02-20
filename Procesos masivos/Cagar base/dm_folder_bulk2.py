import os
import pandas as pd
import pyodbc
import csv
import numpy as np
from datetime import datetime

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\pacientes_hemoglucotest_temp.csv"
error_log_path = r"G:\Mi unidad\UrgenciaQ\errores_hemoglucotest.log"


def crear_tabla_dm():
    """Crea la tabla pacientes_hemoglucotest si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    create_table_sql = """
    CREATE TABLE el_bosque.dbo.dm (
        [Nombre] NVARCHAR(255),
        [PrimerApellido] NVARCHAR(255),
        [SegundoApellido] NVARCHAR(255),
        [RUN] NVARCHAR(20),
        [DV] NVARCHAR(20),
        [Establecimiento] NVARCHAR(255),
        [Sector] NVARCHAR(50),
        [FechaRegistro] NVARCHAR(255),
        [HoraRegistro] NVARCHAR(255),
        [ValorHemoglucotest] NVARCHAR(50)
    )
    """
    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dm'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'pacientes_hemoglucotest' creada exitosamente.")
            else:
                print("Tabla 'pacientes_hemoglucotest' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def validar_rut(rut):
    """Valida y formatea correctamente un RUT"""
    if pd.isna(rut) or rut in ['', 'nan', '-']:
        return None

    # Convertir a string y limpiar
    rut_str = str(rut).strip().replace('.', '').replace('-', '')

    # Separar número y dígito verificador
    if '-' in str(rut):
        numero, dv = str(rut).split('-')
    elif len(rut_str) > 1:
        numero = rut_str[:-1]
        dv = rut_str[-1]
    else:
        return None

    # Validar que el número sea numérico
    if not numero.isdigit():
        return None

    # Formatear como XX.XXX.XXX-X
    try:
        numero = int(numero)
        rut_formateado = f"{numero:,}-{dv}".replace(',', '.')
        return rut_formateado
    except:
        return None


def procesar_dm(files_lote, lote_index, temp_csv_path):
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

        # Convierte a string, elimina espacios y descarta cadenas vacías o NaN
        data['RUN'] = data['RUN'].astype(str)
        data = data[data['RUN'].str.strip() != '']
        data.reset_index(drop=True, inplace=True)

        print(data)

        # Limpiar nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # Procesar valor hemoglucotest
        if 'VALOR HEMOGLUCOTEST' in data.columns:
            data['VALOR HEMOGLUCOTEST'] = data['VALOR HEMOGLUCOTEST'].astype(str).str.strip()
            replacements = {'Hi': '600', 'hi': '600', 'HI': '600', 'H1': '600'}
            data['VALOR HEMOGLUCOTEST'] = data['VALOR HEMOGLUCOTEST'].replace(replacements)
            data['VALOR HEMOGLUCOTEST'] = pd.to_numeric(data['VALOR HEMOGLUCOTEST'], errors='coerce')
            data['VALOR HEMOGLUCOTEST'] = data['VALOR HEMOGLUCOTEST'].fillna(0).astype(int)
        else:
            print("Advertencia: No se encontró columna VALOR HEMOGLUCOTEST")
            data['VALOR HEMOGLUCOTEST'] = 0

        # renombra tus columnas al mismo nombre que en la tabla
        final = data.rename(columns={
            'NOMBRE PACIENTE': 'Nombre',
            'PRIMER APELLIDO': 'PrimerApellido',
            'SEGUNDO APELLIDO': 'SegundoApellido',
            'ESTABLECIMIENTO DE INSCRIPCION': 'Establecimiento',
            'SECTOR': 'Sector',
            'FECHA REGISTRO HEMOGLUCOTEST': 'FechaRegistro',
            'HORA REGISTRO HEMOGLUCOTEST': 'HoraRegistro',
            'VALOR HEMOGLUCOTEST': 'ValorHemoglucotest',
        })

        # añade fecha y hora
        final['FechaRegistro'] = final['FechaRegistro'].astype(str)
        final['HoraRegistro'] = final['HoraRegistro'].astype(str)

        # ordena exactamente como tu tabla
        final = final[[
            'Nombre', 'PrimerApellido', 'SegundoApellido',
            'RUN', 'DV',
            'Establecimiento', 'Sector',
            'FechaRegistro', 'HoraRegistro',
            'ValorHemoglucotest'
        ]]

        # Validar datos antes de exportar
        final_data = final.replace({np.nan: None})

        print(final_data['RUN'])

        # Exportar a CSV temporal con codificación UTF-8-BOM para SQL Server
        final_data.to_csv(
            temp_csv_path,
            index=False,
            sep='|',
            encoding='utf-8-sig',  # ojo con el BOM; SQL Server + CODEPAGE='65001' sí lo soporta
            quoting=csv.QUOTE_MINIMAL,
            escapechar='\\'
        )

        # BULK INSERT a SQL Server con manejo de errores
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=localhost\\SQLEXPRESS01;"
            "Database=el_bosque;"
            "Trusted_Connection=yes;"
        )
        try:
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()

                # Configuración para permitir más errores y continuar
                cursor.execute("SET ANSI_WARNINGS OFF")
                cursor.execute("SET ANSI_NULLS OFF")

                bulk_insert_sql = f"""
                BULK INSERT el_bosque.dbo.dm
                FROM '{temp_csv_path}'
                WITH (
                    -- quita FORMAT='CSV' si tu versión < 2022
                    DATAFILETYPE = 'char',          -- texto plano
                    FIELDTERMINATOR = '|',          -- mismo delimitador que usaste al exportar
                    ROWTERMINATOR = '0x0A',         -- salto de línea LF; usa 0x0D0A si es CRLF
                    FIRSTROW = 2,                   -- salta la fila de cabecera
                    CODEPAGE = '65001',
                    TABLOCK
                );
                """
                cursor.execute(bulk_insert_sql)
                conn.commit()

                # Verificar resultados
                cursor.execute("SELECT COUNT(*) FROM el_bosque.dbo.dm")
                total_registros = cursor.fetchone()[0]
                print(f"Registros en tabla después de inserción: {total_registros}")

        except pyodbc.Error as e:
            print(f"Error durante BULK INSERT: {str(e)}")
            # Obtener detalles de los errores
            if 'errors' in str(e):
                with open(error_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== Errores de inserción en lote {lote_index} ===\n")
                    f.write(str(e) + "\n")
            raise

        print(f"¡Lote {lote_index} insertado! ({final_data.shape[0]} registros procesados)")

    except Exception as e:
        print(f"Error procesando lote {lote_index}: {str(e)}")
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Error en lote {lote_index} ===\n")
            f.write(str(e) + "\n")
    finally:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


if __name__ == "__main__":
    # Inicializar archivo de log
    with open(error_log_path, 'w', encoding='utf-8') as f:
        f.write("=== Log de errores de procesamiento ===\n")

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
            procesar_dm(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_dm(current_lote, lote_index, temp_csv_path)



    print("\nProceso completado exitosamente!")
    print(f"Errores registrados en: {error_log_path}")