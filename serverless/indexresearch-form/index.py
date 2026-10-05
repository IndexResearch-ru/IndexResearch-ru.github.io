from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import format_datetime, make_msgid
from typing import Any

POSTBOX_URL = "https://postbox.cloud.yandex.net/v2/email/outbound-emails"
POSTBOX_FROM = os.getenv("POSTBOX_FROM", "form@indexresearch.ru")
POSTBOX_TO = os.getenv("POSTBOX_TO", "research@indexresearch.ru")
ALLOWED_ORIGINS = {
    item.strip()
    for item in os.getenv(
        "ALLOWED_ORIGINS",
        "https://indexresearch.ru,https://www.indexresearch.ru",
    ).split(",")
    if item.strip()
}
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "32768"))
MIN_FILL_SECONDS = float(os.getenv("MIN_FILL_SECONDS", "1.5"))

ALLOWED_UTM = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "utm_id",
    "gclid",
    "yclid",
    "ysclid",
}
EMAIL_RE = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,63}$")
PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")
COUNTRY_RE = re.compile(r"^[a-z]{2}$")


def _headers(event: dict[str, Any]) -> dict[str, str]:
    raw = event.get("headers") or {}
    return {str(k).lower(): str(v) for k, v in raw.items()}


def _cors(origin: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "600",
    }
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
    return headers


