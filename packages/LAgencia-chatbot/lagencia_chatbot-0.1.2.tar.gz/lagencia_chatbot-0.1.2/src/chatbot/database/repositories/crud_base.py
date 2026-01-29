from typing import Any, Dict, Generic, List, Type, TypeVar, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.sql.expression import delete, update
from sqlalchemy import desc, asc

from chatbot.database.config_db import ConfigDB



# Tipo genérico para los modelos
T = TypeVar("T")


class BaseCRUD(Generic[T]):

    def __init__(self, config_db: ConfigDB, model: Type[T]):
        self.config_db= config_db
        self.model= model

    def dict_to_obj(self, items: Union[Dict, List[Dict]]) -> Union[T, List[T]]:
        """Convierte diccionarios en instancias de modelo."""
        if isinstance(items, list):
            return [self.model(**item) for item in items]
        return self.model(**items)

    def insert(self, item: Union[Dict, T]) -> bool:
        """Inserta un único registro."""
        if isinstance(item, dict):
            item = self.dict_to_obj(item)

        with self.config_db.get_session() as session:
            try:
                session.add(item)
                session.commit()
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al insertar: {ex}")
                return False


    def insert_all(self, items: List[Union[Dict, T]]) -> bool:
        """Inserta múltiples registros (menos de 50)."""

        if len(items) == 0:
            print("No hay registros que insertar")
            return False

        if isinstance(items[0], dict):
            items = self.dict_to_obj(items)

        with self.config_db.get_session() as session:
            try:
                session.add_all(items)
                session.commit()
                print(f"Registros insertados: {len(items)}")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al insertar múltiples registros: {ex}")
                return False


    def bulk_insert(self, items: List[Union[Dict, T]]) -> bool:
        """Inserta grandes volúmenes de datos."""
        if len(items) == 0:
            print("No hay registros que insertar")
            return True
        count_records = len(items)
        if isinstance(items[0], dict):
            items = self.dict_to_obj(items)


        # Rango de 0 a 1,000 registros
        if 0 <= count_records < 1000:
            return self._bulk_save_objects(items)

        # Rango de 1,000 a 10,000 registros, en lotes de 500
        elif 1000 <= count_records < 10000000:  # +3 ceros
            return self._bulk_save_in_batches(items, batch_size=500)

        # Más de 10,000 registros
        else:
            print(
                "Para más de 10,000 registros, se recomienda usar técnicas avanzadas "
                "como COPY en PostgreSQL o LOAD DATA en MySQL."
            )
            return False


    def _bulk_save_objects(self, items: List[T]) -> bool:
        """Inserciones masivas de hasta 1,000 registros."""
        with self.config_db.get_session() as session:
            try:
                session.bulk_save_objects(items)
                session.commit()
                print("Inserción masiva realizada correctamente.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error en inserción masiva: {ex}")
                return False


    def _bulk_save_in_batches(self, items: List[T], batch_size: int) -> bool:
        """Inserciones en lotes para grandes volúmenes de datos."""
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            with self.config_db.get_session() as session:
                try:
                    session.bulk_save_objects(batch)
                    session.commit()
                    print(
                        f"Inserción de un lote de {len(batch)} registros"
                        "realizada correctamente."
                    )
                except SQLAlchemyError as ex:
                    session.rollback()
                    print(f"Error al insertar un lote: {ex}")
                    return False
        return True

    def select_all(self) -> List[T]:
        """Selecciona todos los registros del modelo."""
        with self.config_db.get_session() as session:
            try:
                stmt = select(self.model)
                return session.scalars(stmt).all()
            except SQLAlchemyError as ex:
                print(f"Error al seleccionar registros: {ex}")
                return []


    def select_by_filter(self, filter_condition: Any) -> List[T]:
        """Selecciona registros filtrados por una condición."""
        with self.config_db.get_session() as session:
            try:
                stmt = select(self.model).where(filter_condition)
                return session.scalars(stmt).all()
            except SQLAlchemyError as ex:
                print(f"Error al seleccionar con filtro: {ex}")
                return []


    def update_by_id(self, item_update: Union[Dict, T], item_id: int) -> bool:
        """Actualiza un registro por ID."""
        if isinstance(item_update, self.model):
            item_update = {
                k: v for k, v in vars(item_update).items() if not k.startswith("_")
            }

        with self.config_db.get_session() as session:
            try:
                obj = session.get(self.model, item_id)
                if not obj:
                    print("Registro no encontrado.")
                    return False

                for key, value in item_update.items():
                    setattr(obj, key, value)

                session.commit()
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al actualizar: {ex}")
                return False


    def update_all_by_ids(self, ids: List[int], update_data: Dict) -> bool:
        """
        Actualiza registros masivamente según una lista de IDs.

        Args:
            cls: Modelo de SQLAlchemy.
            ids (List[int]): Lista de IDs para filtrar.
            update_data (Dict): Diccionario con los campos y valores a actualizar.

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        with self.config_db.get_session() as session:
            try:
                # Construir la sentencia de actualización
                update_stmt = (
                    update(self.model)
                    .where(self.model.id.in_(ids))  # Condición WHERE id IN (values)
                    .values(**update_data)        # Valores a actualizar
                )
                result = session.execute(update_stmt)
                session.commit()
                print(f"Se actualizaron {result.rowcount} registros.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al actualizar registros: {ex}")
                return False

    def update_all_by_filter(self, filter_condition: Any, update_data: Dict) -> bool:
        """Actualiza registros masivamente según una condición."""
        with self.config_db.get_session() as session:
            try:
                update_stmt = (
                    update(self.model).where(filter_condition).values(**update_data)
                )
                result = session.execute(update_stmt)
                session.commit()
                print(f"Se actualizaron {result.rowcount} registros.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al actualizar registros: {ex}")
                return False


    def delete_by_id(self, item_id: int) -> bool:
        """Elimina un registro por ID."""
        with self.config_db.get_session() as session:
            try:
                obj = session.get(self.model, item_id)
                if not obj:
                    print("Registro no encontrado.")
                    return False

                session.delete(obj)
                session.commit()
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al eliminar: {ex}")
                return False


    def delete_by_filter(self, filter_condition: Any) -> bool:
        """Elimina registros según una condición."""
        with self.config_db.get_session() as session:
            try:
                stmt = delete(self.model).where(filter_condition)
                result = session.execute(stmt)
                session.commit()
                print(f"Se eliminaron {result.rowcount} registros.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al eliminar con filtro: {ex}")
                return False


    def delete_all(self) -> bool:
        """Elimina todos los registros de la tabla."""
        with self.config_db.get_session() as session:
            try:
                stmt = delete(self.model)
                result = session.execute(stmt)
                session.commit()
                print(f"Se eliminaron {result.rowcount} registros.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al eliminar todos los registros: {ex}")
                return False


    def upsert(self, item: Union[Dict, T]) -> bool:
        """
        Inserta o actualiza un registro. Si ya existe, se actualiza; si no, se inserta.
        Utiliza el método `merge` de SQLAlchemy.
        """
        if isinstance(item, dict):
            item = self.dict_to_obj(item)

        with self.config_db.get_session() as session:
            try:
                session.merge(item)
                session.commit()
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al realizar upsert: {ex}")
                return False

    def upsert_all(self, items: List[Union[Dict, T]]) -> bool:
        """
        Inserta o actualiza múltiples registros.
        Si ya existen, se actualizan; si no, se insertan.
        Utiliza el método `merge` de SQLAlchemy.
        """
        if len(items) == 0:
            print("No hay registros que insertar o actualizar")
            return True
        if isinstance(items[0], dict):  # Verifica si los elementos son diccionarios
            items = self.dict_to_obj(items)

        with self.config_db.get_session() as session:
            try:
                for item in items:
                    session.merge(item)  # Inserta o actualiza cada elemento
                session.commit()
                print(f"Se actualizaron {len(items)} elementos con upsert.")
                return True
            except SQLAlchemyError as ex:
                session.rollback()
                print(f"Error al realizar upsert_all: {ex}")
                return False


    def select_with_limit(self, order_by_field: Any= None, n: int= 1) -> List[T]:
        with self.config_db.get_session() as session:
            if n > 0:
                result= session.query(self.model).order_by(asc(order_by_field)).limit(n).all()
            elif n < 0:
                result= session.query(self.model).order_by(desc(order_by_field)).limit(abs(n)).all()

            elif n == 0:
                result= session.query(self.model).order_by(asc(order_by_field)).limit(1).all()

        return result if result else []
