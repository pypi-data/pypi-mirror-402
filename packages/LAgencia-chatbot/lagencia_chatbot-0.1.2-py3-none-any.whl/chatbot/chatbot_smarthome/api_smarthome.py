import os

import pandas as pd
import requests

URL_VILLACRUZ = "http://manage.smart-home.com.co/api/bi/getMessageGroupRecords/OTcyN2U0ZTQtMjNmNy00MTkxLTllN2ItNGExY2MwYjM1NTQ1O2ZjZDAwYmY4LTQ0ZmUtNDAzZi04MTc2LTEzYmYzNjdkY2JjOTsyLzUvMjAyNA==/?"
URL_LIVIN = "http://manage.smart-home.com.co/api/bi/getMessageGroupRecords/Njk0OTAyMzMtOGQzYS00YWU3LTkzNDItNDIwMzIzODJlYmZiO2YyMzZmZmU0LTMwMzYtNGI0NS05MDU0LTJhNDU4OWQyYTRjNzsyLzI3LzIwMjQ=/?"


class APISmartHome:
    def __init__(self, inmobiliaria: str):
        # inmoobiliar: villacruz/livin
        # data_start/date_end: yyyy-mm-dd

        match inmobiliaria.lower():
            case "villacruz":
                # self.url = config("URL_MESSAGE_LIVIN")
                self.url = URL_VILLACRUZ
            case "livin":
                # self.url = config("URL_MESSAGE_LIVIN")
                self.url = URL_LIVIN

            case _:
                raise ValueError(f"APISmartHome: Error inmobiliaria={inmobiliaria} invalida")

    def get_data(self, date_start: str, date_end: str) -> pd.DataFrame:
        if not date_start or not date_end:
            print(f"APISmartHome: Error en fechas: date_start= {date_start}, date_end: {date_end}")
            raise ValueError(f"APISmartHome: Error en fechas: date_start= {date_start}, date_end: {date_end}")

        params = {"startDate": date_start, "endDate": date_end}
        response = requests.get(self.url, params=params)
        response.raise_for_status()
        self.data = pd.DataFrame(response.json()["records"])
        return self.data

    def save_data(self, path: str):
        if not path:
            path = os.path.join(os.getcwd(), "smarthome_extract.xlsx")
            print(f"{path=}")
        self.data.to_excel(path, index=False)
        print(f"APISmartHome-extract: data guardada en {path}")