def _response(status: int, payload: dict[str, Any], origin: str | None):
    return {
        "statusCode": status,
        "headers": _cors(origin),
        "isBase64Encoded": False,
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _text(value: Any, limit: int) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    if len(value) > limit:
        raise ValueError("field_too_long")
    return value


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_utm(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("invalid_utm")
    result: dict[str, str] = {}
    for key, raw in value.items():
        if key not in ALLOWED_UTM:
            continue
        text = _text(raw, 500)
        if text:
            result[key] = text
    return result


def _iam_token(context: Any) -> str:
    token = getattr(context, "token", None)
    if isinstance(token, dict):
        return str(token.get("access_token") or "")
    if token is not None:
        access_token = getattr(token, "access_token", None)
        if access_token:
            return str(access_token)
    return ""


def _request_id(context: Any) -> str:
    return str(getattr(context, "request_id", "") or "")


def _log(context: Any, status: str, *, site: str = "", lang: str = "", detail: str = "") -> None:
    # Never log the lead payload, name, email, phone, comment, page URL, referrer or UTM values.
    print(
        json.dumps(
            {
                "request_id": _request_id(context),
                "status": status,
                "site": site,
                "lang": lang,
                "detail": detail[:160],
            },
            ensure_ascii=False,
        )
    )


def _email_text(payload: dict[str, Any]) -> str:
    utm = payload["utm"]
    utm_text = "\n".join(f"{key}: {value}" for key, value in utm.items()) or "—"
    return (
        "Новая заявка с IndexResearch.ru\n\n"
        f"Имя: {payload['full_name']}\n"
        f"Телефон: {payload['phone'] or '—'}\n"
        f"Страна телефона: {payload['phone_country'] or '—'}\n"
        f"Email: {payload['email'] or '—'}\n"
        f"Язык: {payload['lang']}\n\n"
        "Комментарий:\n"
        f"{payload['comment'] or '—'}\n\n"
        f"Страница: {payload['page_url'] or '—'}\n"
        f"Referrer: {payload['referrer'] or '—'}\n\n"
        "UTM / источники:\n"
        f"{utm_text}\n\n"
        f"Начало заполнения: {payload['form_started_at'] or '—'}\n"
        f"Отправлено: {payload['submitted_at'] or '—'}\n"
    )


def _send_postbox(payload: dict[str, Any], context: Any) -> str:
    token = _iam_token(context)
    if not token:
        raise RuntimeError("missing_service_account_token")

    message = EmailMessage()
    message["From"] = POSTBOX_FROM
    message["To"] = POSTBOX_TO
    message["Subject"] = "Новая заявка с IndexResearch.ru"
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid(domain="indexresearch.ru")
    if payload["email"]:
        message["Reply-To"] = payload["email"]
    message.set_content(_email_text(payload), charset="utf-8")

    raw_message = base64.b64encode(message.as_bytes(policy=SMTP)).decode("ascii")
    postbox_payload = {
        "FromEmailAddress": POSTBOX_FROM,
        "Destination": {"ToAddresses": [POSTBOX_TO]},
        "Content": {"Raw": {"Data": raw_message}},
    }
    body = json.dumps(postbox_payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        POSTBOX_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-YaCloud-SubjectToken": token,
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        response_body = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(response_body or "{}")
        return str(parsed.get("MessageId") or "")


def _decode_body(event: dict[str, Any]) -> bytes:
    raw = event.get("body")
    if raw is None:
        return b""
    if not isinstance(raw, str):
        raise ValueError("invalid_body")
    if event.get("isBase64Encoded"):
        try:
            return base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise ValueError("invalid_base64") from exc
    return raw.encode("utf-8")


def handler(event: dict[str, Any], context: Any):
    headers = _headers(event)
    origin = headers.get("origin")
    method = str(event.get("httpMethod") or "").upper()

    if origin not in ALLOWED_ORIGINS:
        _log(context, "rejected", detail="origin")
        return _response(403, {"ok": False, "error": "forbidden_origin"}, None)

    if method == "OPTIONS":
        return _response(204, {"ok": True}, origin)

    if method != "POST":
        return _response(405, {"ok": False, "error": "method_not_allowed"}, origin)

    content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        return _response(415, {"ok": False, "error": "unsupported_media_type"}, origin)

    try:
        body = _decode_body(event)
        if not body or len(body) > MAX_BODY_BYTES:
            raise ValueError("invalid_body_size")
        decoded = json.loads(body.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("invalid_json_object")
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _log(context, "invalid_request", detail=str(exc))
        return _response(400, {"ok": False, "error": "invalid_request"}, origin)

    try:
        site = _text(decoded.get("site"), 32)
        lang = _text(decoded.get("lang"), 8).lower()
        if site != "indexresearch":
            raise ValueError("invalid_site")
        if lang not in {"ru", "en", "cn"}:
            raise ValueError("invalid_lang")

        honeypot = _text(decoded.get("company_website"), 300)
        if honeypot:
            _log(context, "spam_silenced", site=site, lang=lang, detail="honeypot")
            return _response(200, {"ok": True}, origin)

        full_name = _text(decoded.get("full_name"), 180)
        phone = _text(decoded.get("phone"), 32)
        phone_country = _text(decoded.get("phone_country"), 8).lower()
        email = _text(decoded.get("email"), 254).lower()
        comment = _text(decoded.get("comment"), 3000)
        page_url = _text(decoded.get("page_url"), 2048)
        referrer = _text(decoded.get("referrer"), 2048)
        form_started_at = _text(decoded.get("form_started_at"), 64)
        submitted_at = _text(decoded.get("submitted_at"), 64)
        utm = _clean_utm(decoded.get("utm"))

        if not full_name:
            raise ValueError("missing_name")
        if not phone and not email:
            raise ValueError("missing_contact")
        if phone and not PHONE_RE.fullmatch(phone):
            raise ValueError("invalid_phone")
        if phone_country and not COUNTRY_RE.fullmatch(phone_country):
            raise ValueError("invalid_phone_country")
        if email and ("\r" in email or "\n" in email or not EMAIL_RE.fullmatch(email)):
            raise ValueError("invalid_email")

        started = _parse_iso(form_started_at)
        submitted = _parse_iso(submitted_at)
        if started and submitted and (submitted - started).total_seconds() < MIN_FILL_SECONDS:
            _log(context, "spam_silenced", site=site, lang=lang, detail="too_fast")
            return _response(200, {"ok": True}, origin)

        payload = {
            "site": site,
            "lang": lang,
            "full_name": full_name,
            "phone": phone,
            "phone_country": phone_country,
            "email": email,
            "comment": comment,
            "page_url": page_url,
            "referrer": referrer,
            "utm": utm,
            "form_started_at": form_started_at,
            "submitted_at": submitted_at,
        }
    except ValueError as exc:
        _log(context, "invalid_request", site=str(decoded.get("site") or ""), lang=str(decoded.get("lang") or ""), detail=str(exc))
        return _response(400, {"ok": False, "error": "invalid_request"}, origin)

    try:
        message_id = _send_postbox(payload, context)
    except urllib.error.HTTPError as exc:
        _log(context, "postbox_error", site=site, lang=lang, detail=f"http_{exc.code}")
        return _response(502, {"ok": False, "error": "delivery_failed"}, origin)
    except urllib.error.URLError:
        _log(context, "postbox_error", site=site, lang=lang, detail="network")
        return _response(502, {"ok": False, "error": "delivery_failed"}, origin)
    except Exception as exc:
        _log(context, "server_error", site=site, lang=lang, detail=type(exc).__name__)
        return _response(500, {"ok": False, "error": "server_error"}, origin)

    _log(context, "sent", site=site, lang=lang, detail=("message_id_received" if message_id else "sent_without_message_id"))
    return _response(200, {"ok": True}, origin)
