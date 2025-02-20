from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time


# Configuración del driver (en este caso se usa Chrome)
driver = webdriver.Chrome()  # Asegúrate de tener el ChromeDriver en tu PATH o especifica la ruta

# Navegar a la página
driver.get("https://iris.rayenaps.cl/")

# Crear un objeto WebDriverWait para esperar los elementos
wait = WebDriverWait(driver, 10)

# Esperar a que el campo de usuario esté presente, limpiar y enviar el valor
username_input = wait.until(EC.presence_of_element_located((By.ID, "mui-1")))
username_input.clear()
username_input.send_keys("14092485-7")

# Esperar a que el campo de contraseña esté presente, limpiar y enviar el valor
password_input = wait.until(EC.presence_of_element_located((By.ID, "mui-3")))
password_input.clear()
password_input.send_keys("Gonzalez.2025")

# Esperar a que el botón "Ingresar" sea clickeable y hacer click
ingresar_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Ingresar')]")))
ingresar_button.click()

# Esperar a que el botón "Seleccionar" sea clickeable y hacer clic
select_div = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='mui-component-select-licenseIdSelected' and contains(text(),'Seleccionar')]")
    )
)
select_div.click()

# Esperar a que aparezca el menú y seleccionar la opción "Centro de Salud Familiar Dra. Haydeé López Casoou S.S. Metropolitano Sur"
menu_item = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//li[@data-value='1141' and contains(.,'Centro de Salud Familiar Dra. Haydeé López Casoou S.S. Metropolitano Sur')]")
    )
)
menu_item.click()

# Esperar a que el botón "Confirmar" sea clickeable y hacer clic
confirmar_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Confirmar')]")
    )
)
confirmar_button.click()

time.sleep(10)

# Abrir una nueva pestaña con la URL directamente
driver.execute_script("window.open('https://www.iris-salud.cl/ReportPortal/sql/queryView.aspx?reportId=2318', '_blank');")

# Cambiar al nuevo controlador (la nueva pestaña)
driver.switch_to.window(driver.window_handles[-1])


# Esperar y completar la fecha en el campo con id "txt4"
fecha_inicio = wait.until(
    EC.presence_of_element_located((By.ID, "txt4"))
)
fecha_inicio.clear()
fecha_inicio.send_keys("03/02/2025")

# Esperar y completar la fecha en el campo con id "txt7"
fecha_fin = wait.until(
    EC.presence_of_element_located((By.ID, "txt7"))
)
fecha_fin.clear()
fecha_fin.send_keys("09/03/2025")

# Escapar de los day picker
driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)


# Esperar a que el elemento select esté presente
select_element = wait.until(
    EC.presence_of_element_located((By.NAME, "txt10"))
)

# Crear un objeto Select a partir del elemento encontrado
select = Select(select_element)

# Seleccionar la opción con valor "72"
select.select_by_value("72")


# Esperar a que el elemento <select> esté presente
select_element_txt11 = wait.until(
    EC.presence_of_element_located((By.NAME, "txt11"))
)

# Crear el objeto Select a partir del elemento encontrado
select_txt11 = Select(select_element_txt11)

# Seleccionar la opción "Atenciones Cerradas" usando su valor ("2")
select_txt11.select_by_value("2")

# Esperar a que el botón de exportar esté presente
export_button = wait.until(EC.presence_of_element_located((By.ID, "tdShowExport")))

# Enviar Escape para cerrar overlays (por ejemplo, un datepicker abierto)
driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

# Hacer scroll hasta el botón
driver.execute_script("arguments[0].scrollIntoView(true);", export_button)

# Volver a esperar a que el botón sea clickeable
export_button = wait.until(EC.element_to_be_clickable((By.ID, "tdShowExport")))

# Forzar el clic usando JavaScript
driver.execute_script("arguments[0].click();", export_button)

# Esperar a que se muestre el menú de exportación y seleccionar la opción Excel
menu_item_excel = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@onclick, \"SelectExport('xls')\") and contains(., 'Excel')]")
    )
)
#menu_item_excel.click()


# Opcional: esperar unos segundos para ver el resultado o cerrar el navegador
time.sleep(200)
# driver.quit()

