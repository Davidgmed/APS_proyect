import sys
from datetime import date, timedelta

from selenium.webdriver.support.ui import WebDriverWait

import Atenciones_HGT
import Atenciones_PA
import Atenciones_respiratorias
import Urgencia_newIris


def calcular_rango_semana_anterior():
    hoy = date.today()
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    fecha_inicio = lunes_actual - timedelta(days=7)
    fecha_fin = fecha_inicio + timedelta(days=6)
    return fecha_inicio.strftime("%d/%m/%Y"), fecha_fin.strftime("%d/%m/%Y")


def main():
    if len(sys.argv) == 3:
        fecha_inicio, fecha_fin = sys.argv[1], sys.argv[2]
    else:
        fecha_inicio, fecha_fin = calcular_rango_semana_anterior()

    print(f"📅 Fecha inicio: {fecha_inicio}")
    print(f"📅 Fecha fin: {fecha_fin}")

    driver = Urgencia_newIris.create_driver()
    wait = WebDriverWait(driver, 150)

    try:
        Urgencia_newIris.login(driver, wait, Urgencia_newIris.USERNAME, Urgencia_newIris.PASSWORD)
        Urgencia_newIris.download_reports(driver, wait, fecha_inicio, fecha_fin)
    finally:
        driver.quit()

    print("Procesando reportes descargados...")
    #Atenciones_HGT.main()
    #Atenciones_PA.main()
    #Atenciones_respiratorias.main()


if __name__ == "__main__":
    main()
