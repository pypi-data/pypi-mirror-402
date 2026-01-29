from chatbot.database.models.models_alquiventas import Libertador, Telefonia, Chatbot
from chatbot.database.repositories.crud_base import BaseCRUD
from chatbot.database.config_db import ConfigDB
from chatbot.database.connections import URI_CONNECTION_DB_ALQUIVENTAS


config_db= ConfigDB(url= URI_CONNECTION_DB_ALQUIVENTAS)

class QuerysLibertador(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Libertador)


class QuerysTelefonia(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Telefonia)


class QuerysChatbot(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Chatbot)


