from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey

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


# class Citas(Base):
#     __tablename__ = "citas"
#     id_cita = Column(String(10), primary_key=True)
#     id_registro_asoc_cita = Column(String(10))
#     fecha_creacion_cita = Column(String(20))
#     tipo_cita = Column(String(50))
#     fecha_cita = Column(String(20))
#     duracion_cita = Column(String(10))
#     fecha_de_fin_cita = Column(String(20))
#     detalles = Column(Text)
#     resgistrado_por = Column(String(100))
#     direccion = Column(String(255))
#     barrio_sector = Column(String(100))
#     numero_llave = Column(String(10))
#     consecutivo_inmueble = Column(String(10))
#     asignado_a = Column(String(100))
#     estado = Column(String(50))
#     imagen = Column(String(50))
#     resultado_cita = Column(String(50))
#     comentario = Column(String(255))




# class CallLog(Base):
#     __tablename__ = "registro_calls"
#     id_registro = Column(String(20), primary_key=True, default=lambda: uuid.uuid4().hex[:8])# mannual: se genera automaticamente por appsheet, portales: consecutivo+telfono
#     fecha_contacto = Column(DateTime)
#     canal_contacto = Column(String(50))
#     nombre_asesor_call = Column(String(50))
#     nombre_asesor_interno = Column(String(50))
#     nombre_cliente = Column(String(50))
#     cedula = Column(String(15))
#     celular = Column(String(15))
#     correo = Column(String(50))
#     sector = Column(String(50))
#     presupuesto = Column(String(20))
#     comodidades = Column(Text)
#     estado_cliente = Column(String(20))
#     fecha_mudanza = Column(DateTime)
#     fecha_proximo_contacto = Column(DateTime)
#     codigo_inmueble = Column(String(10))
#     exhibicion_virtual = Column(String(10))
#     solicitud_libertator = Column(String(10))
#     estado_solicitud = Column(String(20))
#     asesor_externo = Column(String(50))
#     estado_final = Column(String(20))
#     motivo_retiro_cliente = Column(Text)
#     probabilidad_cierre = Column(String(10))
#     fecha_contrato = Column(DateTime)
#     cliente_contactar = Column(Boolean)
#     atencion_asesoría = Column(Boolean)
#     visita_presencial = Column(Boolean)
#     solicitud_estudio = Column(Boolean)
#     solicitud_aprobada = Column(Boolean)
#     orden_contrato = Column(Boolean)
#     inmueble_entregado = Column(Boolean)

#     news = relationship("RegisterNews", back_populates="call")





# class RegisterNews(Base):
#     __tablename__ = "registro_novedades"
#     id_novedades = Column(String(10), primary_key=True)
#     id_registro = Column(String(20), ForeignKey("registro_calls.id_registro"))
#     fecha_novedad = Column(DateTime)
#     tipo_novedad = Column(String(50))
#     detalles = Column(Text)
#     registrado_por = Column(String(50))
#     estado = Column(String(20))
#     proxima_fecha_segimiento = Column(DateTime)
#     asignado_a = Column(String(50))

#     call = relationship("CallLog", back_populates="news")




# class Interests(Base):
#     __tablename__ = "intereses"
#     id = Column(String(20), primary_key=True)  # consecutivo + telefono
#     celular = Column(String(15))  # foreign key de CallLog
#     codigo_inmueble = Column(String(10))
#     canal_contacto = Column(String(50))  # portal
#     fecha_contacto = Column(DateTime)

