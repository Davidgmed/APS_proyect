import os
import pandas as pd
import pyodbc
import csv
import numpy as np
import math
import re

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\diagnosticos_temp.csv"


def crear_tabla_diagnosticos():
    """Crea la tabla diagnosticos si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )

    create_table_sql = """
    CREATE TABLE el_bosque.dbo.hta (
        [LlaveGES2] NVARCHAR(255),
        [PAS] INT,
        [PAD] INT,
        [Alerta] NVARCHAR(20),
        [Centro] NVARCHAR(255),
        [Sector] NVARCHAR(50),
        [RUT] NVARCHAR(20)
    )
    """

    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'hta'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'hta' creada exitosamente.")
            else:
                print("Tabla 'hta' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_hta(files_lote, lote_index, temp_csv_path):
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

        # Limpiar nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # 1. Convertir DV a string para su limpieza
        data['DV'] = data['DV'].astype(str)

        # 2. Identificar valores inválidos en DV:
        #    - Filtrar donde DV no sea 'null' y no coincida con la expresión regular de 0-9 o K (1 caracter)
        dv_invalidos = data[
            (data['DV'].str.lower() != 'null') &
            (~data['DV'].str.match(r'^[0-9Kk]?$', na=True))
            ]

        if not dv_invalidos.empty:
            print(f"\n⚠️ Valores inválidos en DV (Total: {len(dv_invalidos)}):")
            print(dv_invalidos[['RUN', 'DV']].head(10))

        # 3. Limpiar DV:
        #    - Pasar a mayúscula
        #    - Eliminar espacios extra
        #    - Reemplazar posibles 'nan', cadenas vacías u otros, por 'null'
        data['DV'] = (
            data['DV']
            .str.upper()
            .str.strip()
            .replace({'nan': 'null', '^$': 'null'}, regex=True)
            # .str[:1]  # Si quisieras forzar a tomar SOLO el primer caracter
        )

        # 4. Función para generar un RUT válido o 'null'
        def generar_rut(run_value, dv_value):
            """
            Convierte run_value a entero (si es posible) y valida dv_value:
              - dv_value debe ser un dígito [0-9] o 'K' (un solo carácter).
              - Si alguna validación falla, retorna 'null'.
              - De lo contrario, retorna run-dv.
            """
            # Validar que 'run_value' sea convertible a entero
            try:
                run_int = int(float(run_value))  # usar float() -> int() para casos como '9608575.0'
            except (ValueError, TypeError):
                # No se pudo convertir a entero -> es 'null'
                return 'null'

            # Limpiar DV por si acaso
            dv_clean = str(dv_value).strip().upper()

            # Validar DV con regex: un solo caracter, dígito [0-9] o 'K'
            # o si es 'null', se descarta
            if dv_clean == 'null' or not re.match(r'^[0-9K]$', dv_clean):
                return 'null'

            # Retornar la concatenación
            return f"{run_int}-{dv_clean}"

        # 5. Aplicar la función a cada fila para construir la columna 'RUT'
        data['RUT'] = data.apply(
            lambda row: generar_rut(row['RUN'], row['DV']),
            axis=1
        )

        # (Opcional) Si quieres ver cuántos RUT quedaron en 'null'
        ruts_invalidos = data[data['RUT'] == 'null']
        if not ruts_invalidos.empty:
            print(f"\n⚠️ Hay {len(ruts_invalidos)} filas con RUT='null'")


        # Generar LlaveGES2
        def generar_llave(row):
            try:
                # 1. Tomar el primer nombre
                primer_nombre = str(row['NOMBRE']).split()[0]

                # 2. Obtener los primeros 3 caracteres de CIE10
                cie10 = str(row['CIE10'])[:3]

                # 3. Convertir la fecha al formato dd-mm-yyyy
                fecha = pd.to_datetime(row['FECHA ATENCION'], dayfirst=True).strftime('%d-%m-%Y')

                # 4. Tomar RUN y DV
                run = row['RUN']
                dv = str(row['DV']).strip()

                # 5. Limpiar el valor de RUN:
                #    - Si es float (ej. 9608575.0), lo pasamos a int (9608575).
                #    - Si es NaN o algo no convertible, lo dejamos vacío.
                if pd.isna(run):
                    run_str = ''
                else:
                    if isinstance(run, float):
                        run_str = str(int(run))  # Conviertes 9608575.0 a '9608575'
                    else:
                        run_str = str(run)

                # 6. Evaluar DV:
                #    - Si dv es 'nan', 'N' o está vacío, no lo incluimos.
                #    - De lo contrario, concatenamos run_str + '-' + dv
                if dv.lower() == 'nan' or dv.upper() == 'N':
                    # DV inválido, no lo usamos.
                    final_run = run_str
                else:
                    # DV válido
                    if run_str:
                        final_run = f"{run_str}-{dv}"
                    else:
                        final_run = ''

                # 7. Si existe final_run (es decir, tenemos un RUN válido), lo incluimos,
                #    si no, omitimos la parte de RUN/DV.
                if final_run:
                    return f"{primer_nombre}_{cie10}_{fecha}_{final_run}"
                else:
                    return f"{primer_nombre}_{cie10}_{fecha}"

            except Exception:
                return 'null'

        data['LlaveGES2'] = data.apply(generar_llave, axis=1)

        # Dividir PRESION ARTERIAL
        presion_split = data['PRESION ARTERIAL'].str.split('/', n=1, expand=True)
        data['PAS'] = pd.to_numeric(presion_split[0], errors='coerce').fillna(0).astype(int)
        data['PAD'] = pd.to_numeric(presion_split[1], errors='coerce').fillna(0).astype(int)

        # Generar RUT
        # data['RUT'] = data['RUN'].astype(str) + '-' + data['DV']

        # Agrupar y agregar datos
        grouped = data.groupby('LlaveGES2').agg({
            'PAS': 'max',
            'PAD': 'max',
            'ESTABLECIMIENTO': 'first',
            'SECTOR PACIENTE': 'first',
            'RUT': 'first'
        }).reset_index()

        # Renombrar columnas
        grouped = grouped.rename(columns={
            'ESTABLECIMIENTO': 'Centro',
            'SECTOR PACIENTE': 'Sector'
        })

        # Generar alertas
        condiciones = [
            (grouped['PAS'] >= 180) | (grouped['PAD'] >= 110),
            (grouped['PAS'] >= 160) | (grouped['PAD'] >= 100)
        ]
        opciones = ['180/110', '160/100']
        grouped['Alerta'] = np.select(condiciones, opciones, default=None)

        # Filtrar solo registros con alerta
        grouped = grouped[grouped['Alerta'].notnull()]

        # Orden de columnas requerido
        column_order = ['LlaveGES2', 'PAS', 'PAD', 'Alerta', 'Centro', 'Sector', 'RUT']
        grouped = grouped[column_order]

        # Exportar a CSV
        grouped.to_csv(
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
            BULK INSERT el_bosque.dbo.hta
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


# Procesamiento principal
if __name__ == "__main__":
    # Listar archivos válidos
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Informe_de_Atenciones_por_Diagnostico_Urgencia_Web") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_diagnosticos()

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
            procesar_lote_hta(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_hta(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")