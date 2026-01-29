from selenium.webdriver import Chrome, ChromeOptions
import os

# configuracion e iniciacializacion del Chroome Driver


os.environ["XDG_CACHE_HOME"] = os.path.join(os.getcwd(), ".cache", "selenium")


class ChromeDriver:

    def __init__(self, path_save_download: str= None):
        self.path_save_download = path_save_download
        self.BACKGROUND_MODE = True  # !True: ejecucion en segundo plano
        print("Variables instanciadas")
        print(f"{self.path_save_download=}")
        print(f"{self.BACKGROUND_MODE=}")
        print()

    def create(self) -> Chrome:
        chrome_options = ChromeOptions()

        config_prefs = {
            "download.default_directory": self.path_save_download,  # Directorio de descargas
            "download.prompt_for_download": False,  # Desactivar el diálogo de descarga
            "download.directory_upgrade": True,  # Permitir que las descargas se realicen en el directorio especificado
            "safebrowsing.enabled": True,  # Activar la comprobación de seguridad
        }

        chrome_options.add_experimental_option(
            "prefs",
            config_prefs,
        )
        if self.BACKGROUND_MODE:
            # opciones de Chrome para ejecutar en segundo plano
            chrome_options.add_argument(
                "--headless"
            )  # debe ser activado por linea de comandos
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        return Chrome(options=chrome_options)
