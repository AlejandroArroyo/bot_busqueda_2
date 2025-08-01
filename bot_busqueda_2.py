import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import sys

# Configuración Telegram
TOKEN = "7710527674:AAEwIs2sD8nJ2draX7KWu48J5sKXCfBqjv0"
CHAT_ID = "415471027"
PRODUCTO = ["RTX 5070 MSI TRIO OC"]
PRECIO_MAX = 600.0
FREAGMENTO = "TRIO OC"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    requests.post(url, data=data)

def buscar_productos():
    url = "https://www.pccomponentes.com/tarjetas-graficas/geforce-rtx-5070/grafica-nvidia/msi"

    # Configurar Chrome con opciones antidetención
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--1850,1200")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Evitar detección de webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        driver.get(url)

        # Aceptar cookies si aparece
        try:
            boton_cookies = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[id="cookiesAcceptAll"]'))
            )
            boton_cookies.click()
            print("✅ Cookies aceptadas correctamente.")
        except Exception as e:
            print(f"⚠️ No se pudo aceptar cookies: {e}")

        # Esperar a que se cargue al menos un producto
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(3)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="tarjeta-grafica"]'))
            )
            print("✅ Productos detectados.")
        except Exception as e:
            print(f"❌ No se detectaron productos: {e}")

        productos = driver.find_elements(By.CSS_SELECTOR, 'a[href*="tarjeta-grafica"]')
        resultados = []

        for producto in productos:
            try:
                titulo = producto.find_element(By.CSS_SELECTOR, "h3.product-card__title").text
                if FREAGMENTO.lower() not in titulo.lower():
                    continue 

                print(f"🔍 Título detectado: {titulo}")
                if any(p.lower() in titulo.lower() for p in PRODUCTO):
                    precio_txt = producto.find_element(By.CSS_SELECTOR, "span[data-e2e='price-card']").text
                    precio = float(precio_txt.replace("€", "").replace(".", "").replace(",", ".").strip())
                    enlace = producto.get_attribute("href")  # El propio <a> es el enlace
                    resultados.append((precio, titulo, enlace))
                    print(f"��� Producto detectado y agregado: {precio:.2f} ��� - {titulo}\n")
            except Exception as e:
                print(f"⚠️ Error procesando producto: {e}")
                continue

    except Exception as e:
        print(f"❌ Error general: {e}")
        resultados = []

    finally:
        driver.quit()

    resultados = [r for r in resultados if r[0] < PRECIO_MAX]
        
    resultados.sort(key=lambda x: x[0])

    # Enviar resultado por Telegram
    if resultados:
        top3 = resultados[:3]  # tomar las tres más baratas
        for precio, titulo, enlace in top3:
            mensaje = (
                f"🔍 {PRODUCTO}\n"
                f"🟢 Precio: {precio:.2f} €\n"
                f"📦 {titulo}\n"
                f"🔗 {enlace}"
            )
            enviar_telegram(f"⏰ {datetime.now():%d/%m %H:%M}\n{mensaje}")
            time.sleep(1)  # evitar enviar muy rápido
    else:
        enviar_telegram(f"⚠️ No se encontraron resultados válidos para {PRODUCTO}")

# Ejecutar
while True:
    ahora = datetime.now()
    if 7 <= ahora.hour <= 21:
        buscar_productos()
        print("⏰ Script ejecutado correctamente a las", ahora.strftime('%H:%M'))
        sys.exit(0)
    else:
        print(f"⌛ Esperando... {ahora.strftime('%H:%M')}")
    
    # Espera 60 segundos antes de volver a comprobar
    time.sleep(60)
