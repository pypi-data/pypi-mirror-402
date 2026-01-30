from typing import List

from orion.journey.journey_castillo.models import RequestToSendNotifications
from orion.journey.journey_castillo.shipments_by_template_for_gapshup import send_art1_castillo, send_art2_castillo, send_art3_castillo, sends_aviso_novedades, sends_modifica_precio, sends_nuevos_ingresos
from orion.journey.journey_castillo.shipments_by_template_for_gmail import send_email_esto_dicen_de_nosotros, send_email_invitacion_seccion_nosotros, send_email_servicion_diferencial

# ===================== Servicio para hacer envios ==============================


class SendMessageByAPIMeta:
    _function_by_template = []

    def __init__(self, templates: List[str], record: RequestToSendNotifications):
        self._function_by_template.clear()
        self.record = record

        for template in templates:
            # obtenemos la funciones a ejecutar por nombre de plantilla
            self._function_by_template.append(self.get_funtions_by_sends(template))

    def send(self):
        for function in self._function_by_template:
            print(f"Haciendo envio con funcion {function} con data {self.record}")
            result = function(self.record)
            return result

    def get_funtions_by_sends(self, template_name: str):
        match template_name:
            case "nuevos_ingresos":
                return sends_nuevos_ingresos

            case "aviso_novedades":
                return sends_aviso_novedades

            case "modifica_precio":
                return sends_modifica_precio

            case "art1":
                return send_art1_castillo

            case "art2":
                return send_art2_castillo

            case "art3":
                return send_art3_castillo

            case "mail_nosotros_cast":
                return send_email_invitacion_seccion_nosotros

            case "mail_serv_diferencial_cast":
                return send_email_servicion_diferencial

            case "mail_testimonios_cast":
                return send_email_esto_dicen_de_nosotros

            case _:
                raise


if __name__ == "__main__":
    code = "73498"
    phone = "573103738772"
    # sends_new_revenues(phone=phone, code=code)
    record = RequestToSendNotifications(code=code, phone=phone)
    # sends_modifica_precio(record)
