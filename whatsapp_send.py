from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

driver.get("https://web.whatsapp.com")
print("Scan QR Code...")
input("Press Enter after scanning QR...")

def close_popups():
    try:
        popups = driver.find_elements(By.XPATH, "//div[@role='dialog']")
        for p in popups:
            driver.execute_script("arguments[0].remove();", p)
    except:
        pass

def send_whatsapp(phone, message):
    try:
        driver.get(f"https://web.whatsapp.com/send/?phone={phone}")
        time.sleep(5)

        close_popups()
        time.sleep(1)

        # VERY IMPORTANT: Select ONLY the footer chat input, NOT search box
        msg_box = WebDriverWait(driver, 40).until(
            EC.presence_of_element_located(
                (By.XPATH, '//footer//div[@contenteditable="true"]')
            )
        )

        # Click message box safely
        driver.execute_script("arguments[0].focus();", msg_box)
        msg_box.click()

        close_popups()

        msg_box.send_keys(message)
        time.sleep(1)

        msg_box.send_keys(Keys.ENTER)
        time.sleep(5)
        print(f"Message sent successfully to {phone}")
        

    except Exception as e:
        print("ERROR:", e)

send_whatsapp("+918124003869", "Hello! Popup issue fixed. ✔️")
