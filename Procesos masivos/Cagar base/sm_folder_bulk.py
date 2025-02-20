import os
import pandas as pd
import pyodbc
import csv
import numpy as np
import re

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
SIZE_LIMIT = 12 * 1024 * 1024  # 12 MB
folder_path = r"G:\Mi unidad\SaludMental\data2"
# 1. Definir ruta local accesible desde el servicio de SQL Server
temp_csv_path = r"C:\temp\formulario_temp.csv"
os.makedirs(os.path.dirname(temp_csv_path), exist_ok=True)

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost\\SQLEXPRESS01;"
    "Database=el_bosque;"
    "Trusted_Connection=yes;"
)

# =============================================================================
# CREACIÓN DE TABLA (CON TODOS LOS 90 CAMPOS)
# =============================================================================
def crear_tabla_sm_formulario():
    """Crea la tabla sm_formulario con todos los campos requeridos."""
    create_table_sql = """
    CREATE TABLE el_bosque.dbo.sm_formulario (
        [SERVICIO SALUD] NVARCHAR(255),
        [ESTABLECIMIENTO] NVARCHAR(255),
        [RUT] NVARCHAR(50),
        [DV] NVARCHAR(1),
        [CODIGO FAMILIA] NVARCHAR(255),
        [NUMERO DE FICHA RAYEN] NVARCHAR(255),
        [NUMERO DE FICHA CODIGO ANTIGUO] NVARCHAR(255),
        [PACIENTE] NVARCHAR(255),
        [FECHA DE NACIMIENTO] NVARCHAR(255),
        [EDAD PACIENTE] NVARCHAR(255),
        [AÑO APLICACIÓN FORMULARIO] NVARCHAR(50),
        [MES APLICACIÓN FORMULARIO] NVARCHAR(50),
        [DÍAS APLICACIÓN FORMULARIO] NVARCHAR(50),
        [PUEBLO ORIGINARIO] NVARCHAR(255),
        [ALERTAS ADMINISTRATIVAS] NVARCHAR(255),
        [NACIONALIDAD] NVARCHAR(255),
        [SEXO] NVARCHAR(50),
        [GENERO] NVARCHAR(50),
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
        [FECHA FORMULARIO] NVARCHAR(255),
        [FUNCIONARIO] NVARCHAR(255),
        [INSTRUMENTO] NVARCHAR(255),
        [ESTABLECIMIENTO INSCRIPCION] NVARCHAR(255),
        [FORMULARIO] NVARCHAR(255),
        [FUNCIONARIOS FORMULARIO] NVARCHAR(255),
        [1.- ¿USTED ES MADRE DE HIJO MENOR DE 5 AÑOS?] NVARCHAR(255),
        [2.- FECHA PRÓXIMO CONTROL] NVARCHAR(255),
        [3.- ¿ ES VÍCTIMA O AGRESOR/A DE VIOLENCIA?] NVARCHAR(255),
        [4.- ESTADO] NVARCHAR(255),
        [5.- EN LA VIOLENCIA ES] NVARCHAR(255),
        [6.- OBSERVACIONES] NVARCHAR(255),
        [7.- ¿ SUFRE DE ABUSO SEXUAL ?] NVARCHAR(255),
        [8.- ESTADO] NVARCHAR(255),
        [9.- ¿EPISODIO DE SUICIDIO?] NVARCHAR(255),
        [10.- TIPO DE SUICIDIO] NVARCHAR(255),
        [11.- ESTADO] NVARCHAR(255),
        [12.- PLAN AMBULATORIO BÁSICO] NVARCHAR(255),
        [13.- INTERVENCIÓN PREVENTIVA] NVARCHAR(255),
        [14.- INTERVENCIÓN BREVE] NVARCHAR(255),
        [15.- INTERVENCIÓN TERAPEUTICA] NVARCHAR(255),
        [16.- ¿ TIENE  DEPRESIÓN ?] NVARCHAR(255),
        [17.- ESTADO] NVARCHAR(255),
        [18.- TIPO DE DEPRESIÓN] NVARCHAR(255),
        [19.- ¿ TIENE DEPRESIÓN POST - PARTO ?] NVARCHAR(255),
        [20.- ESTADO] NVARCHAR(255),
        [21.- ¿ TIENE TRANSTORNO BIPOLAR ?] NVARCHAR(255),
        [22.- ESTADO] NVARCHAR(255),
        [23.- ¿TIENE DEPRESIÓN REFRACTARIA?] NVARCHAR(255),
        [24.- ESTADO] NVARCHAR(255),
        [25.- ¿TIENE DEPRESIÓN GRAVE CON PSICOSIS?] NVARCHAR(255),
        [26.- ESTADO] NVARCHAR(255),
        [27.- ¿TIENE DEPRESIÓN CON ALTO RIESGO SUICIDA?] NVARCHAR(255),
        [28.- ESTADO] NVARCHAR(255),
        [29.- CONSUMO PERJUDICIAL DE ALCOHOL] NVARCHAR(255),
        [30.- ESTADO] NVARCHAR(255),
        [31.- CONSUMO DEPENDIENTE DEL ALCOHOL] NVARCHAR(255),
        [32.- ESTADO] NVARCHAR(255),
        [33.- CONSUMO PERJUDICIAL DE DROGAS] NVARCHAR(255),
        [34.- ESTADO] NVARCHAR(255),
        [35.- CONSUMO DEPENDIENTE DE DROGAS] NVARCHAR(255),
        [36.- ESTADO] NVARCHAR(255),
        [37.- CONSUMO DE DROGAS Y ALCOHOL] NVARCHAR(255),
        [38.- ESTADO] NVARCHAR(255),
        [39.- ¿ TIENE TRASTORNO DE ANSIEDAD ?] NVARCHAR(255),
        [40.- ESTADO] NVARCHAR(255),
        [41.- TIPO DE TRASTORNO DE ANSIEDAD] NVARCHAR(255),
        [42.- ¿ TIENE ALZHEIMER Y/O OTRAS DEMENCIAS ?] NVARCHAR(255),
        [43.- ETAPA] NVARCHAR(255),
        [44.- ESTADO] NVARCHAR(255),
        [45.- ¿TIENE PSICOSIS?] NVARCHAR(255),
        [46.- ESTADO] NVARCHAR(255),
        [47.- ¿TIENE TRASTORNO ADAPTATIVO?] NVARCHAR(255),
        [48.- ESTADO] NVARCHAR(255),
        [49.- ¿ TIENE ESQUIZOFRENIA ?] NVARCHAR(255),
        [50.- ESTADO] NVARCHAR(255),
        [51.- ¿TIENE UN PRIMER EPISODIOO DE ESQUIZOFRENIA CON OC] NVARCHAR(255),
        [52.- ESTADO] NVARCHAR(255),
        [53.- ¿ TIENE TRASTORNO DE LA CONDUCTA ALIMENTARIA ?] NVARCHAR(255),
        [54.- ESTADO] NVARCHAR(255),
        [55.- ¿ TIENE TRASTORNOS HIPERCINÉTICOS, DE LA ACTIVIDAD] NVARCHAR(255),
        [56.- ESTADO] NVARCHAR(255),
        [57.- ¿ TIENE RETRASO MENTAL ?] NVARCHAR(255),
        [58.- ESTADO] NVARCHAR(255),
        [59.- ¿ TIENE TRASTORNO DE PERSONALIDAD ?] NVARCHAR(255),
        [60.- ESTADO] NVARCHAR(255),
        [61.- ¿ TIENE TRASTORNO GENERALIZADO DEL DESARROLLO ?] NVARCHAR(255),
        [62.- ESTADO] NVARCHAR(255),
        [63.- OTRAS (TRASTORNOS NO INCLUIDOS EN SECCIÓN)] NVARCHAR(255),
        [64.- ESTADO] NVARCHAR(255),
        [65.- ¿TIENE TRASTORNOS CONDUCTALES ASOCIADOS A DEMENCIA] NVARCHAR(255),
        [66.- ESTADO] NVARCHAR(255),
        [67.- ¿TIENE TRASTORNO DISOCIAL DESAFIANTE Y OPOSICIONIS] NVARCHAR(255),
        [68.- ESTADO] NVARCHAR(255),
        [69.- ¿TIENE TRASTORNO DE ANSIEDAD DE SEPARACIÓN EN LA I] NVARCHAR(255),
        [70.- ESTADO] NVARCHAR(255),
        [71.- ¿TIENE OTROS TRASTORNOS DEL COMPORTAMIENTO Y DE LA] NVARCHAR(255),
        [72.- ESTADO] NVARCHAR(255),
        [73.- ¿PACIENTE PRESENTA EPILEPSIA?] NVARCHAR(255),
        [74.- ESTADO] NVARCHAR(255),
        [75.- PROGRAMA REHABILITACIÓN TIPO I] NVARCHAR(255),
        [76.- ESTADO] NVARCHAR(255),
        [77.- PROGRAMA REHABILITACIÓN TIPO II] NVARCHAR(255),
        [78.- ESTADO] NVARCHAR(255),
        [79.- PROGRAMA ACOMPAÑAMIENTO PSICOSOCIAL] NVARCHAR(255),
        [80.- ESTADO] NVARCHAR(255),
        [81.- ¿TIENE AUTISMO?] NVARCHAR(255),
        [82.- ESTADO] NVARCHAR(255),
        [83.- ¿TIENE ASPERGER?] NVARCHAR(255),
        [84.- ESTADO] NVARCHAR(255),
        [85.- ¿TIENE SÍNDROME DE RETT?] NVARCHAR(255),
        [86.- ESTADO] NVARCHAR(255),
        [87.- ¿TIENE TRASTORNO DESINTEGRATIVO DE LA INFANCIA?] NVARCHAR(255),
        [88.- ESTADO] NVARCHAR(255),
        [89.- ¿TIENE TRASTORNO GENERALIZADO DEL DESARROLLO DE LA] NVARCHAR(255),
        [90.- ESTADO] NVARCHAR(255)
    )
    """

    try:
        with pyodbc.connect(CONN_STR, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'sm_formulario'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(create_table_sql)
                print("Tabla 'sm_formulario' creada exitosamente.")
            else:
                print("La tabla 'sm_formulario' ya existe.")
    except Exception as e:
        print(f"Error al crear la tabla: {str(e)}")
        raise

# =============================================================================
# VALIDAR RUT (FUNCIÓN AUXILIAR)
# =============================================================================
def validar_rut(rut):
    """Valida el formato del RUT (ej: 12345678-9)."""
    if pd.isna(rut):
        return False
    rut_str = str(rut).strip().upper()
    return re.match(r"^\d{7,8}-[\dK]$", rut_str) is not None

# =============================================================================
# PROCESAR LOTE DE ARCHIVOS
# =============================================================================
def procesar_lote(files_lote, lote_index, temp_csv_path):
    if not files_lote:
        return

    print(f"\n=== Procesando lote {lote_index} ({len(files_lote)} archivos) ===")
    df_list = []

    for file_info in files_lote:
        file_name, _ = file_info
        full_path = os.path.join(folder_path, file_name)
        print(f"Leyendo archivo: {file_name}")

        try:
            df = pd.read_excel(
                full_path,
                header=16,
                engine='openpyxl',
                dtype=str)
            df_list.append(df)
        except Exception as e:
            print(f"Error al leer {file_name}: {str(e)}")
            continue

    if not df_list:
        print("No hay datos válidos para procesar.")
        return

    try:
        data = pd.concat(df_list, ignore_index=True)

        # Limpiar nombres de columnas
        data.columns = data.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

        # Validar RUT y filtrar
        #if 'RUT' in data.columns:
        #    data = data[data['RUT'].apply(validar_rut)]

        # ---- Paso 1: Guardar DataFrame en un log para inspección ----
        debug_log_path = r"G:\Mi unidad\SaludMental\debug_log.txt"

        with open(debug_log_path, 'w', encoding='utf-8') as f:
            f.write("=== DATAFRAME ANTES DE EXPORTAR A CSV ===\n")
            f.write(f"Columnas: {data.columns.tolist()}\n")
            f.write(data.head(3).to_string() + "\n")  # Primeras 3 filas

        # Definir todas las columnas requeridas (90)
        final_cols = [
            'SERVICIO SALUD', 'ESTABLECIMIENTO', 'RUT', 'DV', 'CODIGO FAMILIA',
            'NUMERO DE FICHA RAYEN', 'NUMERO DE FICHA CODIGO ANTIGUO', 'PACIENTE',
            'FECHA DE NACIMIENTO', 'EDAD PACIENTE', 'AÑO APLICACIÓN FORMULARIO',
            'MES APLICACIÓN FORMULARIO', 'DÍAS APLICACIÓN FORMULARIO', 'PUEBLO ORIGINARIO',
            'ALERTAS ADMINISTRATIVAS', 'NACIONALIDAD', 'SEXO', 'GENERO', 'SECTOR INSCRIPCION',
            'SECTOR CITA', 'DIRECCIÓN', 'COMUNA', 'TELEFONO 1', 'TELEFONO 2', 'PREVISION',
            'CONVENIO', 'SITUACION', 'ESTADO', 'FUNCIONARIO PASIVADOR', 'ATEN ID',
            'FECHA ATENCION', 'FECHA FORMULARIO', 'FUNCIONARIO', 'INSTRUMENTO',
            'ESTABLECIMIENTO INSCRIPCION', 'FORMULARIO', 'FUNCIONARIOS FORMULARIO',
            '1.- ¿USTED ES MADRE DE HIJO MENOR DE 5 AÑOS?', '2.- FECHA PRÓXIMO CONTROL',
            '3.- ¿ ES VÍCTIMA O AGRESOR/A DE VIOLENCIA?', '4.- ESTADO', '5.- EN LA VIOLENCIA ES',
            '6.- OBSERVACIONES', '7.- ¿ SUFRE DE ABUSO SEXUAL ?', '8.- ESTADO',
            '9.- ¿EPISODIO DE SUICIDIO?', '10.- TIPO DE SUICIDIO', '11.- ESTADO',
            '12.- PLAN AMBULATORIO BÁSICO', '13.- INTERVENCIÓN PREVENTIVA',
            '14.- INTERVENCIÓN BREVE', '15.- INTERVENCIÓN TERAPEUTICA',
            '16.- ¿ TIENE  DEPRESIÓN ?', '17.- ESTADO', '18.- TIPO DE DEPRESIÓN',
            '19.- ¿ TIENE DEPRESIÓN POST - PARTO ?', '20.- ESTADO',
            '21.- ¿ TIENE TRANSTORNO BIPOLAR ?', '22.- ESTADO', '23.- ¿TIENE DEPRESIÓN REFRACTARIA?',
            '24.- ESTADO', '25.- ¿TIENE DEPRESIÓN GRAVE CON PSICOSIS?', '26.- ESTADO',
            '27.- ¿TIENE DEPRESIÓN CON ALTO RIESGO SUICIDA?', '28.- ESTADO',
            '29.- CONSUMO PERJUDICIAL DE ALCOHOL', '30.- ESTADO', '31.- CONSUMO DEPENDIENTE DEL ALCOHOL',
            '32.- ESTADO', '33.- CONSUMO PERJUDICIAL DE DROGAS', '34.- ESTADO',
            '35.- CONSUMO DEPENDIENTE DE DROGAS', '36.- ESTADO', '37.- CONSUMO DE DROGAS Y ALCOHOL',
            '38.- ESTADO', '39.- ¿ TIENE TRASTORNO DE ANSIEDAD ?', '40.- ESTADO',
            '41.- TIPO DE TRASTORNO DE ANSIEDAD', '42.- ¿ TIENE ALZHEIMER Y/O OTRAS DEMENCIAS ?',
            '43.- ETAPA', '44.- ESTADO', '45.- ¿TIENE PSICOSIS?', '46.- ESTADO',
            '47.- ¿TIENE TRASTORNO ADAPTATIVO?', '48.- ESTADO', '49.- ¿ TIENE ESQUIZOFRENIA ?',
            '50.- ESTADO', '51.- ¿TIENE UN PRIMER EPISODIOO DE ESQUIZOFRENIA CON OC',
            '52.- ESTADO', '53.- ¿ TIENE TRASTORNO DE LA CONDUCTA ALIMENTARIA ?',
            '54.- ESTADO', '55.- ¿ TIENE TRASTORNOS HIPERCINÉTICOS, DE LA ACTIVIDAD',
            '56.- ESTADO', '57.- ¿ TIENE RETRASO MENTAL ?', '58.- ESTADO',
            '59.- ¿ TIENE TRASTORNO DE PERSONALIDAD ?', '60.- ESTADO',
            '61.- ¿ TIENE TRASTORNO GENERALIZADO DEL DESARROLLO ?', '62.- ESTADO',
            '63.- OTRAS (TRASTORNOS NO INCLUIDOS EN SECCIÓN)', '64.- ESTADO',
            '65.- ¿TIENE TRASTORNOS CONDUCTALES ASOCIADOS A DEMENCIA', '66.- ESTADO',
            '67.- ¿TIENE TRASTORNO DISOCIAL DESAFIANTE Y OPOSICIONIS', '68.- ESTADO',
            '69.- ¿TIENE TRASTORNO DE ANSIEDAD DE SEPARACIÓN EN LA I', '70.- ESTADO',
            '71.- ¿TIENE OTROS TRASTORNOS DEL COMPORTAMIENTO Y DE LA', '72.- ESTADO',
            '73.- ¿PACIENTE PRESENTA EPILEPSIA?', '74.- ESTADO', '75.- PROGRAMA REHABILITACIÓN TIPO I',
            '76.- ESTADO', '77.- PROGRAMA REHABILITACIÓN TIPO II', '78.- ESTADO',
            '79.- PROGRAMA ACOMPAÑAMIENTO PSICOSOCIAL', '80.- ESTADO', '81.- ¿TIENE AUTISMO?',
            '82.- ESTADO', '83.- ¿TIENE ASPERGER?', '84.- ESTADO', '85.- ¿TIENE SÍNDROME DE RETT?',
            '86.- ESTADO', '87.- ¿TIENE TRASTORNO DESINTEGRATIVO DE LA INFANCIA?', '88.- ESTADO',
            '89.- ¿TIENE TRASTORNO GENERALIZADO DEL DESARROLLO DE LA', '90.- ESTADO'
        ]

        # Con esta solución optimizada:
        # Identificar columnas faltantes
        missing_cols = [col for col in final_cols if col not in data.columns]

        # Crear DataFrame con las columnas faltantes inicializadas en NaN
        missing_data = pd.DataFrame(np.nan, index=data.index, columns=missing_cols)

        # Concatenar horizontalmente
        data = pd.concat([data, missing_data], axis=1)

        # Reordenar columnas según final_cols y desfragmentar
        data = data[final_cols].copy()

        def safe_encode(value):
            """Codifica valores y detecta caracteres problemáticos."""
            if isinstance(value, str):
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError as e:
                    print(f"¡Carácter problemático detectado!: {value}")
                    print(f"Posición del error: {e.start}-{e.end}")
                    print(f"Contexto: {value[max(0, e.start-10):e.end+10]}")
                    # Guardar en log
                    with open(debug_log_path, 'a', encoding='utf-8') as f:
                        f.write(f"\nERROR ENCODING: {value}\n")
                    return value.encode('utf-8', errors='replace')  # Reemplazar caracteres inválidos
            return value

        # Aplicar a todo el DataFrame
        data = data.map(safe_encode).map(
            lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        )

        def limpiar_caracteres(texto):
            if isinstance(texto, str):
                return texto.encode('utf-8', 'ignore').decode('utf-8')
            return texto

        data = data.map(limpiar_caracteres)

        # Exportar a CSV temporal
        try:
            # 2. Exportar CSV con separador '~', BOM UTF-8 y terminador de línea '\n'
            data.to_csv(
                temp_csv_path,
                index=False,
                sep='~',
                quoting=csv.QUOTE_ALL,
                encoding='utf-8',
                escapechar='\\'
            )

            print(f"CSV generado en {temp_csv_path} con {data.shape[0]} filas.")


        except UnicodeEncodeError as e:
            # Capturar información detallada del error
            error_context = {
                'error': str(e),
                'position': e.start,
                'object': e.object[max(0, e.start - 15):e.end + 15],  # 15 caracteres alrededor
                'archivos': [f[0] for f in files_lote]
            }
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write("\n=== ERROR DURANTE EXPORTACIÓN CSV ===\n")
                f.write(str(error_context) + "\n")
            raise

        if os.path.exists(temp_csv_path):
            with open(temp_csv_path, 'r', encoding='utf-8-sig') as f:  # Usar utf-8-sig
                line_count = len(f.readlines())
            print(f"Filas en CSV temporal: {line_count}")  # Debe ser >1 (encabezado + datos)

            # ---- Paso 4: Inspeccionar CSV generado ----
            with open(temp_csv_path, 'rb') as f:
                content = f.read()
                try:
                    content.decode('utf-8-sig')
                except UnicodeDecodeError as e:
                    print(f"\nERROR EN CSV TEMPORAL - BYTE PROBLEMÁTICO: {hex(content[e.start])}")
                    print(f"Contexto hexadecimal: {content[max(0, e.start - 10):e.start + 10].hex(' ')}")
                    print(
                        f"Contexto texto (replace): {content[max(0, e.start - 10):e.start + 10].decode('utf-8', errors='replace')}")

                    # Escribir posición exacta en el log
                    with open(debug_log_path, 'a', encoding='utf-8') as f_log:
                        f_log.write(f"\nERROR EN CSV: Byte {hex(content[e.start])} en posición {e.start}\n")
                        f_log.write(f"Lote: {lote_index}, Archivos: {files_lote}\n")
                    raise

        # Después de generar el CSV, añadir:
        with open(temp_csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        # Filtrar líneas que no empiecen con #
        lines = [line for line in lines if not line.startswith('#')]

        with open(temp_csv_path, 'w', encoding='utf-8-sig') as f:
            f.writelines(lines)

        # Antes del BULK INSERT, añadir:
        with open(temp_csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            print("Primeras 3 líneas del CSV:")
            print(lines[0])  # Encabezados
            print(lines[1])  # Primera fila
            print(lines[2])  # Segunda fila



        # BULK INSERT
        with pyodbc.connect(CONN_STR) as conn:
            cursor = conn.cursor()
            bulk_insert_sql = f"""
            BULK INSERT el_bosque.dbo.sm_formulario
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
# EJECUCIÓN PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    # Listar archivos
    files_info = []
    for f in os.listdir(folder_path):
        if f.startswith("Formularios_RAYEN") and f.endswith(".xlsx"):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            files_info.append((f, size))

    if not files_info:
        print("No se encontraron archivos para procesar.")
        exit()

    crear_tabla_sm_formulario()

    # Ordenar y procesar en lotes
    files_info.sort(key=lambda x: x[1])
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

    # Procesar último lote
    if current_lote:
        procesar_lote(current_lote, lote_index, temp_csv_path)

    print("\n¡Proceso completado con éxito!")