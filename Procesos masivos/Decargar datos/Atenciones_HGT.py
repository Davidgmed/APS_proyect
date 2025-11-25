# -*- coding: utf-8 -*-
"""
Procesa reportes de hemoglucotest descargados previamente por Urgencia_newIris.
Consolida la nueva estructura (encabezado interno), conserva por (RUN, FECHA
REGISTRO HEMOGLUCOTEST) la medición con mayor VALOR HEMOGLUCOTEST y escribe en
Google Sheets "Casos glicemia descompensada" en hojas por ESTABLECIMIENTO.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_tabla = fecha_ayer.strftime("%Y-%m-%d")
fecha_ayer_str_simple = fecha_ayer.strftime("%Y%m%d")

# --- Configuración del directorio de descargas (archivos generados por Urgencia_newIris) ---
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
FILE_PREFIX = "Informe_Pacientes_Con_Hemoglucotest"

# --- Configuración de Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r'G:\Mi unidad\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Casos glicemia descompensada")


worksheet_cache = {}


def open_or_create_worksheet(spreadsheet_obj, title: str):
    """Abre una hoja por título o la crea si no existe."""
    if title in worksheet_cache:
        return worksheet_cache[title], False

    try:
        worksheet_cache[title] = spreadsheet_obj.worksheet(title)
        return worksheet_cache[title], False
    except gspread.WorksheetNotFound:
        worksheet_cache[title] = spreadsheet_obj.add_worksheet(title=title, rows=1000, cols=20)
        return worksheet_cache[title], True


def append_df_to_sheet(df, sheet_name):
    """Función para agregar datos a una hoja específica en Google Sheets."""
    worksheet, is_new = open_or_create_worksheet(spreadsheet, sheet_name)
    rows = df.values.tolist()
    if is_new:
        worksheet.append_row(list(df.columns))
    if rows:
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')


# ====================== PROCESAMIENTO & CARGA A GOOGLE SHEETS =================
ESTABLISHMENT_TO_SHEET: Dict[str, str] = {
    'Centro de Salud Familiar Mario Salcedo': 'Mario Salcedo',
    'Centro de Salud Familiar Dra. Haydeé López Casoou': 'Haydeé López',
    'Centro De Salud Familiar Dr. Carlos Lorca': 'Carlos Lorca',
    'Centro Comunitario de Salud Familiar Los Sauces': 'Carlos Lorca',
    'Centro De Salud Familiar Cóndores De Chile': 'Cóndores de Chile',
    'Centro de Salud Familiar Santa Laura': 'Santa Laura',
    'Centro Comunitario Salud Familiar Santa Laura': 'Santa Laura',
    'Centro de Salud Familiar Orlando Letelier': 'Orlando Letelier',
    'COSAM El Bosque': 'Sector 0',
    'UAPO El Bosque': 'Sector 0',
    'UAPORRINO El Bosque': 'Sector 0',
    'Centro Salud Adolescente': 'Sector 0',
    'Direccion de Salud Municipal': 'Sector 0',
    'Centro de Atencion Integral en Salud': 'Sector 0',
    'Centro Comunitario de Rehabilitación El Bosque': 'Sector 0',
    'Centro Especialidad el Bosque': 'Sector 0'
}

REQUIRED_COLUMNS = {
    'NOMBRE PACIENTE',
    'PRIMER APELLIDO',
    'SEGUNDO APELLIDO',
    'RUN',
    'DV',
    'SECTOR',
    'FECHA REGISTRO HEMOGLUCOTEST',
    'VALOR HEMOGLUCOTEST',
    'ESTABLECIMIENTO DE INSCRIPCION'
}

RENAME_MAP = {
    'NOMBRE PACIENTE': 'Nombre',
    'PRIMER APELLIDO': 'PrimerAp',
    'SEGUNDO APELLIDO': 'SegundoAp',
    'RUN': 'RUN',
    'DV': 'DV',
    'SECTOR': 'Sector',
    'FECHA REGISTRO HEMOGLUCOTEST': 'Fecha',
    'VALOR HEMOGLUCOTEST': 'Valor'
}
OUTPUT_COLUMNS = ['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor']


def list_matching_reports(folder: str) -> List[str]:
    files = []
    for f in os.listdir(folder):
        if f.startswith(FILE_PREFIX) and f.lower().endswith(".xlsx") and not f.startswith("~$"):
            files.append(os.path.join(folder, f))
    return files


def read_report_table(path: str, sheet_name=None) -> pd.DataFrame:
    df_raw = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str)
    header_row_idx = None
    for i in range(min(80, len(df_raw))):
        first_cell = str(df_raw.iloc[i, 0]).strip() if pd.notna(df_raw.iloc[i, 0]) else ""
        if first_cell.upper() == "NOMBRE PACIENTE":
            header_row_idx = i
            break

    if header_row_idx is None:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    else:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row_idx, dtype=str)

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how='all', axis=1)
    df = df.dropna(how='all', axis=0)
    return df


def read_all_reports_from_file(xlsx_path: str) -> List[pd.DataFrame]:
    out = []
    try:
        xls = pd.ExcelFile(xlsx_path)
        for sh in xls.sheet_names:
            try:
                df_sh = read_report_table(xlsx_path, sheet_name=sh)
                if REQUIRED_COLUMNS.issubset(set(df_sh.columns)):
                    out.append(df_sh.copy())
            except Exception:
                continue
    except Exception as e:
        print(f"[WARN] No se pudo abrir {xlsx_path}: {e}")
    return out


def consolidate_and_pick_max(all_frames: List[pd.DataFrame]) -> pd.DataFrame:
    if not all_frames:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    df_all = pd.concat(all_frames, ignore_index=True)

    for col in [
        'RUN', 'DV', 'SECTOR', 'FECHA REGISTRO HEMOGLUCOTEST', 'VALOR HEMOGLUCOTEST',
        'NOMBRE PACIENTE', 'PRIMER APELLIDO', 'SEGUNDO APELLIDO', 'ESTABLECIMIENTO DE INSCRIPCION'
    ]:
        if col in df_all.columns:
            df_all[col] = df_all[col].astype(str).str.strip()

    df_all['VALOR HEMOGLUCOTEST'] = pd.to_numeric(df_all.get('VALOR HEMOGLUCOTEST', pd.NA), errors='coerce')

    df_valid = df_all.dropna(subset=['RUN', 'FECHA REGISTRO HEMOGLUCOTEST', 'VALOR HEMOGLUCOTEST']).copy()
    idx_max = df_valid.groupby(['RUN', 'FECHA REGISTRO HEMOGLUCOTEST'])['VALOR HEMOGLUCOTEST'].idxmax()
    return df_valid.loc[idx_max].copy()


def build_output(df_max: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df_max.columns)
    if missing:
        raise ValueError(f"Faltan columnas esperadas en los datos consolidados: {missing}")

    df_out = df_max[list(RENAME_MAP.keys()) + ['ESTABLECIMIENTO DE INSCRIPCION']].rename(columns=RENAME_MAP)
    df_out = df_out[['Nombre', 'PrimerAp', 'SegundoAp', 'RUN', 'DV', 'Sector', 'Fecha', 'Valor', 'ESTABLECIMIENTO DE INSCRIPCION']]
    return df_out


def main():
    downloaded_files = list_matching_reports(download_dir)
    if not downloaded_files:
        print("No se encontraron archivos de hemoglucotest generados por Urgencia_newIris.")
        raise SystemExit

    dfs_validas: List[pd.DataFrame] = []
    for file in downloaded_files:
        try:
            dfs_validas.extend(read_all_reports_from_file(file))
        except Exception as e:
            print(f"Error leyendo {file}: {str(e)}")

    if not dfs_validas:
        print("No se encontraron archivos válidos para procesar")
        raise SystemExit

    df_max = consolidate_and_pick_max(dfs_validas)
    df_out = build_output(df_max)

    df_out['Valor'] = pd.to_numeric(df_out['Valor'], errors='coerce')
    df_out = df_out[df_out['Valor'] >= 200].copy()
    df_out['Fecha'] = pd.to_datetime(df_out['Fecha'], errors='coerce', dayfirst=True)
    df_out['Fecha'] = df_out['Fecha'].dt.strftime("%d-%m-%Y")
    df_out['FechaCarga'] = fecha_actual.strftime("%d-%m-%Y")
    df_out['CentroAtencion'] = df_out['ESTABLECIMIENTO DE INSCRIPCION'].apply(
        lambda est: ESTABLISHMENT_TO_SHEET.get(est, est)
    )
    df_out['RUT'] = df_out['RUN'].astype(str).str.strip() + "-" + df_out['DV'].astype(str).str.strip()

    COLUMNAS_SALIDA = [
        'FechaCarga',
        'CentroAtencion',
        'Sector',
        'Nombre',
        'PrimerAp',
        'SegundoAp',
        'RUT',
        'Fecha',
        'Valor'
    ]

    total_escritos = 0
    for est, hoja in ESTABLISHMENT_TO_SHEET.items():
        block = df_out[df_out['ESTABLECIMIENTO DE INSCRIPCION'] == est]
        if not block.empty:
            block = block[COLUMNAS_SALIDA]
            append_df_to_sheet(block, hoja)
            total_escritos += len(block)
            print(f"Agregados {len(block)} registros a hoja '{hoja}'")

    externos = df_out[~df_out['ESTABLECIMIENTO DE INSCRIPCION'].isin(ESTABLISHMENT_TO_SHEET.keys())]
    if not externos.empty:
        externos = externos[COLUMNAS_SALIDA]
        append_df_to_sheet(externos, 'Externos')
        total_escritos += len(externos)
        print(f"Agregados {len(externos)} registros a hoja 'Externos'")

    print(f"Proceso completado exitosamente. Registros escritos: {total_escritos}")


if __name__ == "__main__":
    main()
