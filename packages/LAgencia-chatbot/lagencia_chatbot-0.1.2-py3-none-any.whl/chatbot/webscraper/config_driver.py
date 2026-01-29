import os

from dotenv import load_dotenv

load_dotenv()

# path_root = os.getcwd()
# path_abs_chatbot = os.path.join(path_root, "..", "outputs", "chatbot")
# path_abs_libertador = os.path.join(path_root, "..", "outputs", "libertador")
# path_abs_citas = os.path.join(path_root, "..", "outputs", "citas")


class CredentialsConfig:
    def __init__(self, real_state_name: str = None) -> None:
        real_state_name = real_state_name.lower()

        # * config libertador
        self.URL_segurosbolivar = os.getenv("URL_SEGUROS_BOLIVAR")
        self.URL_ellibertador = os.getenv("URL_EL_LIBERTADOR")

        match real_state_name:
            case "villacruz":
                self.USER_ellibertador = os.getenv("USER_LIBERTADOR_VILLACRUZ")
                self.PASSWORD_ellibertador = os.getenv("PASSWORD_LIBERTADOR_VILLACRUZ")

            case "castillo":
                self.USER_ellibertador = os.getenv("USER_LIBERTADOR_CASTILLO")
                self.PASSWORD_ellibertador = os.getenv("PASSWORD_LIBERTADOR_CASTILLO")

            case "alquiventas":
                self.USER_ellibertador = os.getenv("USER_LIBERTADOR_ALQUIVENTAS")
                self.PASSWORD_ellibertador = os.getenv("PASSWORD_LIBERTADOR_ALQUIVENTAS")

            case "livin":
                self.USER_ellibertador = os.getenv("USER_LIBERTADOR_LIVIN")
                self.PASSWORD_ellibertador = os.getenv("PASSWORD_LIBERTADOR_LIVIN")

        # * config para citas
        match real_state_name:
            case "villacruz":
                self.URL_CITAS = os.getenv("URL_CITAS_VILLACRUZ")
                self.COMNPANY_VILLACRUZ_CITAS = os.getenv("COMNPANY_CITAS_VILLACRUZ")
                self.USER_VILLACRUZ_CITAS = os.getenv("USER_CITAS_VILLACRUZ")
                self.PASSWORD_VILLACRUZ_CITAS = os.getenv("PASSWORD_CITAS_VILLACRUZ")

        # * config para whabonet
        match real_state_name:
            case "castillo":
                self.URL_WHABONETT = os.getenv("URL_WHABONETT_LOGIN_CASTILLO")
                self.ENDPINT_masterTipificacion = os.getenv("URL_WHABONETT_MASTERTIPIFICATION_CASTILLO")
                self.USER_WHABONETT = os.getenv("USER_WHABONETT_CASTILLO")
                self.PASSWORD_WHABONETT = os.getenv("PASSWORD_WHABONETT_CASTILLO")

            case "alquiventas":
                self.URL_WHABONETT = os.getenv("URL_WHABONETT_LOGIN_ALQUIVENTAS")
                self.ENDPINT_masterTipificacion = os.getenv("URL_WHABONETT_MASTERTIPIFICATION_ALQUIVENTAS")
                self.USER_WHABONETT = os.getenv("USER_WHABONETT_ALQUIVENTAS")
                self.PASSWORD_WHABONETT = os.getenv("PASSWORD_WHABONETT_ALQUIVENTAS")
