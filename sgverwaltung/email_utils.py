"""
Zentrale E-Mail-Hilfsfunktion für sg-verwaltung.

Alle Apps sollen ausschließlich `send_email` aus diesem Modul verwenden,
damit das E-Mail-Verhalten projektübergreifend an einer einzigen Stelle
konfiguriert werden kann.

Verwendung:
    from sgverwaltung.email_utils import send_email

    send_email(
        to=['empfaenger@example.com'],
        subject='Betreff',
        body='Textnachricht',
    )
"""

import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail

logger = logging.getLogger('sgverwaltung.email')


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def send_email(
    to: list[str],
    subject: str,
    body: str,
    *,
    html_body: str | None = None,
    from_email: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    background: bool = True,
) -> bool:
    """
    Versendet eine E-Mail und gibt True zurück wenn erfolgreich, sonst False.

    Standardmäßig wird die Mail in einem Hintergrund-Thread gesendet
    (background=True), damit die aufrufende View nicht blockiert wird.
    Mit background=False wartet die Funktion auf das Ergebnis und gibt
    True/False zurück.

    Im DEBUG-Modus wird die E-Mail nicht an die eigentlichen Empfänger
    gesendet, sondern an settings.DEBUG_EMAIL_RECIPIENT. Die ursprünglichen
    Empfänger werden als erste Zeilen im E-Mail-Body aufgeführt.

    Bei einem Sendefehler wird der Fehler geloggt und eine Benachrichtigung
    an settings.ADMIN_EMAIL geschickt. Diese Funktion wirft nie eine
    Exception — Aufrufer können sich auf den bool-Rückgabewert verlassen.

    Parameter:
        to          – Liste mit Empfänger-Adressen (Pflicht)
        subject     – Betreff (Pflicht)
        body        – Reiner Text-Body (Pflicht)
        html_body   – Optionaler HTML-Body (wird als Alternative eingebettet)
        from_email  – Absenderadresse; Standard: settings.DEFAULT_FROM_EMAIL
        cc          – Optionale CC-Empfänger
        bcc         – Optionale BCC-Empfänger
        background  – Bei True (Standard) wird im Hintergrund gesendet;
                      Rückgabewert ist dann immer True

    Rückgabe:
        True  – E-Mail gesendet oder Hintergrund-Versand gestartet
        False – Fehler beim synchronen Versand (background=False)
    """
    if background:
        threading.Thread(
            target=send_email,
            kwargs=dict(
                to=to, subject=subject, body=body,
                html_body=html_body, from_email=from_email,
                cc=cc, bcc=bcc, background=False,
            ),
            daemon=True,
        ).start()
        return True
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    # actual_to  = list(to) # TODO
    actual_to  = [settings.DEBUG_EMAIL_RECIPIENT]
    actual_cc  = list(cc)  if cc  else []
    actual_bcc = list(bcc) if bcc else []

    if settings.DEBUG:
        redirect_header = _build_redirect_header(actual_to, actual_cc, actual_bcc)
        body = redirect_header + body
        if html_body is not None:
            html_body = redirect_header.replace('\n', '<br>\n') + html_body

        actual_to  = [settings.DEBUG_EMAIL_RECIPIENT]
        actual_cc  = []
        actual_bcc = []
        subject    = f'[DEBUG] {subject}'

    try:
        if html_body:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=actual_to,
                cc=actual_cc,
                bcc=actual_bcc,
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send()
            logger.info('E-Mail gesendet | to=%s | subject=%r', actual_to, subject)
        else:
            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=actual_to,
                fail_silently=False,
            )
            logger.info('E-Mail gesendet | to=%s | subject=%r', actual_to, subject)
        return True

    except Exception as exc:
        logger.error(
            'E-Mail-Versand fehlgeschlagen | to=%s | subject=%r | Fehler: %s',
            actual_to, subject, exc,
            exc_info=True,
        )
        _send_admin_notification(original_to=to, subject=subject, error=exc)
        return False


# ---------------------------------------------------------------------------
# Private Hilfsfunktionen
# ---------------------------------------------------------------------------

def _build_redirect_header(
    original_to: list[str],
    original_cc: list[str],
    original_bcc: list[str],
) -> str:
    """Erzeugt den Hinweis-Header, der im DEBUG-Modus dem Body vorangestellt wird."""
    lines = [
        '*** ENTWICKLUNGSMODUS: Diese E-Mail wurde umgeleitet. ***',
        f'Ursprüngliche Empfänger (To):  {", ".join(original_to)}',
    ]
    if original_cc:
        lines.append(f'Ursprüngliche Empfänger (CC):  {", ".join(original_cc)}')
    if original_bcc:
        lines.append(f'Ursprüngliche Empfänger (BCC): {", ".join(original_bcc)}')
    lines.append('')
    lines.append('')
    return '\n'.join(lines)


def _send_admin_notification(
    original_to: list[str],
    subject: str,
    error: Exception,
) -> None:
    """
    Sendet eine Fehler-Benachrichtigung an settings.ADMIN_EMAIL.
    Wirft nie eine Exception — Fehler werden nur geloggt.
    Ruft niemals send_email() auf (kein Rekursionsrisiko).
    """
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        return

    try:
        send_mail(
            subject='[SYNC] E-Mail-Versand fehlgeschlagen',
            message=(
                f'Beim Versand einer E-Mail ist ein Fehler aufgetreten.\n\n'
                f'Ursprünglicher Betreff: {subject}\n'
                f'Ursprüngliche Empfänger: {", ".join(original_to)}\n\n'
                f'Fehlermeldung:\n{error}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception as exc:
        logger.error(
            'Admin-Benachrichtigung konnte nicht gesendet werden: %s', exc,
            exc_info=True,
        )
