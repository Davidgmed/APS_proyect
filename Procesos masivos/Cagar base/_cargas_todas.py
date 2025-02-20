import subprocess
import sys

scripts = [
    "Actividades_folder_bulk.py",
    "Admitidos_folder_bulk.py",
    "dm_folder_bulk2.py",
    "Ges_folder_bulk.py",
    "hba1c_folder_bulk.py",
    "hta_folder_bulk.py",
    "Policonsultantes_folder_bulk.py",
    "Tiempos_folder_bulk.py"
    #"sm_folder_bulk.py"
]

for script in scripts:
    print(f"Ejecutando {script}…")
    # Usa sys.executable para asegurar que empleas el mismo intérprete
    subprocess.run([sys.executable, script], check=True)

print("✅ Todos los scripts han terminado sin errores.")
