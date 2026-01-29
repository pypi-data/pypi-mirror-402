from typing import Union

import pandas as pd

from chatbot.chatbot_smarthome.api_smarthome import APISmartHome
from chatbot.database.models.models_livin import Chatbot as ChatbotLivin
from chatbot.database.models.models_villacruz import Chatbot as ChatbotVillacruz
from chatbot.database.repositories.repository_livin import QuerysChatbot as QuerysChatbotLivin
from chatbot.database.repositories.repository_villacruz import QuerysChatbot as QuerysChatbotVillacruz
from chatbot.processing.tools import add_business_hours, add_holiday, df_to_dicts

type_chatbot = Union[ChatbotVillacruz, ChatbotLivin]


def extract(inmobiliaria: str, date_start: str, date_end: str):
    api = APISmartHome(inmobiliaria)
    result = api.get_data(date_start, date_end)
    return result


def transform(chatbot: pd.DataFrame) -> pd.DataFrame:
    chatbot = chatbot.copy()

    if chatbot.empty:
        return chatbot

    s = chatbot["firstMessageDate"].astype("string").str.strip()

    chatbot["firstMessageDate"] = pd.to_datetime(s, format="ISO8601", errors="coerce").dt.floor("s")  # elimina milisegundos

    # obtener fecha
    chatbot.loc[:, "fecha"] = chatbot["firstMessageDate"].dt.date
    # obtener hora
    chatbot.loc[:, "hora"] = chatbot["firstMessageDate"].dt.hour
    # obtener dia de la semana
    chatbot.loc[:, "nombre_dia"] = chatbot["firstMessageDate"].dt.day_name()
    chatbot["nombre_dia"] = chatbot["nombre_dia"].replace({"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo"})

    # obtener minutos
    chatbot.loc[:, "minutos"] = chatbot["responseMinutes"].fillna(0)

    # llenamos valores faltantes del messageUser/opert_rpta
    chatbot.loc[:, "messageUser"] = chatbot["messageUser"].replace("", "NO REGISTRA")
    chatbot.loc[:, "messageUser"] = chatbot["messageUser"].fillna("NO REGISTRA")

    chatbot.rename(
        columns={"firstMessageDate": "creado", "messageUser": "oper_rpta"},
        inplace=True,
    )

    chatbot = chatbot[
        [
            # "id",
            "creado",
            "fecha",
            "hora",
            "nombre_dia",
            "oper_rpta",
            "minutos",
        ]
    ]

    chatbot = add_business_hours(chatbot, "hora")
    chatbot = add_holiday(chatbot, "fecha")

    return chatbot


def load_smarthome(data: pd.DataFrame, inmobiliaria: str):
    # agregar limites de fechas

    # creado        datetime64[ns]
    # fecha         datetime64[ns]
    # hora                   int32
    # nombre_dia            object
    # oper_rpta             object
    # minutos              float64
    # hora_habil             int64
    # es_festivo              bool
    # dtype: object
    if inmobiliaria == "livin":
        tool = QuerysChatbotLivin()
        recods = df_to_dicts(data)
        tool.bulk_insert(recods)

    if inmobiliaria == "villacruz":
        tool = QuerysChatbotVillacruz()
        recods = df_to_dicts(data)
        tool.bulk_insert(recods)
