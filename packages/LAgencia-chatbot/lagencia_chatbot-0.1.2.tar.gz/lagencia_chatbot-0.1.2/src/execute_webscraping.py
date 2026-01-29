from chatbot.webscraper.config_driver import CredentialsConfig
from chatbot.webscraper.customer_chrome_driver import ChromeDriver
from chatbot.webscraper.webscraping_chatbot import WebScrapingWhabonett
from chatbot.processing.tools import (
    delete_files_from_folder,
    read_file_whatbonett,
)
# La configuracion del webscraper: path_save_download, url page web, credentials




#from __future__ import annotations

import time
from pathlib import Path
import pandas as pd


def read_and_delete_latest_xlsx(
    folder_path: str | Path,
    *,
    timeout: int = 120,
    poll: float = 0.5,
    read_excel_kwargs: dict | None = None,
) -> pd.DataFrame:
    """
    Localiza el .xlsx más reciente dentro de folder_path, lo lee con pandas,
    elimina el archivo y retorna el DataFrame.

    - Espera hasta `timeout` segundos a que exista un .xlsx y no haya archivos temporales de descarga.
    - Ignora archivos temporales de Office: '~$*.xlsx'
    - Ignora descargas en progreso: '*.crdownload'

    Args:
        folder_path: Ruta del directorio donde se descargó el Excel.
        timeout: Segundos máximos de espera.
        poll: Intervalo de sondeo en segundos.
        read_excel_kwargs: kwargs extra para pd.read_excel (sheet_name, dtype, etc.)

    Returns:
        pd.DataFrame

    Raises:
        FileNotFoundError: Si no aparece ningún .xlsx en el tiempo dado.
    """
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"El folder no existe o no es directorio: {folder}")

    read_excel_kwargs = read_excel_kwargs or {}

    end = time.time() + timeout
    while time.time() < end:
        # si hay descargas en progreso, espera
        if any(folder.glob("*.crdownload")):
            print("***")
            time.sleep(poll)
            continue

        # archivos .xlsx válidos (excluye temporales de Excel)
        candidates = [
            p for p in folder.glob("*.xls")
            if p.is_file() and not p.name.startswith("~$")
        ]

        if candidates:
            latest = max(candidates, key=lambda p: p.stat().st_mtime)

            # lee
            df = read_file_whatbonett(latest._str)

            # elimina después de leer
            latest.unlink(missing_ok=True)

            return df

        time.sleep(poll)

    raise FileNotFoundError(f"No se encontró ningún .xlsx en {folder} dentro de {timeout}s")



def execute_webscraping(inmobiliaria, date, path_save):
    load_credentials = CredentialsConfig(inmobiliaria)
    driver = ChromeDriver(path_save_download= path_save).create()
    WebScrapingWhabonett(driver, load_credentials, date).execute()


    df = read_and_delete_latest_xlsx(
        path_save,
        timeout=180,

    )
    return df



if __name__ == "__main__":
    inmobiliaria = "alquiventas"
    date = "2026-01-15"

    execute_webscraping(inmobiliaria, date, r"C:\Users\Pc\Desktop\proyectos\pr\chatbot")

    df = read_and_delete_latest_xlsx(
        r"C:\Users\Pc\Desktop\proyectos\pr\chatbot",
        timeout=180,
        #read_excel_kwargs={"export-2026-01-19_07_33_20": 0}
    )
    print(df.head())
