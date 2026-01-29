from datetime import datetime, timedelta
from typing import List, Union

import pandas as pd

from chatbot.chatbot_whatbonett.etl_whabonett import (
    extract as extract_whabonett,
)
from chatbot.chatbot_whatbonett.etl_whabonett import (
    load as load_whabonett,
)
from chatbot.chatbot_whatbonett.etl_whabonett import (
    transform as transform_whabonett,
)
from chatbot.database.models.models_alquiventas import Chatbot as ChatbotAlquiventas
from chatbot.database.models.models_castillo import Chatbot as ChatbotCastillo
from chatbot.database.models.models_livin import Chatbot as ChatbotLivin
from chatbot.database.models.models_villacruz import Chatbot as ChatbotVillacruz
from chatbot.database.repositories.repository_alquiventas import QuerysChatbot as QuerysChatbotAlquiventas
from chatbot.database.repositories.repository_castillo import QuerysChatbot as QuerysChatbotCastillo
from chatbot.database.repositories.repository_livin import QuerysChatbot as QuerysChatbotLivin
from chatbot.database.repositories.repository_villacruz import QuerysChatbot as QuerysChatbotVillacruz

type_chatbot = Union[ChatbotVillacruz, ChatbotLivin]


def get_last_date_load(name_real_state: str) -> List[type_chatbot]:
    records = []
    match name_real_state:
        case "villacruz":
            tool = QuerysChatbotVillacruz()
            records = tool.select_with_limit(ChatbotVillacruz.fecha, -1)

        case "livin":
            tool = QuerysChatbotLivin()
            records = tool.select_with_limit(ChatbotLivin.fecha, -1)

        case "castillo":
            tool = QuerysChatbotCastillo()
            records = tool.select_with_limit(ChatbotCastillo.fecha, -1)

        case "alquiventas":
            tool = QuerysChatbotAlquiventas()
            records = tool.select_with_limit(ChatbotAlquiventas.fecha, -1)

    return records


def extract_whabonett_castillo(path_save: str):
    inmobiliaria = "castillo"

    last_date = get_last_date_load(inmobiliaria)[0].fecha + timedelta(days=1)
    now = datetime.now().date()
    print(f"*** {last_date} - {now} ***")

    if last_date < now:
        date = last_date.strftime("%Y-%m-%d")

        print(f"Ejecutando chatbot {inmobiliaria} para la fecha {last_date}")

        data = extract_whabonett(inmobiliaria, "2026-01", path_save)

        return data


def transform_whabonett_castillo(data):
    data_transform = transform_whabonett(data)
    return data_transform


def load_whabonett_castillo(data):
    inmobiliaria = "castillo"

    load_whabonett(data, inmobiliaria)


# usa webscraping
def extract_whabonett_alquiventas(path_save: str):
    inmobiliaria = "alquiventas"

    last_date = get_last_date_load(inmobiliaria)[0].fecha + timedelta(days=1)
    now = datetime.now().date()
    print(f"*** {last_date} - {now} ***")

    if last_date < now:
        date = last_date.strftime("%Y-%m-%d")

        print(f"Ejecutando chatbot {inmobiliaria} para la fecha {last_date}")

        data = extract_whabonett(inmobiliaria, date, path_save)

        return data


def transform_whabonett_alquiventas(data: pd.DataFrame):
    data_transform = transform_whabonett(data)

    return data_transform


def load_whabonett_alquiventas(data: pd.DataFrame):
    load_whabonett(df=data, inmobiliaria="alquiventas")


def main():
    # path_save = r"C:\Users\Pc\Desktop\proyectos\pr\chatbot"
    # data = extract_whabonett_alquiventas(path_save)
    # data_transform = transform_whabonett_alquiventas(data)
    # load_whabonett_alquiventas(data_transform)

    path_save = r"C:\Users\Pc\Desktop\proyectos\pr\chatbot"
    data = extract_whabonett_castillo(path_save)
    data_transform = transform_whabonett_castillo(data)
    load_whabonett_castillo(data_transform)

    print(data_transform)


if __name__ == "__main__":
    main()
