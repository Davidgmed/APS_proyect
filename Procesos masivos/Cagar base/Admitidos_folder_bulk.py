import os
import pandas as pd
import pyodbc
import csv

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\admitidos_temp.csv"


def crear_tabla_si_no_existe():
    """Crea la tabla si no existe en la base de datos"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )
    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()

            # Verificar existencia de la tabla
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'admitidos' 
                AND TABLE_SCHEMA = 'dbo'
            """)

            if cursor.fetchone()[0] == 0:
                # Crear tabla
                cursor.execute("""
                CREATE TABLE el_bosque.dbo.admitidos (
                    [SS] VARCHAR(100),
                    [ESTABLECIMIENTO] VARCHAR(255),
                    [CORRELATIVO] VARCHAR(20),
                    [FECHA DE LLEGADA] VARCHAR(50),
                    [HORA DE LLEGADA] VARCHAR(50),
                    [CATEGORIZACION] VARCHAR(10),
                    [NOMBRE PACIENTE] VARCHAR(255),
                    [SEXO] VARCHAR(20),
                    [EDAD AÑOS] VARCHAR(10),
                    [EDAD MESES] VARCHAR(10),
                    [EDAD DIAS] VARCHAR(10),
                    [NACIONALIDAD] VARCHAR(50),
                    [DIRECCION] VARCHAR(255),
                    [CIE 10] VARCHAR(20),
                    [DIAGNOSTICO PRINCIPAL] VARCHAR(MAX),
                    [ESTADO] VARCHAR(50),
                    [PREVISION] VARCHAR(50),
                    [RUT] VARCHAR(20),
                    [FUNCIONARIO REGISTRA INGRESO] VARCHAR(255),
                    [Técnico Paramédico] VARCHAR(255),
                    [Médico] VARCHAR(255),
                    [Enfermero(a)] VARCHAR(255),
                    [FECHA TERMINO] VARCHAR(50),
                    [HORA TERMINO] VARCHAR(50)
                )
                """)
                print("Tabla 'admitidos' creada exitosamente.")
            else:
                print("Tabla 'admitidos' ya existe.")

    except Exception as e:
        print(f"Error al verificar/crear tabla: {str(e)}")
        raise


def procesar_lote(files_lote, lote_index, temp_csv_path):
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
        print(f"Lote {lote_index} - Concatenando y transformando...")
        data = pd.concat(df_list, ignore_index=True)

        # Limpiar columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        data.drop(columns=['LLEGA EN'], inplace=True, errors='ignore')

        # Función mejorada para formateo de fechas
        def formatear_fechas(fecha, hora):
            try:
                # Parsear fecha con formato específico
                fecha_dt = pd.to_datetime(fecha, format='%d-%m-%Y', dayfirst=True, errors='coerce')
                fecha_formateada = fecha_dt.dt.strftime('%d-%m-%Y') + ' 0:00'

                # Parsear hora con formato específico
                hora_dt = pd.to_datetime(hora, format='%H:%M:%S', errors='coerce')
                hora_formateada = hora_dt.dt.strftime('1899/12/31 %H:%M:%S.000')

                return fecha_formateada, hora_formateada
            except Exception as e:
                print(f"Error formateando fechas: {str(e)}")
                return fecha, hora

        # Aplicar transformaciones
        data['FECHA DE LLEGADA'], data['HORA DE LLEGADA'] = formatear_fechas(
            data['FECHA DE LLEGADA'], data['HORA DE LLEGADA']
        )
        data['FECHA TERMINO'], data['HORA TERMINO'] = formatear_fechas(
            data['FECHA TERMINO'], data['HORA TERMINO']
        )

        # Manejo de valores nulos
        columnas_na = ['CIE 10', 'DIAGNOSTICO PRINCIPAL', 'Técnico Paramédico', 'Médico', 'Enfermero(a)']
        for col in columnas_na:
            data[col] = data[col].replace(r'^\s*$', 'null', regex=True).fillna('null')

        # Orden de columnas
        columnas_orden = [
            'SS', 'ESTABLECIMIENTO', 'CORRELATIVO', 'FECHA DE LLEGADA', 'HORA DE LLEGADA',
            'CATEGORIZACION', 'NOMBRE PACIENTE', 'SEXO', 'EDAD AÑOS', 'EDAD MESES', 'EDAD DIAS',
            'NACIONALIDAD', 'DIRECCION', 'CIE 10', 'DIAGNOSTICO PRINCIPAL', 'ESTADO', 'PREVISION',
            'RUT', 'FUNCIONARIO REGISTRA INGRESO', 'Técnico Paramédico', 'Médico', 'Enfermero(a)',
            'FECHA TERMINO', 'HORA TERMINO'
        ]

        for col in columnas_orden:
            if col not in data.columns:
                data[col] = None

        data = data[columnas_orden]

        # Exportar CSV
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
            BULK INSERT el_bosque.dbo.admitidos
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

        print(f"¡Lote {lote_index} insertado correctamente! ({data.shape[0]} registros)")

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
        if f.startswith("Informe_Urgencia_Web_Pacientes_Admitidos") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_si_no_existe()

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
            procesar_lote(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")