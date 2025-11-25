# -*- coding: utf-8 -*-
"""
Procesa reportes de Presión Arterial descargados previamente por Urgencia_newIris.
Consolida información, calcula PAS/PAD máximas por paciente y fecha, genera
alertas y escribe en Google Sheets en hojas por ESTABLECIMIENTO.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

import gspread
import numpy as np
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_tabla = fecha_ayer.strftime("%Y-%m-%d")
fecha_ayer_str_simple = fecha_ayer.strftime("%Y%m%d")

# --- Configuración del directorio de descargas (archivos generados por Urgencia_newIris) ---
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
FILE_PREFIX = "Informe_de_Atenciones_por_Diagnostico_Urgencia_Web"

# --- Configuración de Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r'G:\Mi unidad\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Casos presion arterial descompensada")


def open_or_create_worksheet(spreadsheet_obj, title: str):
    """Abre una hoja por título o la crea si no existe."""
    try:
        return spreadsheet_obj.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet_obj.add_worksheet(title=title, rows=1000, cols=20)


def append_df_to_sheet(df, sheet_name):
    """Función para agregar datos a una hoja específica en Google Sheets."""
    worksheet = open_or_create_worksheet(spreadsheet, sheet_name)
    existing_data = worksheet.get_all_values()
    if not existing_data:
        worksheet.append_row(list(df.columns))  # si está vacía, escribir encabezados
    start_row = len(existing_data) + 1
    rows = df.values.tolist()
    if rows:
        worksheet.append_rows(rows, table_range=f"A{start_row}")


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
    'ID',
    'RUN',
    'DV',
    'NOMBRE',
    'PRIMER APELLIDO',
    'SEGUNDO APELLIDO',
    'SECTOR PACIENTE',
    'ESTABLECIMIENTO',
    'FECHA ATENCION',
    'PRESION ARTERIAL'
}


def list_xlsx_files(folder: str) -> List[str]:
    all_files = []
    for f in os.listdir(folder):
        if f.startswith(FILE_PREFIX) and f.lower().endswith(".xlsx") and not f.startswith("~$"):
            all_files.append(os.path.join(folder, f))
    return all_files


def read_report_table(path: str, sheet_name=None) -> pd.DataFrame:
    df_raw = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str)
    header_row_idx = None
    for i in range(min(80, len(df_raw))):
        first_cell = str(df_raw.iloc[i, 0]).strip() if pd.notna(df_raw.iloc[i, 0]) else ""
        if first_cell.upper() == "ID":
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
            except Exception as e:
                print(f"Error leyendo hoja {sh} en {xlsx_path}: {e}")
                continue
    except Exception as e:
        print(f"[WARN] No se pudo abrir {xlsx_path}: {e}")
    return out


def consolidate_pa(all_frames: List[pd.DataFrame]) -> pd.DataFrame:
    if not all_frames:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    data = pd.concat(all_frames, ignore_index=True)

    for col in ['RUN', 'DV', 'ESTABLECIMIENTO', 'SECTOR PACIENTE', 'PRESION ARTERIAL', 'FECHA ATENCION']:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip()

    data['RUT'] = data['RUN'].astype(str).str.strip() + "-" + data['DV'].astype(str).str.strip()

    presion_split = data['PRESION ARTERIAL'].str.split('/', n=1, expand=True)
    data['PAS'] = pd.to_numeric(presion_split[0], errors='coerce')
    data['PAD'] = pd.to_numeric(presion_split[1], errors='coerce')

    data['FECHA ATENCION'] = pd.to_datetime(data['FECHA ATENCION'], errors='coerce', dayfirst=True)

    data = data.dropna(subset=['PAS', 'PAD', 'FECHA ATENCION', 'RUT'])

    grouped = data.groupby(
        ['RUT', 'FECHA ATENCION', 'ESTABLECIMIENTO', 'SECTOR PACIENTE'],
        as_index=False
    ).agg({
        'PAS': 'max',
        'PAD': 'max'
    })

    condiciones = [
        (grouped['PAS'] >= 180) | (grouped['PAD'] >= 110),
        (grouped['PAS'] >= 160) | (grouped['PAD'] >= 100),
        (grouped['PAS'] >= 140) | (grouped['PAD'] >= 90),
    ]
    opciones = ['Criterio 1: >=180/110', 'Criterio 2: >=160/100', 'Criterio 3: >=140/90']
    grouped['Alerta'] = np.select(condiciones, opciones, default='Sin alerta')

    grouped['Fecha'] = grouped['FECHA ATENCION'].dt.strftime('%d-%m-%Y')
    grouped['FechaCarga'] = fecha_actual.strftime("%d-%m-%Y")
    grouped['Sector'] = grouped['SECTOR PACIENTE']
    grouped['CentroAtencion'] = grouped['ESTABLECIMIENTO'].apply(
        lambda est: ESTABLISHMENT_TO_SHEET.get(est, est)
    )
    grouped['AlertaN'] = grouped['Alerta'].map({
        'Criterio 1: >=180/110': 1,
        'Criterio 2: >=160/100': 2,
        'Criterio 3: >=140/90': 3,
        'Sin alerta': 0
    })

    grouped = grouped.sort_values(by=['AlertaN', 'PAS', 'PAD'], ascending=[False, False, False])

    columnas_salida = [
        'FechaCarga', 'CentroAtencion', 'Sector','NOMBRE','PRIMER APELLIDO','SEGUNDO APELLIDO','RUT', 'Fecha', 'PAS', 'PAD', 'Alerta'
    ]
    return grouped[columnas_salida]


def main():
    downloaded_files = list_xlsx_files(download_dir)
    if not downloaded_files:
        print("No se encontraron archivos de presión arterial generados por Urgencia_newIris.")
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

    consolidated = consolidate_pa(dfs_validas)

    total_escritos = 0
    for est, hoja in ESTABLISHMENT_TO_SHEET.items():
        block = consolidated[consolidated['CentroAtencion'] == hoja]
        if not block.empty:
            append_df_to_sheet(block, hoja)
            total_escritos += len(block)
            print(f"Agregados {len(block)} registros a hoja '{hoja}'")

    externos = consolidated[~consolidated['CentroAtencion'].isin(ESTABLISHMENT_TO_SHEET.values())]
    if not externos.empty:
        append_df_to_sheet(externos, 'Externos')
        total_escritos += len(externos)
        print(f"Agregados {len(externos)} registros a hoja 'Externos'")

    print(f"Proceso completado exitosamente. Registros escritos: {total_escritos}")


if __name__ == "__main__":
    main()
