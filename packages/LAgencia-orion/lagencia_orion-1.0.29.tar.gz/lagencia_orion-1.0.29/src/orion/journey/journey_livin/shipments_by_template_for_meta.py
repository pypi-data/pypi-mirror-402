import json

import requests

from orion.journey.journey_livin.models import RequestToSendNotifications


def sends_nuevos_ingresos(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_nuevos_ingresos")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "nuevos_ingresos", "contactId": record.phone, "clientId": "573184444845", "addMessage": False, "components": [{"type": "button", "index": "0", "parameter_name": "id", "value": record.token}]})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)


    if record.add_data:
        _mobile_adviser = record.add_data.adviser_phone
        _adviser_name = record.add_data.adviser_name
        _name_customer = record.add_data.customer_name
        _mobile_customer = record.add_data.customer_phone
        _token = record.token

        if _mobile_adviser and _adviser_name and _name_customer and _mobile_customer and _token:
            payload = json.dumps(
                {
                    "name": "suscripcion_asesor_ut",
                    "contactId": _mobile_adviser,
                    "clientId": "573184444845",
                    "addMessage": "false",
                    "components": [
                        {"type": "text", "parameter_name": "nombre_asesor", "value": _adviser_name, "index": "0"},
                        {"type": "text", "parameter_name": "nombre_cliente", "value": _name_customer, "index": "1"},
                        {"type": "text", "parameter_name": "cel_cliente", "value": _mobile_customer, "index": "2"},
                        {"type": "button", "index": "0", "parameter_name": "id", "value": _token},
                    ],
                }
            )

            response_adviser = requests.request("GET", url, headers=headers, data=payload)



    print(response.text)


def sends_modifica_precio(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_modifica_precio")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "modifica_precio", "contactId": record.phone, "clientId": "573184444845", "addMessage": False, "components": [{"type": "button", "index": "0", "parameter_name": "id", "value": record.token}]})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def sends_aviso_novedades(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_aviso_novedades")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "aviso_novedades", "contactId": record.phone, "clientId": "573184444845", "addMessage": False, "components": [{"type": "button", "index": "0", "parameter_name": "id", "value": record.token}]})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def send_art1_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art1_castillo")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "45a90_dias_semana1", "contactId": record.phone, "clientId": "573184444845", "addMessage": False})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def send_art2_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art2_castillo")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "art_est_arrend", "contactId": record.phone, "clientId": "573184444845", "addMessage": False})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def send_art3_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art3_castillo")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({"name": "import_contrato", "contactId": record.phone, "clientId": "573184444845", "addMessage": False})
    headers = {"Content-Type": "application/json", "Cookie": "ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4"}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
