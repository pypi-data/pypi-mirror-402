# La configuracion del webscraper: path_save_download, url page web, credentials
import time
from pathlib import Path

import pandas as pd

from chatbot.database.repositories.repository_alquiventas import QuerysChatbot as QuerysChatbotAlquiventas
from chatbot.database.repositories.repository_castillo import QuerysChatbot as QuerysChatbotCastillo
from chatbot.processing.tools import (
    add_business_hours,
    add_holiday,
    df_to_dicts,
    read_file_whatbonett,
)
from chatbot.webscraper.config_driver import CredentialsConfig
from chatbot.webscraper.customer_chrome_driver import ChromeDriver
from chatbot.webscraper.webscraping_chatbot import WebScrapingWhabonett


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
        candidates = [p for p in folder.glob("*.xls") if p.is_file() and not p.name.startswith("~$")]

        if candidates:
            latest = max(candidates, key=lambda p: p.stat().st_mtime)

            # lee
            print(f"{latest=}")
            df = read_file_whatbonett(latest._str)

            # elimina después de leer
            latest.unlink(missing_ok=True)

            return df

        time.sleep(poll)

    raise FileNotFoundError(f"No se encontró ningún .xlsx en {folder} dentro de {timeout}s")


def extract(inmobiliaria, date, path_save):
    load_credentials = CredentialsConfig(inmobiliaria)
    driver = ChromeDriver(path_save_download=path_save).create()
    WebScrapingWhabonett(driver, load_credentials, date).execute()

    df = read_and_delete_latest_xlsx(path_save, timeout=180)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # # Obtener Fecha
    # df.loc[:, "fecha"]= df["Creado"].apply(lambda x: str(x)[:19])
    # df.loc[:, "fecha"]= pd.to_datetime(df["fecha"])
    # df.loc[:, "fecha"]= df["fecha"].dt.date

    # # # Obtener Hora
    # df.loc[: ,"hora"]= df["Creado"].dt.hour

    # # Extraer y convertir a datetime
    # df["fecha"] = pd.to_datetime(df["Creado"].astype(str).str[:19])

    # # Extraer fecha y hora
    # df["hora"] = df["fecha"].dt.hour
    # df["fecha"] = df["fecha"].dt.date

    # df["creado_copy"] = pd.to_datetime(df["Creado"], errors="coerce")
    df["hora"] = df["Creado"].dt.hour
    df["fecha"] = df["Creado"].dt.date
    df["nombre_dia"] = df["Creado"].dt.day_name()

    # obtener dia de la semana
    # df.loc[:, "nombre_dia"] = df["Creado"].dt.day_name()
    df["nombre_dia"] = df["nombre_dia"].replace({"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo"})

    # Obtener minutos
    df.loc[:, "minutos"] = df["seg-Rpta(1)"].apply(lambda x: int(float(str(x).replace(",", "")) / 60))

    # llenamos valores faltantes del messageUser/opert_rpta
    df.loc[:, "Oper-Rpta(1)"] = df["Oper-Rpta(1)"].replace("", "NO REGISTRA")
    df.loc[:, "Oper-Rpta(1)"] = df["Oper-Rpta(1)"].fillna("NO REGISTRA")

    df = df[
        [
            "id",
            "Creado",
            "fecha",
            "hora",
            "nombre_dia",
            "Oper-Rpta(1)",
            "minutos",
        ]
    ]
    df.rename(
        columns={
            "Creado": "creado",
            "Oper-Rpta(1)": "oper_rpta",
        },
        inplace=True,
    )

    df = add_business_hours(df, "hora")
    df = add_holiday(df, "fecha")

    df.drop(columns=["id"], inplace=True)
    print(df.head())
    return df


def load(df: pd.DataFrame, inmobiliaria: str):
    # agregar limites de fechas

    # id                     int64
    # creado        datetime64[ns]
    # fecha         datetime64[ns]
    # hora                   int32
    # nombre_dia            object
    # oper_rpta             object
    # minutos                int64
    # hora_habil             int64
    # es_festivo              bool
    # dtype: object
    if inmobiliaria == "castillo":
        tool = QuerysChatbotCastillo()
        recods = df_to_dicts(df)
        tool.bulk_insert(recods)

    if inmobiliaria == "alquiventas":
        tool = QuerysChatbotAlquiventas()
        recods = df_to_dicts(df)
        tool.bulk_insert(recods)
