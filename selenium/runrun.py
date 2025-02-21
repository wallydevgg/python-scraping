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
import matplotlib.pyplot as plt

# Configurar la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image):
    """
    Preprocesa la imagen para mejorar el reconocimiento de texto en CAPTCHAs.
    Incluye más pasos de depuración visual.
    """
    # Convertir la imagen PIL a formato numpy array
    img_np = np.array(image)

    # Convertir a escala de grises si la imagen es RGB
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np

    # Mostrar imagen en escala de grises para depuración
    plt.figure(figsize=(15, 3))
    plt.subplot(1, 5, 1)
    plt.imshow(gray, cmap="gray")
    plt.title("Escala de Grises")
    plt.axis("off")

    # Mejora de contraste y brillo
    alpha = 1.5  # Contraste más alto
    beta = 10  # Brillo más alto
    contrasted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    plt.subplot(1, 5, 2)
    plt.imshow(contrasted, cmap="gray")
    plt.title("Contraste Mejorado")
    plt.axis("off")

    # Umbral adaptativo más flexible
    binary = cv2.adaptiveThreshold(
        contrasted,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15,  # Block size más pequeño para más detalle
        3,  # Constante más pequeña para preservar detalles
    )

    plt.subplot(1, 5, 3)
    plt.imshow(binary, cmap="gray")
    plt.title("Umbral Adaptativo")
    plt.axis("off")

    # Eliminar ruido pequeño
    kernel = np.ones((2, 2), np.uint8)
    denoised = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    plt.subplot(1, 5, 4)
    plt.imshow(denoised, cmap="gray")
    plt.title("Ruido Eliminado")
    plt.axis("off")

    # Suave dilatación para conectar componentes
    kernel_dilate = np.ones((2, 1), np.uint8)
    dilated = cv2.dilate(denoised, kernel_dilate, iterations=1)

    plt.subplot(1, 5, 5)
    plt.imshow(dilated, cmap="gray")
    plt.title("Dilatación")
    plt.axis("off")

    plt.tight_layout()
    plt.show()

    # Aumentar tamaño
    scale_factor = 3  # Factor más agresivo
    result = cv2.resize(
        dilated, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR
    )

    # Asegurar texto negro sobre fondo blanco
    mean_val = cv2.mean(result)[0]
    if mean_val > 127:
        result = cv2.bitwise_not(result)

    # Intentar rotar ligeramente la imagen (opcional)
    rows, cols = result.shape
    rotation_matrix = cv2.getRotationMatrix2D(
        (cols / 2, rows / 2), 5, 1
    )  # Rotar 5 grados
    result = cv2.warpAffine(result, rotation_matrix, (cols, rows))

    # Convertir el resultado de nuevo a formato PIL
    processed_image = Image.fromarray(result)
    return processed_image


def extract_and_process_captcha(driver, max_retries=3):
    """
    Extrae y procesa el captcha con reintentos y mejor manejo de errores.
    """
    for attempt in range(max_retries):
        try:
            # Esperar a que el elemento del captcha esté presente y tenga src
            captcha_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//img[@id='image' and @src]")
                )
            )

            # Obtener y depurar el atributo src
            src_attribute = captcha_element.get_attribute("src")
            print(f"Valor de src completo: {src_attribute}")
            if not src_attribute or "base64," not in src_attribute:
                raise ValueError("El atributo 'src' no es válido o no contiene Base64")

            # Extraer y decodificar Base64
            captcha_base64 = src_attribute.split("base64,")[1]
            captcha_image = Image.open(BytesIO(base64.b64decode(captcha_base64)))

            # Preprocesar imagen
            processed_image = preprocess_image(captcha_image)

            # Probar diferentes configuraciones de Tesseract
            configs = [
                r"--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- -c tessedit_certainty_threshold=95",
                r"--oem 1 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- -c tessedit_certainty_threshold=80",
                r"--oem 2 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
            ]

            captcha_text = None
            for config in configs:
                captcha_text = pytesseract.image_to_string(
                    processed_image, config=config
                ).strip()
                if captcha_text and len(captcha_text) > 0:
                    print(f"Texto extraído con config {config}: {captcha_text}")
                    break

            if not captcha_text:
                raise ValueError("No se pudo extraer texto del captcha")

            # Guardar imágenes para análisis manual
            processed_image.save(f"captcha_attempt_{attempt}_processed.png")
            captcha_image.save(f"captcha_attempt_{attempt}_original.png")

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
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Inicializar el driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

        # Abrir la página
        driver.get("https://consultavehicular.sunarp.gob.pe/")
        driver.implicitly_wait(5)

        # Procesar el captcha
        result = extract_and_process_captcha(driver)

        if not result["text"]:
            print(
                "No se pudo extraer el texto del CAPTCHA. Verifica la imagen procesada."
            )
            return

        print(f"Resultado final: Texto del Captcha: {result['text']}")

        # Interactuar con el formulario
        time.sleep(2)  # Esperar a que la página esté lista
        text_box_placa = driver.find_element(by=By.ID, value="nroPlaca")
        text_box_placa.send_keys("AUB042")

        text_box_captcha = driver.find_element(by=By.ID, value="codigoCaptcha")
        text_box_captcha.send_keys(result["text"])

        submit_button = driver.find_element(by=By.ID, value="submitButton")
        submit_button.click()

    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        return {
            "image": None,
            "text": "",
            "original_image": None,
        }
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
