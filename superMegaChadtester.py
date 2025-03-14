import time
import random
import pandas as pd
import requests
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def send_discord_notification(webhook_url, message):
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        # Discord zwraca status 204 przy poprawnym wysłaniu wiadomości
        if response.status_code == 204:
            print("Powiadomienie Discord wysłane.")
        else:
            print(f"Błąd przy wysyłaniu powiadomienia Discord, status code: {response.status_code}")
    except Exception as e:
        print("Błąd przy wysyłaniu powiadomienia Discord:", e)

def accept_cookies(driver, wait):
    try:
        accept_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Akceptuji') or contains(text(),'Akceptuję')]")))
        accept_button.click()
        print("Cookies zaakceptowane.")
    except TimeoutException:
        print("Nie znaleziono przycisku akceptacji cookies.")

def fill_and_submit_form(driver, wait):
    result = {"URL": driver.current_url, "Formularz": "Nie wysłany"}
    
    try:
        first_name = driver.find_element(By.ID, "form-field-FirstName")
        first_name.clear()
        first_name.send_keys("test")
        print("Pole 'form-field-FirstName' wypełnione.")
    except Exception:
        print("Pole 'form-field-FirstName' nie znalezione.")
    
    try:
        last_name = driver.find_element(By.ID, "form-field-LastName")
        last_name.clear()
        last_name.send_keys("Testowy")
        print("Pole 'form-field-LastName' wypełnione.")
    except Exception:
        print("Pole 'form-field-LastName' nie znalezione.")
    
    try:
        email_field = driver.find_element(By.ID, "form-field-email")
        email_field.clear()
        email_field.send_keys("test@test.pl")
        print("Pole 'form-field-email' wypełnione.")
    except Exception:
        print("Pole 'form-field-email' nie znalezione.")
    
    try:
        phone_field = driver.find_element(By.ID, "form-field-field_9f38431")
        phone_field.clear()
        phone_field.send_keys("999999999")
        print("Pole 'form-field-field_9f38431' wypełnione.")
    except Exception:
        print("Pole 'form-field-field_9f38431' nie znalezione.")
    
    try:
        checkbox = driver.find_element(By.ID, "form-field-field_43067ff")
        if not checkbox.is_selected():
            checkbox.click()
        print("Checkbox 'form-field-field_43067ff' zaznaczony.")
    except Exception:
        print("Checkbox 'form-field-field_43067ff' nie znaleziony.")
    
    time.sleep(random.uniform(3, 8))
    
    try:
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Wyślij')]")))
        submit_button.click()
        print("Przycisk 'Wyślij' kliknięty.")
    except TimeoutException:
        print("Nie znaleziono przycisku 'Wyślij'.")
    
    try:
        WebDriverWait(driver, 30).until(lambda d: "podziękowanie" in d.current_url.lower())
        print("Przekierowano do strony podziękowania. Formularz wysłany.")
        result["Formularz"] = "Wysłany"
    except TimeoutException:
        print("Brak przekierowania do strony podziękowania w ciągu 30 sekund. Aktualny URL:", driver.current_url)
    
    try:
        logs = driver.get_log("browser")
    except Exception as e:
        logs = []
        print("Błąd przy pobieraniu logów przeglądarki:", e)
    
    serious_errors = []
    error_404 = False
    for log in logs:
        msg = log["message"]
        if ("JQMIGRATE" in msg or "ERR_BLOCKED_BY_CLIENT" in msg or "ERR_QUIC_PROTOCOL_ERROR" in msg):
            continue
        if log["level"] == "SEVERE":
            serious_errors.append(msg)
        if "404" in msg:
            error_404 = True
    if error_404:
        result["Error"] = "BŁĄD 404"
    
    if serious_errors:
        print("Poważne błędy w konsoli:")
        for err in serious_errors:
            print(err)
    else:
        print("Brak poważnych błędów w konsoli.")
    
    return result

def process_form(form_url):
    print("\nPrzetwarzanie formularza:")
    print("Bazowy URL:", form_url)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get(form_url)
    wait = WebDriverWait(driver, 15)
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("Strona nie załadowała się poprawnie.")
        driver.quit()
        return {"URL": form_url, "Error": "BŁĄD 404"}
    
    accept_cookies(driver, wait)
    time.sleep(random.uniform(3, 8))
    
    result = fill_and_submit_form(driver, wait)
    print("Wynik:", result)
    driver.quit()
    return result

def main():
    file_path = "landing.csv"
    try:
        df = pd.read_csv(file_path, header=None, names=["URL"])
        links = df["URL"].tolist()
        print(f"Wczytano {len(links)} linków z pliku {file_path}")
    except Exception as e:
        print("Błąd przy wczytywaniu pliku CSV:", e)
        return
    
    discord_webhook_url = "https://discord.com/api/webhooks/1350026426040057889/bA7k5h7e6SqyeD0O-ejicgMBZg918SOapcVTNP3WFcTRenab-BSxwIZ209oyy668_AHc"
    
    for link in links:
        result = process_form(link)
        if result is None:
            continue
        if "Error" in result and result["Error"] == "BŁĄD 404":
            message = f"BŁĄD 404: Strona dla URL: {link} nie została załadowana."
            send_discord_notification(discord_webhook_url, message)
        elif result.get("Formularz") != "Wysłany":
            message = f"Formularz dla URL: {link} nie został wysłany.\nAktualny URL: {result['URL']}"
            send_discord_notification(discord_webhook_url, message)
        time.sleep(random.uniform(3, 8))

def job():
    main()
    exit()

# Harmonogram – uruchomienie codziennie o 15:00
schedule.every().day.at("11:10").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
