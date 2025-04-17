import time
import random
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

def send_discord_notification(webhook_url, message):
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("Powiadomienie Discord wysłane.")
        else:
            print(f"Błąd przy wysyłaniu powiadomienia Discord, status code: {response.status_code}")
    except Exception as e:
        print("Błąd przy wysyłaniu powiadomienia Discord:", e)

def accept_cookies(driver, wait):
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Akceptuji') or contains(text(),'Akceptuję')]")))
        btn.click()
        print("Cookies zaakceptowane.")
    except TimeoutException:
        print("Nie znaleziono przycisku akceptacji cookies.")

def fill_and_submit_form(driver, wait):
    result = {"URL": driver.current_url, "Formularz": "Nie wysłany"}

    for field_id, value, name in [
        ("form-field-FirstName", "test", "FirstName"),
        ("form-field-LastName", "Testowy", "LastName"),
        ("form-field-email", "test@test.pl", "email"),
        ("form-field-field_9f38431", "999999999", "telefon"),
    ]:
        try:
            el = driver.find_element(By.ID, field_id)
            el.clear()
            el.send_keys(value)
            print(f"Pole '{name}' wypełnione.")
        except Exception:
            print(f"Nie znaleziono pola {name}.")

    try:
        cb = driver.find_element(By.ID, "form-field-field_43067ff")
        if not cb.is_selected():
            cb.click()
        print("Checkbox zaznaczony.")
    except Exception:
        print("Nie znaleziono checkboxa.")

    time.sleep(random.uniform(3, 8))

    try:
        submit = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Wyślij')]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", submit)
        time.sleep(1)
        try:
            submit.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", submit)
        print("Przycisk 'Wyślij' kliknięty.")
    except TimeoutException:
        print("Nie znaleziono przycisku 'Wyślij'.")

    try:
        WebDriverWait(driver, 30).until(
            lambda d: "podziękowanie" in d.current_url.lower())
        print("Podziękowanie – formularz wysłany.")
        result["Formularz"] = "Wysłany"
    except TimeoutException:
        print("Brak przekierowania do strony podziękowania:", driver.current_url)

    try:
        logs = driver.get_log("browser")
    except Exception:
        logs = []
    serious = [log["message"] for log in logs if log["level"] == "SEVERE"]
    if any("404" in log["message"] for log in logs):
        result["Error"] = "BŁĄD 404"
    if serious:
        print("Poważne błędy w konsoli:")
        for e in serious:
            print(e)
    else:
        print("Brak poważnych błędów w konsoli.")

    return result

def process_form(form_url):
    print("\nPrzetwarzanie:", form_url)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=chrome_options)
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
    try:
        df = pd.read_csv("landing.csv", header=None, names=["URL"])
        links = df["URL"].tolist()
        print(f"Wczytano {len(links)} linków.")
    except Exception as e:
        print("Błąd wczytywania CSV:", e)
        return

    webhook = "https://discord.com/api/webhooks/1350026426040057889/bA7k5h7e6SqyeD0O-ejicgMBZg918SOapcVTNP3WFcTRenab-BSxwIZ209oyy668_AHc"
    for link in links:
        res = process_form(link)
        if not res:
            continue
        if res.get("Error") == "BŁĄD 404":
            send_discord_notification(webhook, f"BŁĄD 404: {link}")
        elif res.get("Formularz") != "Wysłany":
            send_discord_notification(
                webhook,
                f"Formularz nie wysłany: {link}\nURL: {res['URL']}"
            )
        time.sleep(random.uniform(3, 8))

if __name__ == "__main__":
    main()
