from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def seleccionar_opcion_menu(wait, opcion):
    """
    Espera a que la opción del menú sea clickable y la selecciona.

    :param wait: objeto WebDriverWait previamente configurado.
    :param opcion: diccionario con los datos de la opción, con claves:
                   - 'data_value': valor del atributo data-value.
                   - 'texto': parte del texto visible de la opción.
    """
    xpath = f"//li[@data-value='{opcion['data_value']}' and contains(.,'{opcion['texto']}')]"
    menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    menu_item.click()

# Listado de centros urgencia
urgencias = [
    {"data_value": "1149", "texto": "SAPU Dr. Carlos Lorca S.S. Metropolitano Sur"},
    {"data_value": "1145", "texto": "SAR Haydeé López Casoou S.S. Metropolitano Sur"},
    {"data_value": "1130", "texto": "SAPU Condores de Chile S.S. Metropolitano Sur"},
    {"data_value": "1130", "texto": "SAPU Santa Laura S.S. Metropolitano Sur"}
]

urgencias_simple = [
    {"nombre": "SAPU Dr. Carlos Lorca"},
    {"nombre": "SAR Haydeé López Casoou"},
    {"nombre": "SAPU Condores de Chile"},
    {"nombre": "SAPU Santa Laura"}
]



# Listado de centros atenciones
centros = [
    {"data_value": "1139", "texto": "Centro de Salud Familiar Santa Laura S.S. Metropolitano Sur"},
    {"data_value": "1140", "texto": "Centro Comunitario Salud Familiar Santa Laura S.S. Metropolitano Sur"},
    {"data_value": "1142", "texto": "Centro de Salud Familiar Mario Salcedo S.S. Metropolitano Sur"},
    {"data_value": "1165", "texto": "Centro de Salud Familiar Orlando Letelier S.S. Metropolitano Sur"},
    {"data_value": "1085", "texto": "Centro De Salud Familiar Cóndores De Chile S.S. Metropolitano Sur"},
    {"data_value": "1163", "texto": "Centro De Salud Familiar Dr. Carlos Lorca S.S. Metropolitano Sur"},
    {"data_value": "1141", "texto": "Centro de Salud Familiar Dra. Haydeé López Casoou S.S. Metropolitano Sur"},
    {"data_value": "1364", "texto": "Centro Comunitario de Salud Familiar Los Sauces S.S. Metropolitano Sur"},
]

# Listado de centros atenciones
otros = [
    {"data_value": "1147", "texto": "Centro Salud Adolescente S.S. Metropolitano Sur"},
    {"data_value": "1382", "texto": "Centro Especialidad el Bosque S.S. Metropolitano Sur"},
    {"data_value": "1084", "texto": "COSAM El Bosque S.S. Metropolitano Sur"},
    {"data_value": "1164", "texto": "Direccion de Salud Municipal S.S. Metropolitano Sur"},
]

# Ejemplo de uso: iterar sobre la lista de opciones
def recorrer_menu(wait, lista_opciones):
    for opcion in lista_opciones:
        try:
            seleccionar_opcion_menu(wait, opcion)
            # Aquí podrías incluir código adicional para procesar la opción seleccionada
            print(f"Opción '{opcion['texto']}' seleccionada.")
        except Exception as e:
            print(f"No se pudo seleccionar la opción '{opcion['texto']}': {e}")

# Ejemplo de configuración de WebDriverWait (suponiendo que ya tienes un driver configurado)
# from selenium import webdriver
# driver = webdriver.Chrome()
# wait = WebDriverWait(driver, 10)

# Luego, simplemente llamas a recorrer_menu(wait, opciones_menu)
