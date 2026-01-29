from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, inspect
from sqlalchemy import Column, Integer, BigInteger, Text, Float

from .tools_models import Tools

Base= declarative_base()


class Libertador(Base, Tools):
    __tablename__ = "libertador_estudio_digital"
    solicitud = Column(String(10), primary_key=True)
    fecha_radicacion = Column(DateTime)
    fecha_resultado = Column(DateTime)
    resultado = Column(String(30))
    destino = Column(String(30))
    tipo_persona = Column(String(30))
    ciudad = Column(String(30))
    direccion = Column(String(100))
    numero_inmobiliaria = Column(Integer)
    nombre_inquilino = Column(String(30))
    numero_inquilino = Column(String(50))
    nombre_asesor = Column(String(50))
    correo_asesor = Column(String(50))
    fecha_actualizacion= Column(DateTime)


class Telefonia(Base, Tools):
    __tablename__ = "cdr"
    id = Column(Integer, primary_key=True, autoincrement=True)
    caller = Column(String(20))
    dispo_name = Column(String(50))
    tiempo_completo = Column(String(10))
    tiempo_llamada = Column(String(10))
    extension = Column(String(20))
    fecha = Column(DateTime)
    hora = Column(String(10))
    tipo = Column(String(50))
    nombre = Column(String(100))
    grupo = Column(String(10))
    nivel = Column(String(10))
    transferida = Column(Integer)
    estado_general = Column(String(50))
    cod= Column(String(30))


class Chatbot(Base, Tools):
    __tablename__ = "ANS_atencion_chatbot"
    id = Column(Integer, primary_key= True, autoincrement= True)
    creado = Column(DateTime)
    fecha = Column(DateTime)
    hora = Column(Integer)
    nombre_dia = Column(String(30))
    oper_rpta = Column(String(100), nullable=True)
    minutos = Column(Integer)
    hora_habil = Column(Integer)
    es_festivo = Column(Boolean)


class Prospect(Base):
    __tablename__ = "prospectos"
    Id = Column(BigInteger, primary_key=True)
    CustomerId = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    ProspectId = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    Project = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    LocationSource = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    CreatedDate = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    CloseDate = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    Probability = Column(BigInteger, nullable=True)
    Stage = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    SaleCycle = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    Owner = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    ActivityStatus = Column(BigInteger, nullable=True)
    DigitalRecords = Column(BigInteger, nullable=True)
    Sex = Column(Text(collation="utf8mb3_unicode_ci"), nullable=True)
    CustomerType = Column(Float, nullable=True)
    City = Column(Float, nullable=True)
    Country = Column(Float, nullable=True)
    Campaign = Column(Float, nullable=True)
    DifferenceActionDate = Column(BigInteger, nullable=True)
