import json

import requests

from orion.journey.journey_livin.models import RequestToSendNotifications


def sends_nuevos_ingresos(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_nuevos_ingresos")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "nuevos_ingresos",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False,
    "components": [
        {
        "type": "button",
        "index": "0",
        "parameter_name": "id",
        "value": record.token
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def sends_modifica_precio(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_modifica_precio")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "modifica_precio",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False,
    "components": [
        {
        "type": "button",
        "index": "0",
        "parameter_name": "id",
        "value": record.token
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def sends_aviso_novedades(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_aviso_novedades")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "aviso_novedades",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False,
    "components": [
        {
        "type": "button",
        "index": "0",
        "parameter_name": "id",
        "value": record.token
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)










def send_art1_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art1_castillo")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "45a90_dias_semana1",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)



def send_art2_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art2_castillo")
    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "art_est_arrend",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def send_art3_livin(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art3_castillo")

    url = "https://smart-home.com.co/WhatsAppTemplate.aspx?method=POST"

    payload = json.dumps({
    "name": "import_contrato",
    "contactId": record.phone,
    "clientId": "573184444845",
    "addMessage": False
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'ASP.NET_SessionId=up1ipnetbqgs0n3fnmla1ak4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


