import os
import time

from colorama import Fore, init
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from chatbot.webscraper.config_driver import CredentialsConfig
from chatbot.webscraper.customer_chrome_driver import ChromeDriver

init(autoreset=True)

# Ejecucion del webscraping


class WebScrapingWhabonett:
    def __init__(
        self,
        driver: ChromeDriver,
        credentials: CredentialsConfig,
        date: str,
    ):
        self.driver = driver
        self.credentials = credentials
        self.fecha = date

    def sing_in(self):
        url = self.credentials.URL_WHABONETT
        self.driver.get(url)

        TIMEOUT = 120
        try:
            XPATH_FORM_LOGIN = "/html/body/div/div/div/form"
            WebDriverWait(driver=self.driver, timeout=TIMEOUT).until(EC.visibility_of_element_located(locator=(By.XPATH, XPATH_FORM_LOGIN)))
        except Exception as ex:
            print(ex)

        else:
            password_whabonett = self.credentials.PASSWORD_WHABONETT
            user_whabonett = self.credentials.USER_WHABONETT
            XPATH_InputForEmail = '//*[@id="InputForEmail"]'
            XPATH_InputForPassword = '//*[@id="InputForPassword"]'
            XPATH_ButtonLogin = "/html/body/div/div/div/form/button"
            self.mBox = self.driver.find_element(By.XPATH, XPATH_InputForEmail)
            self.mBox.send_keys(user_whabonett)
            self.mBox = self.driver.find_element(By.XPATH, XPATH_InputForPassword)
            self.mBox.send_keys(password_whabonett)
            self.driver.find_element(By.XPATH, XPATH_ButtonLogin).click()

    def search_master_typing_report(self):
        url = self.credentials.ENDPINT_masterTipificacion
        self.driver.get(url)
        TIMEOUT = 120
        try:
            XPATH_TABLE_DATA = '//*[@id="gcrud-search-form"]/div[2]/table'
            WebDriverWait(driver=self.driver, timeout=TIMEOUT).until(EC.visibility_of_element_located(locator=(By.XPATH, XPATH_TABLE_DATA)))
        except Exception as e:
            print(e)

        else:
            XPATH_InputForDate = '//*[@id="gcrud-search-form"]/div[2]/table/thead/tr[2]/td[6]/input'
            column_creado = self.driver.find_element(
                By.XPATH,
                XPATH_InputForDate,
            )
            print("****fecha: ", self.fecha)
            column_creado.send_keys(self.fecha)

    def download_data(self):
        # self.clean_folder_download()

        # localizamos y pinchamos la opcion "descarga"
        XPATH_ButtonDownload = '//*[@id="gcrud-search-form"]/div[1]/div[1]/a[1]/span'
        self.driver.find_element(By.XPATH, XPATH_ButtonDownload).click()

        TIMEOUTH = 120
        start_time = time.time()
        # download_directory = self.credentials.path_save_download_whabonett

        time.sleep(30)

        # while True:
        #     if time.time() - start_time > TIMEOUTH:
        #         print("Tiempo de espera excedido. La descarga no se ha completado.")
        #         break

        #     new_files = os.listdir(download_directory)

        #     if new_files:
        #         new_files = new_files[0]
        #         pattern = r".*\.xls$"
        #         re.match(pattern, new_files)
        #         if re.match(pattern, new_files):
        #             print(
        #                 Fore.MAGENTA + "Se ha descargado un nuevo archivo:",
        #                 Fore.GREEN + new_files,
        #             )
        #             break
        #     else:
        #         print(Fore.YELLOW + "Esperando a que se complete la descarga...")
        #         time.sleep(1)  # Espera 1 segundo antes de volver a verificar
        time.sleep(1)
        self.driver.quit()

    def clean_folder_download(self):
        files = os.listdir(self.credentials.path_save_download_whabonett)
        if files:
            for file in files:
                os.remove(os.path.join(self.credentials.path_save_download_whabonett, file))

    def execute(self):
        print(Fore.CYAN + "* HACIENDO LOGING EN WHATBONETT")
        self.sing_in()
        print(Fore.CYAN + "* BUSCANDO REPORTE DE TIPIFICACIÓN MAESTRO")
        self.search_master_typing_report()
        print(Fore.CYAN + "* HACIENDO DOWNLOAD DE ARCHIVOS")
        self.download_data()
        print(Fore.CYAN + "* WEBSCRAPING COMPLETADO...")
