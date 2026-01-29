import os
from datetime import datetime, timedelta
from typing import List, Union

import pandas as pd

from chatbot.chatbot_smarthome.etl_smarthome import (
    extract as extract_smarthome,
)
from chatbot.chatbot_smarthome.etl_smarthome import (
    load_smarthome,
)
from chatbot.chatbot_smarthome.etl_smarthome import (
    transform as transform_smarthome,
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


# #========================Config====================
# # * smarthome: Livin/villacruz
# # * whabonett: catillo/alquiventas

path_root = os.getcwd()
path_abs = os.path.join(path_root)


def extract_smarthome_livin():
    inmobiliaria = "livin"
    now = datetime.now().date()
    start_date = get_last_date_load(inmobiliaria)[0].fecha + timedelta(days=1)
    end_date = now - timedelta(days=1)

    if start_date > end_date:
        print("start_date es mayor que end_date")
        return

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    print(f"Ejecutando chatbot {inmobiliaria} para las fechas {start_date} - {end_date}")

    data = extract_smarthome(inmobiliaria, date_start=start_date, date_end=end_date)

    return data


def transform_smarthome_livin(data: pd.DataFrame):
    data_transform = transform_smarthome(data)
    return data_transform


def load_smarthome_livin(data: pd.DataFrame):
    inmobiliaria = "livin"
    load_smarthome(data, inmobiliaria)


def extract_smarthome_villacruz():
    inmobiliaria = "villacruz"
    now = datetime.now().date()
    start_date = get_last_date_load(inmobiliaria)[0].fecha + timedelta(days=1)
    end_date = now - timedelta(days=1)

    if start_date > end_date:
        print("start_date es mayor que end_date")
        return

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    print(f"Ejecutando chatbot {inmobiliaria} para las fechas {start_date} - {end_date}")

    data = extract_smarthome(inmobiliaria, date_start=start_date, date_end=end_date)

    return data


def transform_smarthome_villacruz(data: pd.DataFrame):
    data_transform = transform_smarthome(data)
    return data_transform


def load_smarthome_villacruz(data: pd.DataFrame):
    inmobiliaria = "villacruz"
    load_smarthome(data, inmobiliaria)


def execute_chatbot_smarthome_for_livin():
    data = extract_smarthome_livin()
    print(data)
    data_transform = transform_smarthome_livin(data)
    print(data_transform)
    load_smarthome_livin(data_transform)


def execute_chatbot_smarthome_for_villacruz():
    data = extract_smarthome_villacruz()
    print(data)
    data_transform = transform_smarthome_villacruz(data)
    print(data_transform)
    load_smarthome_villacruz(data_transform)


def main():
    execute_chatbot_smarthome_for_livin()
    execute_chatbot_smarthome_for_villacruz()


if __name__ == "__main__":
    main()
