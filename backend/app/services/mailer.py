"""Envio de e-mails via SMTP (Gmail, Brevo, Resend, Outlook... qualquer um serve).

Sem SMTP configurado (desenvolvimento), o e-mail não é enviado: o conteúdo aparece no
log da API, então dá para testar a recuperação de senha copiando o link de lá.
"""

import html
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger("uvicorn.error")


def send_email(to: str, subject: str, text: str, html_body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        log.warning("SMTP não configurado: e-mail para %s NÃO enviado.\n%s", to, text)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to
    message.set_content(text)
    message.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    try:
        if settings.smtp_security == "ssl":
            server = smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, context=context, timeout=15
            )
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
        with server:
            if settings.smtp_security == "starttls":
                server.starttls(context=context)
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError):
        # Roda em background: só registra. A pessoa pode pedir o link de novo.
        log.exception("Falha ao enviar e-mail para %s", to)


def send_password_reset(to: str, name: str, link: str, minutes: int) -> None:
    subject = "Redefina sua senha do JAOPALLOOZA 🔑"
    text = (
        f"Oi, {name}!\n\n"
        "Alguém (tomara que você) pediu para redefinir sua senha do JAOPALLOOZA.\n"
        f"Use o link abaixo para criar uma nova. Ele vale por {minutes} minutos e só funciona"
        " uma vez:\n\n"
        f"{link}\n\n"
        "Se não foi você, é só ignorar este e-mail: sua senha continua a mesma."
    )
    safe_name, safe_link = html.escape(name), html.escape(link, quote=True)
    html_body = f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0 auto;color:#121212">
  <div style="background:#c81e15;color:#fff;padding:24px;border-radius:16px 16px 0 0">
    <div style="font-size:26px;font-weight:bold;letter-spacing:1px">JAOPALLOOZA</div>
  </div>
  <div style="border:1px solid #ebebeb;border-top:0;padding:24px;border-radius:0 0 16px 16px">
    <p style="font-size:18px;margin:0 0 12px">Oi, {safe_name}! 👋</p>
    <p>Alguém (tomara que você) pediu para redefinir sua senha.
       O link vale por <strong>{minutes} minutos</strong> e só funciona uma vez.</p>
    <p style="text-align:center;margin:28px 0">
      <a href="{safe_link}" style="background:#c81e15;color:#fff;text-decoration:none;
         padding:14px 28px;border-radius:12px;font-weight:bold;display:inline-block">
        Criar nova senha
      </a>
    </p>
    <p style="color:#6b6b6b;font-size:13px">Se não foi você, é só ignorar este e-mail:
       sua senha continua a mesma.</p>
  </div>
</div>"""
    send_email(to, subject, text, html_body)
