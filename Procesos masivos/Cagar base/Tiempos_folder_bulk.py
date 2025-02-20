import os
import pandas as pd
import pyodbc
import csv

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\tiempos_temp.csv"


def crear_tabla_tiempos():
    """Crea la tabla tiempos si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )

    create_table_sql = """
    CREATE TABLE el_bosque.dbo.tiempos (
        [ID] FLOAT,
        [SERVICIO DE SALUD] NVARCHAR(100),
        [ESTABLECIMIENTO] NVARCHAR(200),
        [RUN] NVARCHAR(20) NULL,  -- Permitir NULL
        [DV] NVARCHAR(2) NULL,     -- Permitir NULL
        [RUN RESPONSABLE] NVARCHAR(20),
        [EDAD AÑOS] INT,
        [EDAD MESES] INT,
        [EDAD DIAS] INT,
        [SEXO] NVARCHAR(20),
        [OTRA IDENTIFICACION] NVARCHAR(100),
        [NOMBRE PACIENTE] NVARCHAR(255),
        [PREVISION] NVARCHAR(100),
        [CALLE] NVARCHAR(255),
        [NUMERO] NVARCHAR(20),
        [DPTO] NVARCHAR(20),
        [REGION] NVARCHAR(100),
        [COMUNA] NVARCHAR(100),
        [COMUNA RESIDENCIA] NVARCHAR(100),
        [REGIÓN RESIDENCIA] NVARCHAR(100),
        [NACIONALIDAD] NVARCHAR(100),
        [TIPO USUARIO] NVARCHAR(50),
        [ESTABLECIMIENTO DE INSCRIPCIÓN] NVARCHAR(255),
        [CORRELATIVO] NVARCHAR(20),
        [FECHA ADMISION] NVARCHAR(50),
        [HORA ADMISION] NVARCHAR(50),
        [FECHA 1° CATEGORIZACION] NVARCHAR(50),
        [HORA 1° CATEGORIZACION] NVARCHAR(50),
        [FECHA ULTIMA CATEGORIZACION] NVARCHAR(50),
        [HORA ULTIMA CATEGORIZACION] NVARCHAR(50),
        [FECHA ANAMNESIS] NVARCHAR(50),
        [HORA ANAMNESIS] NVARCHAR(50),
        [FECHA INDICACIONES] NVARCHAR(50),
        [HORA INDICACIONES] NVARCHAR(50),
        [FECHA INDICACION REALIZADA] NVARCHAR(50),
        [HORA INDICACION REALIZADA] NVARCHAR(50),
        [FECHA EVOLUCION] NVARCHAR(50),
        [HORA EVOLCION] NVARCHAR(50),
        [FECHA ALTA] NVARCHAR(50),
        [HORA ALTA] NVARCHAR(50),
        [NOMBRE FUNCIONARIO REALIZO ADMISION] NVARCHAR(255),
        [INSTRUMENTO QUE REALIZA ADMISION] NVARCHAR(100),
        [PRIMERA CATEGORIZACION] NVARCHAR(20),
        [NOMBRE PROFESIONAL QUE REGISTRA PRIMERA CATEGORIZACION] NVARCHAR(255),
        [INSTRUMENTO PROFESIONAL QUE REGISTRA PRIEMRA CATEGORIZACION] NVARCHAR(100),
        [ULTIMA CATEGORIZACION] NVARCHAR(20),
        [NOMBRE PROFESIONAL QUE REGISTRA ULTIMA CATEGORIZACION] NVARCHAR(255),
        [INSTRUMETO PROFESIONAL QUE REGISTRA ULTIMA CATEGORIZACION] NVARCHAR(100),
        [CODIGO DIAGNOSTICO] NVARCHAR(20),
        [DIAGNOSTICO PRINCIPAL] NVARCHAR(MAX),
        [NOMBRE PROFESIONAL REGISTRA ANAMNESIS] NVARCHAR(255),
        [INSTRUMETO PROFESIONAL REGISTRA ANAMNESIS] NVARCHAR(100),
        [NOMBRE PROFESIONAL REGISTRA EVOLUCIÓN] NVARCHAR(255),
        [INSTRUMENTO PROFESIONAL REGISTRA EVOLUCIÓN] NVARCHAR(100),
        [PROCEDIMIENTO SOLICITADO] NVARCHAR(255),
        [FUNCIONARIO REGISTRA EL PROCEDIMIENTO] NVARCHAR(255),
        [ESTAMENTO FUNCIONARIO REGISTRA PROCEDIMIENTO] NVARCHAR(100),
        [FUNCIONARIO APLICA PROCEDIMIENTO] NVARCHAR(255),
        [ESTAMENTO FUNCIONARIO APLICA PROCEDIMIENTO] NVARCHAR(100),
        [INDICACIONES] NVARCHAR(MAX),
        [NOMBRE FUNCIONARIO QUE REGISTRA INDICACIONES] NVARCHAR(255),
        [INSTRUMENTO FUNCIONARIO QUE REGISTRA INDICACIONES] NVARCHAR(100),
        [DESTINO ALTA] NVARCHAR(100),
        [FUNCIONARIO REGISTRA ALTA] NVARCHAR(255),
        [INSTRUMENTO PROFESIONAL ALTA] NVARCHAR(100),
        [fecha SIGNOS VITALES] NVARCHAR(50),
        [HORA SIGNOS VITALES] NVARCHAR(50),
        [FUNCIONARIO REGISTRA SIGNOS VITALES] NVARCHAR(255),
        [INSTRUMENTO PROFESIONAL QUE REGISTRA SIGNOS VITALES] NVARCHAR(100),
        [ESTADO] NVARCHAR(50),
        [MOTIVO EGRESO ADMINISTRATIVO] NVARCHAR(255),
        [OBSERVACION MOTIVO EGRESO] NVARCHAR(MAX)
    )
    """

    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'tiempos'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'tiempos' creada exitosamente.")
            else:
                print("Tabla 'tiempos' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_tiempos(files_lote, lote_index, temp_csv_path):
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

        # --- Nuevo: Manejo especial para RUN y DV ---
        # Convertir a string y manejar valores vacíos/NaN
        data['RUN'] = data['RUN'].astype(str).replace(['nan', 'NaT', 'None', ''], 'null')
        data['DV'] = data['DV'].astype(str).replace(['nan', 'NaT', 'None', ''], 'null')

        # Limpiar formato de RUN (ej: 2.042,00 -> 2042)
        data['RUN'] = data['RUN'].str.replace(r'[^\d]', '', regex=True)
        data['RUN'] = data['RUN'].apply(lambda x: x if x != '' else 'null')

        # Manejar columnas numéricas de edad
        numeric_cols = ['EDAD AÑOS', 'EDAD MESES', 'EDAD DIAS']
        for col in numeric_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)

        # Función para formatear fechas y horas
        def formatear_fecha_hora(fecha, hora):
            try:
                fecha_str = pd.to_datetime(fecha, dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y') + ' 0:00'
                hora_str = pd.to_datetime(hora, format='%H:%M:%S', errors='coerce').dt.strftime(
                    '1899/12/31 %H:%M:%S.000')
                return fecha_str, hora_str
            except:
                return fecha, hora

        # Aplicar transformaciones a todas las columnas de fecha/hora
        date_time_columns = [
            ('FECHA ADMISION', 'HORA ADMISION'),
            ('FECHA 1° CATEGORIZACION', 'HORA 1° CATEGORIZACION'),
            ('FECHA ULTIMA CATEGORIZACION', 'HORA ULTIMA CATEGORIZACION'),
            ('FECHA ANAMNESIS', 'HORA ANAMNESIS'),
            ('FECHA INDICACIONES', 'HORA INDICACIONES'),
            ('FECHA INDICACION REALIZADA', 'HORA INDICACION REALIZADA'),
            ('FECHA EVOLUCION', 'HORA EVOLCION'),
            ('FECHA ALTA', 'HORA ALTA'),
            ('fecha SIGNOS VITALES', 'HORA SIGNOS VITALES')
        ]

        for fecha_col, hora_col in date_time_columns:
            if fecha_col in data.columns and hora_col in data.columns:
                data[fecha_col], data[hora_col] = formatear_fecha_hora(data[fecha_col], data[hora_col])

        # Manejar valores nulos y vacíos
        text_columns = [col for col in data.columns if data[col].dtype == 'object']
        for col in text_columns:
            data[col] = data[col].replace(r'^\s*$', 'null', regex=True).fillna('null')
            data[col] = data[col].astype(str)

        # Asegurar todas las columnas requeridas
        expected_columns = [
            'ID', 'SERVICIO DE SALUD', 'ESTABLECIMIENTO', 'RUN', 'DV', 'RUN RESPONSABLE',
            'EDAD AÑOS', 'EDAD MESES', 'EDAD DIAS', 'SEXO', 'OTRA IDENTIFICACION',
            'NOMBRE PACIENTE', 'PREVISION', 'CALLE', 'NUMERO', 'DPTO', 'REGION',
            'COMUNA', 'COMUNA RESIDENCIA', 'REGIÓN RESIDENCIA', 'NACIONALIDAD',
            'TIPO USUARIO', 'ESTABLECIMIENTO DE INSCRIPCIÓN', 'CORRELATIVO',
            'FECHA ADMISION', 'HORA ADMISION', 'FECHA 1° CATEGORIZACION',
            'HORA 1° CATEGORIZACION', 'FECHA ULTIMA CATEGORIZACION',
            'HORA ULTIMA CATEGORIZACION', 'FECHA ANAMNESIS', 'HORA ANAMNESIS',
            'FECHA INDICACIONES', 'HORA INDICACIONES', 'FECHA INDICACION REALIZADA',
            'HORA INDICACION REALIZADA', 'FECHA EVOLUCION', 'HORA EVOLCION',
            'FECHA ALTA', 'HORA ALTA', 'NOMBRE FUNCIONARIO REALIZO ADMISION',
            'INSTRUMENTO QUE REALIZA ADMISION', 'PRIMERA CATEGORIZACION',
            'NOMBRE PROFESIONAL QUE REGISTRA PRIMERA CATEGORIZACION',
            'INSTRUMENTO PROFESIONAL QUE REGISTRA PRIEMRA CATEGORIZACION',
            'ULTIMA CATEGORIZACION', 'NOMBRE PROFESIONAL QUE REGISTRA ULTIMA CATEGORIZACION',
            'INSTRUMETO PROFESIONAL QUE REGISTRA ULTIMA CATEGORIZACION',
            'CODIGO DIAGNOSTICO', 'DIAGNOSTICO PRINCIPAL',
            'NOMBRE PROFESIONAL REGISTRA ANAMNESIS', 'INSTRUMETO PROFESIONAL REGISTRA ANAMNESIS',
            'NOMBRE PROFESIONAL REGISTRA EVOLUCIÓN', 'INSTRUMENTO PROFESIONAL REGISTRA EVOLUCIÓN',
            'PROCEDIMIENTO SOLICITADO', 'FUNCIONARIO REGISTRA EL PROCEDIMIENTO',
            'ESTAMENTO FUNCIONARIO REGISTRA PROCEDIMIENTO', 'FUNCIONARIO APLICA PROCEDIMIENTO',
            'ESTAMENTO FUNCIONARIO APLICA PROCEDIMIENTO', 'INDICACIONES',
            'NOMBRE FUNCIONARIO QUE REGISTRA INDICACIONES', 'INSTRUMENTO FUNCIONARIO QUE REGISTRA INDICACIONES',
            'DESTINO ALTA', 'FUNCIONARIO REGISTRA ALTA', 'INSTRUMENTO PROFESIONAL ALTA',
            'fecha SIGNOS VITALES', 'HORA SIGNOS VITALES', 'FUNCIONARIO REGISTRA SIGNOS VITALES',
            'INSTRUMENTO PROFESIONAL QUE REGISTRA SIGNOS VITALES', 'ESTADO',
            'MOTIVO EGRESO ADMINISTRATIVO', 'OBSERVACION MOTIVO EGRESO'
        ]

        for col in expected_columns:
            if col not in data.columns:
                data[col] = 'null'

        data = data[expected_columns]


        # Después de procesar los datos, antes de exportar a CSV:

        # A. Validar valores problemáticos en DV
        dv_invalidos = data[
            (data['DV'] != 'null') &
            (~data['DV'].str.match(r'^[0-9Kk]?$', na=True))
            ]

        if not dv_invalidos.empty:
            print(f"\n⚠️ Valores inválidos en DV (Total: {len(dv_invalidos)}):")
            print(dv_invalidos[['RUN', 'DV']].head(10))  # Muestra los primeros 10

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
            BULK INSERT el_bosque.dbo.tiempos
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
        if f.startswith("Informe_Urgencia_Tiempo_Espera") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_tiempos()

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
            procesar_lote_tiempos(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_tiempos(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")