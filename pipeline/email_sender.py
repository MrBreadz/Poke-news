"""Génère et envoie la newsletter HTML quotidienne."""
import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "site", "templates")
NEWSLETTERS_DIR = "newsletters"


def _build_newsletter_html(edition: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    tmpl = env.get_template("newsletter.html.j2")
    return tmpl.render(edition=edition, date_str=edition["date"])


def save_newsletter(edition: dict) -> str:
    Path(NEWSLETTERS_DIR).mkdir(exist_ok=True)
    date_str = edition["date"]
    html = _build_newsletter_html(edition)
    path = os.path.join(NEWSLETTERS_DIR, f"{date_str}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"[Email] Newsletter sauvegardée : {path}")
    return html


def send_newsletter(edition: dict, html: str):
    recipients_raw = os.getenv("NEWSLETTER_RECIPIENTS", "").strip()
    if not recipients_raw:
        logger.warning("[Email] NEWSLETTER_RECIPIENTS non défini — envoi ignoré")
        return

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    date_str = edition["date"]
    subject = f"🃏 Pokémon TCG Daily — {date_str}"

    # Détection du provider
    brevo_key = os.getenv("BREVO_API_KEY", "").strip()
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if brevo_key:
        _send_brevo(brevo_key, recipients, subject, html)
    elif gmail_user and gmail_pass:
        _send_gmail(gmail_user, gmail_pass, recipients, subject, html)
    else:
        logger.warning("[Email] Aucun provider configuré (BREVO_API_KEY ou GMAIL_USER/GMAIL_APP_PASSWORD)")


def _send_gmail(user: str, password: str, recipients: list, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user, password)
            server.sendmail(user, recipients, msg.as_string())
        logger.info(f"[Email] Envoyé via Gmail à {recipients}")
    except Exception as e:
        logger.error(f"[Email] Gmail SMTP error: {e}")


def _send_brevo(api_key: str, recipients: list, subject: str, html: str):
    import requests
    payload = {
        "sender": {"name": "Pokémon TCG Daily", "email": "no-reply@pokenewsdaily.fr"},
        "to": [{"email": r} for r in recipients],
        "subject": subject,
        "htmlContent": html,
    }
    try:
        r = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={"api-key": api_key, "content-type": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        logger.info(f"[Email] Envoyé via Brevo à {recipients}")
    except Exception as e:
        logger.error(f"[Email] Brevo error: {e}")
