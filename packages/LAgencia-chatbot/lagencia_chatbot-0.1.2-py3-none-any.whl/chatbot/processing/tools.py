import os
from pathlib import Path
import re

import numpy as np
import pandas as pd
from workalendar.america import Colombia


# def read_file_whatbonett(path: str) -> pd.DataFrame:
#     if not os.path.join(path):
#         raise FileNotFoundError(f"No se encontro: {path}")
#     if path.endswith("xlsx") or path.endswith("xls") or path.endswith("csv"):
#         data = pd.read_csv(path, encoding="utf-16", delimiter="\t", parse_dates=["Creado"])

#     data["Creado"] = pd.to_datetime(data["Creado"], dayfirst=True)

#     return data



def read_file_whatbonett(path: str) -> pd.DataFrame:
    p = Path(path).expanduser().resolve()

    if not p.exists():
        raise FileNotFoundError(f"No se encontro: {p}")

    ext = p.suffix.lower()

    # Detecta si es un xlsx REAL (xlsx es un zip que empieza con PK)
    is_real_xlsx = False
    if ext == ".xlsx":
        with open(p, "rb") as f:
            is_real_xlsx = (f.read(2) == b"PK")

    if ext == ".xlsx" and is_real_xlsx:
        df = pd.read_excel(p)

    elif ext in (".xls", ".xlsx", ".csv", ".tsv", ".txt"):
        # Export típico de sistemas: UTF-16 + tabs
        # engine="python" evita muchos errores del parser C
        df = pd.read_csv(
            p,
            encoding="utf-16",
            sep="\t",
            engine="python",
            on_bad_lines="skip",  # si quieres NO perder filas, dime y lo cambiamos
        )

    else:
        raise ValueError(f"Extensión no soportada: {ext}")

    if "Creado" in df.columns:
        df["Creado"] = pd.to_datetime(df["Creado"], dayfirst=True, errors="coerce")

    return df






def formater_dates(time_string: str) -> str:
    return re.sub(r"T|\.\d+", lambda x: " " if x.group(0) == "T" else "", time_string)


def read_file_samarthome_livin(path: str) -> pd.DataFrame:
    if not os.path.join(path):
        raise FileNotFoundError(f"No se encontro: {path}")
    if path.endswith("xlsx") or path.endswith("xls"):
        data = pd.read_excel(path)
        data.loc[:, "firstMessageDate"] = data["firstMessageDate"].apply(lambda x: formater_dates(str(x)))
        data["firstMessageDate"] = pd.to_datetime(data["firstMessageDate"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        data = data.infer_objects()
        return data
    print(f"No existe el archivo: {path}")
    raise FileNotFoundError(f"No existe el archivo: {path}")


def read_file_samarthome_villacruz(path: str) -> pd.DataFrame:
    if not os.path.join(path):
        raise FileNotFoundError(f"No se encontro: {path}")
    if path.endswith("xlsx") or path.endswith("xls"):
        data = pd.read_excel(path, parse_dates=["firstMessageDate"])
        print(data["firstMessageDate"])
        data.loc[:, "firstMessageDate"] = data["firstMessageDate"].apply(lambda x: formater_dates(str(x)))
        data["firstMessageDate"] = pd.to_datetime(data["firstMessageDate"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        data = data.infer_objects()
        return data
    print(f"No existe el archivo: {path}")
    raise FileNotFoundError(f"No existe el archivo: {path}")


def add_business_hours(df: pd.DataFrame, column_hora) -> pd.DataFrame:
    df = df.copy()
    df.loc[:, "hora_habil"] = df[column_hora].apply(lambda x: 1 if (7 < x < 17 and x != 12) else 0)

    # horas habiles Lunes-Domingo
    df.loc[:, "hora_habil"] = df[column_hora].apply(lambda x: 1 if (7 < x < 17 and x != 12) else 0)
    # obtener horario habil sabados
    index = df[(df["nombre_dia"] == "Sabado") & (df[column_hora] > 11)].index
    df.loc[index, "hora_habil"] = 0
    index = df[(df["nombre_dia"] == "Sabado") & (df[column_hora] < 8)].index
    df.loc[index, "hora_habil"] = 0

    index = df[(df["nombre_dia"] == "Domingo")].index
    df.loc[index, "hora_habil"] = 0

    return df


def add_holiday(df: pd.DataFrame, column_fecha: str) -> pd.DataFrame:
    df = df.copy()
    # Crear una instancia del calendario para Colombia
    cal = Colombia()

    # df[column_fecha] = pd.to_datetime(df[column_fecha])

    # Verificar si una fecha es un día festivo en Colombia
    # df.loc[:, "es_festivo"] = df[column_fecha].apply(lambda x: cal.is_holiday(x))

    df[column_fecha] = pd.to_datetime(df[column_fecha], errors="coerce")
    df["es_festivo"] = df[column_fecha].apply(lambda x: cal.is_holiday(x) if pd.notnull(x) else False)

    return df


def week_of_month(dt) -> int:
    first_day = dt.replace(day=1)
    dom = dt.day
    adjusted_dom = dom + first_day.weekday()
    return int(np.ceil(adjusted_dom / 7.0))


from typing import Dict, List

import pandas as pd


def df_to_dicts(df: pd.DataFrame) -> List[Dict]:
    """Convierte un DataFrame en una lista de diccionarios"""

    df = df.replace("", None).copy()
    df = df.replace(np.nan, None).copy()
    df = df.replace(pd.NaT, None).copy()
    df = df.replace("NaT", None).copy()
    df = df.replace("nan", None).copy()
    records = df.to_dict("records")
    return records


def list_obj_to_df(records: List[Dict]) -> pd.DataFrame:
    """Convierte una lista de objetos en un DataFrame"""

    if len(records) == 0:
        return pd.DataFrame()

    rows = []
    for row in records:
        dict_ = vars(row)
        del dict_["_sa_instance_state"]
        rows.append(dict_)

    return pd.DataFrame(rows)


def delete_files_from_folder(path):
    """
    Elimina archivos .xls, .xlsx y .csv dentro de la carpeta especificada.
    """
    if not os.path.exists(path):
        print(f"La carpeta '{path}' no existe.")
        return

    if not os.path.isdir(path):
        print(f"'{path}' no es un directorio válido.")
        return

    for item in os.listdir(path):
        path_file = os.path.join(path, item)

        if os.path.isfile(path_file) and item.lower().endswith((".xls", ".xlsx", ".csv")):
            try:
                os.remove(path_file)
                print(f"Archivo eliminado: {path_file}")
            except Exception as e:
                print(f"Error al eliminar '{path_file}': {e}")
        else:
            print(f"Omitiendo: {path_file}")
