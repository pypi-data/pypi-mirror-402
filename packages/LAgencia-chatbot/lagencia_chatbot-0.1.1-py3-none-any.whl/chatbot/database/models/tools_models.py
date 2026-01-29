
class Tools:

    def to_dict(self):
        """Convierte el modelo en un diccionario."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def show_schema(self):
        schema= {column.name : column.type for column in self.__table__.columns}
        print(schema)
        return schema


