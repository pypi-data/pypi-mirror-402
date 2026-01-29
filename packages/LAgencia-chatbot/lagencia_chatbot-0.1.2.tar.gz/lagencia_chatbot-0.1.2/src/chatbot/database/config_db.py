from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator, Any

# Nota:
# scoped_session : es un adminisrador de sessiones


class ConfigDB:

    def __init__(self, url: str, echo= False, pool_size= 5, max_overflow=5, pool_recycle=3600):
        self.engine= create_engine(
                    url,
                    echo= echo,
                    pool_size= pool_size,  # Número máximo de conexiones activas
                    max_overflow= max_overflow,  # Conexiones adicionales que se pueden crear temporalmente
                    pool_recycle= pool_recycle,  # Tiempo en segundos antes de reciclar una conexión
                    pool_pre_ping=True  # Añadido para verificar conexiones
                )

        session_factory= sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(session_factory)


    @contextmanager
    def get_session(self) -> Generator[scoped_session, Any, Any]:
        """Proporciona acceso a la sesión actual del hilo y garantiza su limpieza."""
        session = self.Session
        print(f"Session ID (in memory): {id(session)}")
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            # Solo cerramos la sesión, pero no hacemos remove() aquí
            # porque podría ser utilizada en otra parte del mismo hilo
            session.close()

    def remove_session(self):
        """Elimina la sesión asociada al hilo actual. Llamar al final del ciclo de vida."""
        self.Session.remove()

