import os
import pandas as pd
import pyodbc
import csv

# Configuración
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
temp_csv_path = r"G:\Mi unidad\UrgenciaQ\policonsultantes_temp.csv"


def crear_tabla_policonsultantes():
    """Crea la tabla policonsultantes si no existe"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS01;"
        "Database=el_bosque;"
        "Trusted_Connection=yes;"
    )

    create_table_sql = """
    CREATE TABLE el_bosque.dbo.policonsultantes (
        [ATEN ID] BIGINT,
        [ESTABLECIMIENTO INSCRIPCION] NVARCHAR(255),
        [SECTOR INSCRIPCIÓN] NVARCHAR(50),
        [COMUNA INSCRIPCIÓN] NVARCHAR(50),
        [ESTABLECIMIENTO ATENCION] NVARCHAR(255),
        [COMUNA ATENCION] NVARCHAR(50),
        [RUN] NVARCHAR(20) NULL,  -- Permitir NULL
        [DV] NVARCHAR(2) NULL,     -- Permitir NULL
        [OTRA IDENTIFICACION] NVARCHAR(50),
        [PREVISION] NVARCHAR(50),
        [CONVENIO] NVARCHAR(50),
        [DIRECCION FAMILIAR NOMBRE] NVARCHAR(255),
        [DIRECCION FAMILIAR NUMERO] NVARCHAR(20),
        [RESTO DIRECCION FAMILIAR] NVARCHAR(255),
        [DEPTO FAMILIAR] NVARCHAR(20),
        [NOMBRES] NVARCHAR(255),
        [PRIMER APELLIDO] NVARCHAR(255),
        [SEGUNDO APELLIDO] NVARCHAR(255),
        [FECHA HORA INGRESO] DATETIME,
        [EDAD AÑOS ATENCION] INT,
        [EDAD MESES ATENCION] INT,
        [EDAD DIAS ATENCION] INT,
        [SEXO] NVARCHAR(20),
        [MOTIVO CONSULTA] NVARCHAR(MAX),
        [CATEGORIZACIÓN] NVARCHAR(20),
        [DIAGNOSTICO] NVARCHAR(MAX),
        [CODIGO ESTANDAR] NVARCHAR(20),
        [TIPO DESTINO] NVARCHAR(50),
        [CANTIDAD ATENCIONES PERIODO] INT,
        [LlaveID] NVARCHAR(255),
        [GrupoEdad] NVARCHAR(50),
        [COD_1] NVARCHAR(5),
        [Edad2] NVARCHAR(50)
    )
    """

    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'policonsultantes'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'policonsultantes' creada exitosamente.")
            else:
                print("Tabla 'policonsultantes' ya existe.")
    except Exception as e:
        print(f"Error creando tabla: {str(e)}")
        raise


def procesar_lote_policonsultantes(files_lote, lote_index, temp_csv_path):
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")

    df_list = []
    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Lote {lote_index} - Leyendo: {file_name}")

        try:
            # Leer archivo saltando metadatos
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

        # Manejo de campos clave
        data['RUN'] = (
            data['RUN']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)  # quita el ".0" final típico de los floats
            .str.replace(r'\D', '', regex=True)  # luego elimina lo no numérico
        )
        data['DV'] = data['DV'].astype(str).str.replace(r'[^0-9Kk]', '', regex=True).str.upper()

        # Generar columnas adicionales
        data['LlaveID'] = data.apply(
            lambda x: f"P_{x['OTRA IDENTIFICACION']}" if pd.isnull(x['RUN']) or x[
                'RUN'] == '' else f"{x['RUN']}-{x['DV']}",
            axis=1
        )

        data['GrupoEdad'] = pd.cut(
            data['EDAD AÑOS ATENCION'],
            bins=[-1, 0, 5, 20, 64, 200],
            labels=[
                'a. Menor a 1 año',
                'b. Entre 1 a 5 años',
                'c. Entre 6 a 20 años',
                'd. Entre 21 a 64 años',
                'e. 65 años y más'
            ]
        )

        data['COD_1'] = data['CODIGO ESTANDAR'].str[0]
        data['Edad2'] = pd.cut(
            data['EDAD AÑOS ATENCION'],
            bins=[-1, 9, 19, 64, 200],
            labels=[
                'a- 0 a 9 años',
                'b- 10 a 19 años',
                'c- 20 a 64 años',
                'd- 65 años y más'
            ]
        )

        # Formatear fecha
        data['FECHA HORA INGRESO'] = pd.to_datetime(
            data['FECHA HORA INGRESO'],
            dayfirst=True,
            errors='coerce'
        ).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Manejar valores nulos
        text_columns = [col for col in data.columns if data[col].dtype == 'object']
        for col in text_columns:
            data[col] = data[col].replace(r'^\s*$', 'null', regex=True).fillna('null')
            data[col] = data[col].astype(str)

        # Orden de columnas requerido
        column_order = [
            'ATEN ID', 'ESTABLECIMIENTO INSCRIPCION', 'SECTOR INSCRIPCIÓN',
            'COMUNA INSCRIPCIÓN', 'ESTABLECIMIENTO ATENCION', 'COMUNA ATENCION',
            'RUN', 'DV', 'OTRA IDENTIFICACION', 'PREVISION', 'CONVENIO',
            'DIRECCION FAMILIAR NOMBRE', 'DIRECCION FAMILIAR NUMERO',
            'RESTO DIRECCION FAMILIAR', 'DEPTO FAMILIAR', 'NOMBRES',
            'PRIMER APELLIDO', 'SEGUNDO APELLIDO', 'FECHA HORA INGRESO',
            'EDAD AÑOS ATENCION', 'EDAD MESES ATENCION', 'EDAD DIAS ATENCION',
            'SEXO', 'MOTIVO CONSULTA', 'CATEGORIZACIÓN', 'DIAGNOSTICO',
            'CODIGO ESTANDAR', 'TIPO DESTINO', 'CANTIDAD ATENCIONES PERIODO',
            'LlaveID', 'GrupoEdad', 'COD_1', 'Edad2'
        ]

        data = data[column_order]

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
            BULK INSERT el_bosque.dbo.policonsultantes
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
        if f.startswith("Policonsultantes_") and f.endswith('.xlsx'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar")
        exit()

    # Crear tabla si no existe
    crear_tabla_policonsultantes()

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
            procesar_lote_policonsultantes(current_lote, lote_index, temp_csv_path)
            lote_index += 1
            current_lote = []
            current_size = 0

        current_lote.append(file_info)
        current_size += file_size

    if current_lote:
        procesar_lote_policonsultantes(current_lote, lote_index, temp_csv_path)

    print("\nProceso completado exitosamente!")