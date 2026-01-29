from chatbot.database.models.models_livin import Libertador, Telefonia, Chatbot, Prospect
from chatbot.database.repositories.crud_base import BaseCRUD
from chatbot.database.config_db import ConfigDB
from chatbot.database.connections import URI_CONNECTION_DB_LIVIN


config_db= ConfigDB(url= URI_CONNECTION_DB_LIVIN)

class QuerysLibertador(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Libertador)


class QuerysTelefonia(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Telefonia)


class QuerysChatbot(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Chatbot)


class QuerysProspect(BaseCRUD):
    def __init__(self):
        super().__init__(config_db= config_db, model= Prospect)
