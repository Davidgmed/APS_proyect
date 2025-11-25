"""
Ejecuta los scripts de carga a Google Sheets para HGT, presión arterial y respiratorio.
Se asume que los reportes ya fueron descargados; este orquestador solo dispara
la carga/transformación hacia Google Sheets.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    #("Atenciones_HGT.py", "hemoglucotest"),
    ("Atenciones_PA.py", "presión arterial"),
    #("Atenciones_respiratorias.py", "casos respiratorios"),
]


def run_script(script_name: str, descripcion: str) -> None:
    base_dir = Path(__file__).resolve().parent
    script_path = base_dir / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"No se encontró el script {script_path}")

    print(f"Iniciando carga de {descripcion} con {script_path.name}...")
    subprocess.run([sys.executable, str(script_path)], check=True)
    print(f"Carga de {descripcion} finalizada.\n")


def main():
    for script_name, descripcion in SCRIPTS:
        run_script(script_name, descripcion)


if __name__ == "__main__":
    main()
