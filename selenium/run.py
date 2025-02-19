import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import base64
import pytesseract


def extract_and_process_captcha(driver):
    try:
        captcha_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "image"))
        )
        src_attribute = captcha_element.get_attribute("src")
        print("Atributo src:", src_attribute)

        # Verificar si el atributo `src` está vacío
        if not src_attribute:
            # Intentar cambiar al iframe si existe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print("Cambiando al iframe...")
                driver.switch_to.frame(iframes[0])  # Cambiar al primer iframe
                captcha_element = driver.find_element(By.ID, "image")
                src_attribute = captcha_element.get_attribute("src")
                print("Atributo src dentro del iframe:", src_attribute)

            # Verificar nuevamente si el atributo `src` está vacío
            if not src_attribute:
                raise Exception("El atributo 'src' está vacío.")

        # Verificar si el atributo `src` tiene el formato esperado
        if "," not in src_attribute:
            raise Exception("El atributo 'src' no tiene el formato Base64 esperado.")

        # Extraer la parte Base64 del atributo `src`
        captcha_base64 = src_attribute.split(",")[1]

        # Decodificar la imagen Base64
        captcha_image = base64.b64decode(captcha_base64)

        # Convertir la imagen en un objeto de Pillow
        image = Image.open(BytesIO(captcha_image))

        # Mostrar la imagen (opcional)
        image.show()

        # Retornar la imagen para su uso posterior
        return image
    except Exception as e:
        print("Error al extraer o procesar el captcha:", e)
        raise Exception(f"Error procesando la imagen del captcha: {e}")


# Configurar el driver de Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

try:
    # Abrir la página
    driver.get("https://consultavehicular.sunarp.gob.pe/")

    # Extraer y procesar el captcha

    captcha_image = extract_and_process_captcha(driver)

    # Mostrar información del captcha procesado
    print("Captcha procesado correctamente.")

    captcha_text = pytesseract.image_to_string(captcha_image)
    print("Texto extraído del captcha:", captcha_text)

    # Mantener el navegador abierto por 30 segundos (opcional)
    time.sleep(30)

finally:
    # Cerrar el navegador
    driver.quit()
