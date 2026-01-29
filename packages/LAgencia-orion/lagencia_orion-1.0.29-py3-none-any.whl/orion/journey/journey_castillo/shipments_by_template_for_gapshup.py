import json

import requests
from loguru import logger

from orion.journey.journey_castillo.models import RequestToSendNotifications


def sends_nuevos_ingresos(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_nuevos_ingresos")
    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "729f29ac-5f34-4cf3-8caf-4380a224fd93",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "nuevos_ingresos",
    "IntegratorUser": "0",
    "message": [],
    "number": record.add_data.customer_phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

def sends_aviso_novedades(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_aviso_novedades")
    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "c00ec3f3-0047-499b-b03d-733253c141d1",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "aviso_novedades",
    "IntegratorUser": "0",
    "message": [],
    "number": record.add_data.customer_phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

def sends_modifica_precio(record: RequestToSendNotifications):
    print("HACIENDO ENVIO sends_modifica_precio")

    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "618c62bf-7be9-4a0e-838c-d82d86ae501e",
        "params": [
            record.token
        ]
        }
    ],
    "localid": "modifica_precio",
    "IntegratorUser": "0",
    "message": [],
    "number": record.add_data.customer_phone
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)





def send_art1_castillo(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art1_castillo")
    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "883530ac-dba9-48fa-acc3-f01207ff9001",
        "params": []
        }
    ],
    "localid": "art1",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573175865413/da27201d-5314-470a-afae-12ebc1e04772/1760104970564_busq_inm_cast.jpg"
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



def send_art2_castillo(record: RequestToSendNotifications):
    print("HACIENDO ENVIO send_art2_castillo")
    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "d8594ebf-62b1-4fd1-ba56-89c16a85274e",
        "params": []
        }
    ],
    "localid": "art2",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573175865413/4564c8a1-c74d-48c6-958d-e37bd842b747/1760104553083_est_lib_cast.jpg"
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



def send_art3_castillo(record: RequestToSendNotifications):

    print("HACIENDO ENVIO send_art3_castillo")

    url = "https://arrcastilloback.bonett.chat/gupshup-send-templates"

    payload = json.dumps({
    "app": "arrcastillo",
    "securekey": "sk_e6de090b1f89457698ff81a01b7b9e9e",
    "template": [
        {
        "id": "ad1fde47-3175-477d-9480-e0b4fc22968e",
        "params": []
        }
    ],
    "localid": "art3",
    "IntegratorUser": "0",
    "message": [
        {
        "image": {
            "link": "https://fss.gupshup.io/0/public/0/0/gupshup/573175865413/0aa6987c-c0be-49ed-b17a-c1903c4ebbb3/1760104754563_import_cont_cast.jpg"
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

