import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel

from load_templates import select_email_template_table
from orion.journey.journey_villacruz.models import RequestToSendNotifications


"""
Variables de entorno esperadas:

SMTP_SERVER   -> host del servidor SMTP (ej: smtp.gmail.com)
SMTP_USER     -> usuario/correo remitente
SMTP_PASSWORD -> password o app password
SMTP_PORT     -> puerto SMTP (ej: 587)
"""


class DataRequestedForGmail(BaseModel):
    SMTP_SERVER: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_PORT: int
    subject: str
    recipients: List[str]
    html_content: str
    files: Optional[List[Path | str]] = None


def build_gmail_data_from_env(
    subject: str,
    recipients: List[str],
    html_content: str,
    files: Optional[List[Path | str]] = None,
) -> DataRequestedForGmail:
    """
    Construye el objeto DataRequestedForGmail leyendo las variables SMTP
    desde el entorno. Lanza un RuntimeError si falta algo importante.
    """
    server = os.getenv("SMTP_SERVER_VILLACRUZ")
    user = os.getenv("SMTP_USER_VILLACRUZ")
    password = os.getenv("SMTP_PASSWORD_VILLACRUZ")
    port_raw = os.getenv("SMTP_PORT_VILLACRUZ", "587")

    if not all([server, user, password, port_raw]):
        raise RuntimeError(
            "Variables SMTP incompletas: "
            f"SMTP_SERVER={server}, SMTP_USER={user}, SMTP_PORT={port_raw}, "
            f"SMTP_PASSWORD={'***' if password else None}"
        )

    try:
        port = int(port_raw)
    except ValueError:
        raise RuntimeError(f"SMTP_PORT inválido: {port_raw}")

    return DataRequestedForGmail(
        SMTP_SERVER=server,
        SMTP_USER=user,
        SMTP_PASSWORD=password,
        SMTP_PORT=port,
        subject=subject,
        recipients=recipients,
        html_content=html_content,
        files=files,
    )


def shipment_by_email(data: DataRequestedForGmail) -> bool:
    logger.info(f"data.recipients={data.recipients}")
    recipients = [str(recipient).strip() for recipient in data.recipients]
    cc_recipients: List[str] = []
    bcc_recipients: List[str] = []

    # build message
    msg = MIMEMultipart()
    msg["From"] = data.SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = data.subject
    msg["Cc"] = ", ".join(cc_recipients)
    msg["Bcc"] = ", ".join(bcc_recipients)

    # Agregar el HTML como cuerpo del correo
    msg.attach(MIMEText(data.html_content, "html", "utf-8"))

    # Adjuntar archivos
    if data.files:
        for file_path in data.files:
            file_path = Path(file_path)
            if file_path.exists():
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    filename = file_path.name
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}",
                    )

                    msg.attach(part)
                    logger.info(f"✅ Archivo adjuntado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error al adjuntar {file_path}: {e}")
            else:
                logger.warning(f"⚠️ Archivo no encontrado: {file_path}")

    # Envío del correo
    try:
        with smtplib.SMTP(data.SMTP_SERVER, data.SMTP_PORT) as server:
            server.starttls()  # Seguridad TLS
            server.login(data.SMTP_USER, data.SMTP_PASSWORD)
            all_recipients = recipients + cc_recipients + bcc_recipients
            server.sendmail(data.SMTP_USER, all_recipients, msg.as_string())

        logger.info("Correo enviado con éxito ✅")
        return True
    except Exception as e:
        logger.error(f"❌ Error al enviar correo: {e}")
        return False


# ===================== Envios por gmail ===============================


def _send_with_template(template_name: str, subject: str, record: RequestToSendNotifications) -> bool:
    """
    Helper interno para reutilizar lógica entre las diferentes funciones de envío.
    """
    html_template = select_email_template_table(template_name).html_body

    if not html_template:
        logger.warning(f"Envio de correo <{template_name}> a <{record.recipients}> fallido: plantilla vacía")
        return False

    try:
        data_requested = build_gmail_data_from_env(
            subject=subject,
            recipients=record.recipients,
            html_content=html_template,
        )
    except Exception as e:
        logger.error(f"❌ Error al construir DataRequestedForGmail: {e}")
        return False

    ok = shipment_by_email(data_requested)

    if ok:
        logger.warning(f"Envio de correo <{template_name}> a <{record.recipients}> exitoso")
    else:
        logger.warning(f"Envio de correo <{template_name}> a <{record.recipients}> fallido")

    return ok


def send_email_esto_dicen_de_nosotros(record: RequestToSendNotifications) -> bool:
    template_name = "esto_dicen_de_nosotros.html"
    subject = "Descubre por qué nuestros clientes confían en Villacruz 🏡"
    return _send_with_template(template_name, subject, record)


def send_email_invitacion_seccion_nosotros(record: RequestToSendNotifications) -> bool:
    template_name = "invitacion_seccion_nosotros.html"
    subject = "Conoce más sobre Arrendamientos Villacruz"
    return _send_with_template(template_name, subject, record)


def send_email_servicion_diferencial(record: RequestToSendNotifications) -> bool:
    template_name = "servicio_diferencial.html"
    subject = "Así de fácil es encontrar un inmueble con Villacruz"
    return _send_with_template(template_name, subject, record)


if __name__ == "__main__":
    # Ejemplo de prueba local (usa las mismas variables de entorno que en Airflow)
    templates_html = [
        "templates_gmail/esto_dicen_de_nosotros.html",
        "templates_gmail/invitacion_seccion_nosotros.html",
        "templates_gmail/servicio_diferencial.html",
    ]

    for template in templates_html:
        path_template = Path(template)
        if not path_template.exists():
            logger.warning(f"Plantilla no encontrada para prueba: {path_template}")
            continue

        html_template = path_template.read_text(encoding="utf-8")

        try:
            data = build_gmail_data_from_env(
                subject=f"Prueba template: {path_template.name}",
                recipients=["analista1@lagencia.com.co"],
                html_content=html_template,
            )
            result_shipment = shipment_by_email(data)
            logger.info(f"Resultado envío prueba {path_template.name}: {result_shipment}")
        except Exception as e:
            logger.error(f"Error en prueba con {path_template.name}: {e}")
