import os

from config_db import ConfigDB

from models.models_alquiventas import Base as base_alquiventas
from models.models_villacruz import Base as base_villacruz
from models.models_castillo import Base as base_castillo
from models.models_livin import Base as base_livin
from connections import URI_CONNECTION_DB_VILLACRUZ, URI_CONNECTION_DB_CASTILLO, URI_CONNECTION_DB_ALQUIVENTAS,URI_CONNECTION_DB_LIVIN



engine_villacruz= ConfigDB(url=URI_CONNECTION_DB_VILLACRUZ).engine
engine_castillo= ConfigDB(url=URI_CONNECTION_DB_CASTILLO).engine
engine_alquiventas= ConfigDB(url= URI_CONNECTION_DB_ALQUIVENTAS).engine
engine_livin= ConfigDB(url=URI_CONNECTION_DB_LIVIN).engine

base_villacruz.metadata.create_all(engine_villacruz)
base_castillo.metadata.create_all(engine_castillo)
base_alquiventas.metadata.create_all(engine_alquiventas)
base_livin.metadata.create_all(engine_livin)