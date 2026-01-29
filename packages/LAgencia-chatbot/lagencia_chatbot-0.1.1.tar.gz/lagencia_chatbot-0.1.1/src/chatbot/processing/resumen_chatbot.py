import pandas as pd
from models.tools import calculate_chatbot_summary


data = pd.read_excel(r"tr.xlsx")[["fecha", "nombre_dia", "oper_rpta", "es_festivo"]]
data = calculate_chatbot_summary(data, "fecha")
print(data)
data.to_excel("resumen.xlsx", index=False)
