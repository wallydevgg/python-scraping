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
import cv2
import numpy as np

# Configurar la ruta de Tesseract - AÑADIR ESTA LÍNEA AL INICIO
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image):
    """
    Preprocesa la imagen para mejorar el reconocimiento de texto.
    """
    # Convertir la imagen PIL a formato numpy array
    img_np = np.array(image)

    # Convertir a escala de grises
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Aplicar umbral adaptativo
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Eliminar ruido
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Aumentar contraste
    result = cv2.GaussianBlur(opening, (3, 3), 0)

    return Image.fromarray(result)


def extract_and_process_captcha(driver, max_retries=3):
    """
    Extrae y procesa el captcha con reintentos y mejor manejo de errores.
    """
    for attempt in range(max_retries):
        try:
            # Esperar a que el elemento del captcha esté presente
            captcha_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "image"))
            )

            # Obtener el atributo src
            src_attribute = captcha_element.get_attribute("src")
            if not src_attribute:
                raise ValueError("El atributo 'src' está vacío")

            # Verificar formato Base64
            if "base64," not in src_attribute:
                raise ValueError("El atributo 'src' no contiene datos Base64")

            # Extraer y decodificar Base64
            captcha_base64 = src_attribute.split("base64,")[1]
            captcha_image = Image.open(BytesIO(base64.b64decode(captcha_base64)))

            # Preprocesar imagen
            processed_image = preprocess_image(captcha_image)

            # Configurar pytesseract para mejor reconocimiento
            custom_config = r"--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

            # Extraer texto
            captcha_text = pytesseract.image_to_string(
                processed_image, config=custom_config
            ).strip()

            if not captcha_text:
                raise ValueError("No se pudo extraer texto del captcha")

            return {
                "image": processed_image,
                "text": captcha_text,
                "original_image": captcha_image,
            }

        except Exception as e:
            print(f"Intento {attempt + 1} fallido: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Error después de {max_retries} intentos: {str(e)}")
            time.sleep(2)  # Esperar antes de reintentar


def main():
    driver = None
    try:
        # Configurar opciones de Chrome
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")

        # Inicializar el driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

        # Abrir la página
        driver.get("https://consultavehicular.sunarp.gob.pe/")

        # Procesar el captcha
        result = extract_and_process_captcha(driver)

        # Mostrar resultados
        print("Texto extraído del captcha:", result["text"])
        result["processed_image"].show()  # Mostrar imagen procesada

    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
    finally:
        if driver:
            driver.quit()

    return {
        "image": None,
        "text": "",
        "original_image": None,
    }


if __name__ == "__main__":
    main()
