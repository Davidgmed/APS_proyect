import subprocess
import sys
from datetime import date, timedelta

hoy = date.today()
weekday = hoy.weekday()  # lunes=0, martes=1, ...

lunes_actual = hoy - timedelta(days=weekday)
fecha_inicio = lunes_actual - timedelta(days=7)
fecha_fin = fecha_inicio + timedelta(days=6)

fecha_inicio_str = fecha_inicio.strftime("%d/%m/%Y")
fecha_fin_str = fecha_fin.strftime("%d/%m/%Y")

print(f"📅 Fecha inicio: {fecha_inicio_str}")
print(f"📅 Fecha fin: {fecha_fin_str}")

scripts = [
    "login_unico.py",
    "Actividades_newIris.py",
    "Glicosiladas_newIris.py",
    #"Urgencia_newIris.py",
    "Urgencia_newIris_poli.py",
]

for script in scripts:
    print(f"🚀 Ejecutando {script}…")
    subprocess.run(
        [sys.executable, script, fecha_inicio_str, fecha_fin_str],
        check=True
    )

print("✅ Todos los scripts han terminado sin errores.")
