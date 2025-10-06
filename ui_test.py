from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ⚡ webdriver-manager administra de forma automáticamente el ChromeDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

try:
    # Lleva a la página de login
    driver.get("http://127.0.0.1:5000/login")
    print("✅ Página de login cargada")

    # Se completa el formulario de login con usuario de prueba
    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")
    user_input.send_keys("admin")
    pass_input.send_keys("123456")
    pass_input.send_keys(Keys.ENTER)
    print("✅ Login enviado")

    # Se corrobora que estamos en el panel
    
    assert "Panel" in driver.title or "Inventario" in driver.page_source
    print("✅ Login exitoso y panel cargado")

finally:
    driver.quit()
    print("🚪 Navegador cerrado")
