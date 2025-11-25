# -*- coding: utf-8 -*-
"""
Procesa reportes respiratorios descargados previamente por Urgencia_newIris.
Filtra diagnósticos CIE10 respiratorios y envía los resultados a Google Sheets
segmentados por establecimiento.
"""

import os
from datetime import datetime, timedelta

import gspread
import numpy as np
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

fecha_actual = datetime.now()
fecha_ayer = fecha_actual - timedelta(days=1)
fecha_tabla = fecha_ayer.strftime("%Y-%m-%d")

# --- Configuración del directorio de descargas (archivos generados por Urgencia_newIris) ---
download_dir = r"G:\Mi unidad\UrgenciaQ\Datos_newiris"
FILE_PREFIX = "Informe_de_Atenciones_por_Diagnostico_Urgencia_Web"

# --- Configuración de Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r'G:\Mi unidad\quantum-balm-400521-65b53594e910.json', scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Casos respiratorios red de urgencia 2025")

establishment_to_sector = {
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
worksheet_cache = {}


def get_worksheet(sheet_name):
    if sheet_name not in worksheet_cache:
        worksheet_cache[sheet_name] = spreadsheet.worksheet(sheet_name)
    return worksheet_cache[sheet_name]


def append_df_to_sheet(df, sheet_name):
    worksheet = get_worksheet(sheet_name)
    rows = df.values.tolist()
    worksheet.append_rows(rows, value_input_option='USER_ENTERED')


def list_downloaded_reports(folder: str):
    reports = []
    for f in os.listdir(folder):
        if f.startswith(FILE_PREFIX) and f.lower().endswith('.xlsx') and not f.startswith('~$'):
            reports.append(os.path.join(folder, f))
    return reports


def main():
    downloaded_files = list_downloaded_reports(download_dir)
    if not downloaded_files:
        print("No se encontraron archivos respiratorios generados por Urgencia_newIris.")
        raise SystemExit

    cie10_prefixes = (
        'J09', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18',
        'J20', 'J21', 'J22', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J47'
    )

    dfs = []
    for file in downloaded_files:
        try:
            df = pd.read_excel(file, skiprows=8)
            dfs.append(df)
        except Exception as e:
            print(f"Error leyendo {file}: {str(e)}")

    if not dfs:
        print("No se encontraron archivos válidos para procesar")
        raise SystemExit

    df_combined = pd.concat(dfs, ignore_index=True)
    df_filtered = df_combined[df_combined['CIE10'].str.startswith(cie10_prefixes, na=False)].copy()

    df_filtered[['sistolica', 'diastolica']] = df_filtered['PRESION ARTERIAL'].str.split('/', expand=True)
    df_filtered['sistolica'] = pd.to_numeric(df_filtered['sistolica'], errors='coerce').fillna(0)
    df_filtered['diastolica'] = pd.to_numeric(df_filtered['diastolica'], errors='coerce')

    def handle_duplicates(group):
        if len(group) > 1 and (group['sistolica'] == 0).all():
            return group.drop_duplicates(subset=['CIE10'])
        return group

    df_filtered = df_filtered.groupby('ID', group_keys=False).apply(handle_duplicates).reset_index(drop=True)
    df_result = df_filtered.loc[df_filtered.groupby('ID')['sistolica'].idxmax()]

    df_result.replace([np.inf, -np.inf, np.nan], None, inplace=True)
    columns_to_keep = [
        'RUN', 'DV', 'NOMBRE', 'PRIMER APELLIDO', 'SEGUNDO APELLIDO',
        'SECTOR PACIENTE', 'ESTABLECIMIENTO', 'DIAGNOSTICO', 'CIE10',
        'FECHA ATENCION', 'PROFESIONAL RESPONSABLE', 'ULTIMA CATEGORIZACION',
        'SEXO', 'EDAD AÑOS'
    ]
    df_result = df_result[columns_to_keep]

    df_result = df_result.dropna(subset=['RUN'])
    df_result['RUN'] = df_result['RUN'].astype(int)
    df_result['RUT'] = df_result['RUN'].astype(str) + '-' + df_result['DV'].astype(str)
    df_result = df_result.drop(columns=['RUN', 'DV'])
    df_result['fecha'] = fecha_tabla

    columns_order = ['fecha', 'RUT'] + [col for col in columns_to_keep if col not in ['RUN', 'DV']]
    df_result = df_result[columns_order]

    for establishment, sector in establishment_to_sector.items():
        df_sector = df_result[df_result['ESTABLECIMIENTO'] == establishment]
        if not df_sector.empty:
            append_df_to_sheet(df_sector, sector)
            print(f"Datos agregados a {sector}")

    df_externos = df_result[~df_result['ESTABLECIMIENTO'].isin(establishment_to_sector.keys())]
    if not df_externos.empty:
        append_df_to_sheet(df_externos, 'Externos')

    for file in downloaded_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Archivo eliminado: {file}")

    print("Proceso completado exitosamente!")


if __name__ == "__main__":
    main()
