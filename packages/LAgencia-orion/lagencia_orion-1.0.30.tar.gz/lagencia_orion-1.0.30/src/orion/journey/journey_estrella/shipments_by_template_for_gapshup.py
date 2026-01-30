import json

import requests

from orion.journey.journey_estrella.models import RequestToSendNotifications


def sends_nuevos_ingresos(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_nuevos_ingresos")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "c478de5a-da02-4e88-8a76-5542b33ee6be",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "nuevos_ingresos",
    "IntegratorUser": "0",
    "message": [],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def sends_modifica_precio(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_modifica_precio")

    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "b618e451-7558-481c-a78d-bad0ee4f79fe",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "precio_modif",
    "IntegratorUser": "0",
    "message": [],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

def sends_aviso_novedades(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_aviso_novedades")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "a93a5c67-c6b8-43fe-b1db-2784ef70c5ba",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "nuevo_ingreso",
    "IntegratorUser": "0",
    "message": [],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)









def send_art1_estrella(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art1_castillo")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "6f841f60-0012-415f-a8d2-454a69454532",
        "params": []
        }
    ],
    "localid": "art3",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573022434038/0ea9377a-7f78-4d00-8b92-471124920cf3/1760025819604_busq_inm.jpg"
        },
        "type": "image"
        }
    ],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)



def send_art2_estrella(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art2_castillo")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "dac6e334-9737-4190-a4a1-815b94a47ecd",
        "params": []
        }
    ],
    "localid": "art2",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573022434038/02fe1967-888c-492d-9fb8-f6491e9df4cc/1760026845839_est_lib.jpg"
        },
        "type": "image"
        }
    ],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def send_art3_estrella(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art3_castillo")

    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "laestrellaalquiventas",
    "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
    "template": [
        {
        "id": "4bfe2faf-f064-403f-ab03-3f8eaf7f0686",
        "params": []
        }
    ],
    "localid": "art3",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573022434038/3f15f269-8588-4939-8cf3-cdcf51a2eb54/1760026385518_import_cont.jpg"
        },
        "type": "image"
        }
    ],
    "number": record.phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

