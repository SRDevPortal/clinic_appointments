from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import quote

import frappe
import requests
from frappe.utils import get_system_timezone, getdate, get_time


TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarConfigError(Exception):
    """Raised when Google Calendar configuration is incomplete."""


class GoogleCalendarAPIError(Exception):
    """Raised when Google Calendar API calls fail."""


def _get_conf_value(*keys, default=None):
    for key in keys:
        value = frappe.conf.get(key)
        if value not in (None, ""):
            return value
    return default


def _require_conf_value(*keys, label: str):
    value = _get_conf_value(*keys)
    if value in (None, ""):
        raise GoogleCalendarConfigError(f"Missing Google Calendar setting: {label}")
    return value


def _get_access_token() -> str:
    response = requests.post(
        _get_conf_value("google_calendar_token_url", default=TOKEN_URL),
        data={
            "client_id": _require_conf_value(
                "google_calendar_client_id",
                "google_client_id",
                label="google_calendar_client_id",
            ),
            "client_secret": _require_conf_value(
                "google_calendar_client_secret",
                "google_client_secret",
                label="google_calendar_client_secret",
            ),
            "refresh_token": _require_conf_value(
                "google_calendar_refresh_token",
                "google_refresh_token",
                label="google_calendar_refresh_token",
            ),
            "grant_type": "refresh_token",
        },
        timeout=30,
    )

    if not response.ok:
        raise GoogleCalendarAPIError(
            f"Google token request failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise GoogleCalendarAPIError("Google token response did not include an access_token")

    return access_token


def _build_event_payload(encounter) -> dict:
    appointment_date = getattr(encounter, "pe_appointment_date", None) or getattr(
        encounter, "encounter_date", None
    )
    appointment_time = getattr(encounter, "pe_appointment_time", None) or getattr(
        encounter, "appointment_time", None
    )

    if not appointment_date or not appointment_time:
        raise GoogleCalendarConfigError(
            "Appointment date and time are required before generating a Google Meet link."
        )

    timezone = _get_conf_value(
        "google_calendar_timezone",
        "google_meet_timezone",
        default=get_system_timezone(),
    )
    duration_minutes = int(
        _get_conf_value("google_calendar_meet_duration_minutes", default=30) or 30
    )

    start_at = datetime.combine(getdate(appointment_date), get_time(appointment_time))
    end_at = start_at + timedelta(minutes=duration_minutes)

    patient_label = getattr(encounter, "patient_name", None) or getattr(encounter, "patient", None)
    practitioner_label = getattr(encounter, "pe_practitioner", None) or getattr(
        encounter, "practitioner", None
    )

    description_lines = [
        f"Patient Encounter: {encounter.name}",
        f"Patient: {patient_label or 'Unknown Patient'}",
    ]
    if practitioner_label:
        description_lines.append(f"Practitioner: {practitioner_label}")

    return {
        "summary": f"Online Appointment - {patient_label or encounter.name}",
        "description": "\n".join(description_lines),
        "start": {"dateTime": start_at.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_at.isoformat(), "timeZone": timezone},
        "conferenceData": {
            "createRequest": {
                "requestId": frappe.generate_hash(length=16),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "extendedProperties": {
            "private": {
                "patient_encounter": encounter.name,
            }
        },
    }


def _extract_meet_link(payload: dict) -> str | None:
    if payload.get("hangoutLink"):
        return payload["hangoutLink"]

    conference_data = payload.get("conferenceData") or {}
    for entry in conference_data.get("entryPoints") or []:
        if entry.get("entryPointType") == "video" and entry.get("uri"):
            return entry["uri"]

    return None


def _calendar_url(calendar_id: str, event_id: str | None = None) -> str:
    encoded_calendar_id = quote(calendar_id, safe="")
    if event_id:
        return f"{CALENDAR_API_BASE}/calendars/{encoded_calendar_id}/events/{quote(event_id, safe='')}"
    return f"{CALENDAR_API_BASE}/calendars/{encoded_calendar_id}/events"


def create_meet_event(encounter) -> dict:
    token = _get_access_token()
    calendar_id = _get_conf_value("google_calendar_id", default="primary")

    response = requests.post(
        _calendar_url(calendar_id),
        params={"conferenceDataVersion": 1, "sendUpdates": "none"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=_build_event_payload(encounter),
        timeout=30,
    )

    if not response.ok:
        raise GoogleCalendarAPIError(
            f"Google event create failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    return {
        "event_id": payload.get("id"),
        "meet_link": _extract_meet_link(payload),
    }


def update_meet_event(encounter, event_id: str) -> dict:
    token = _get_access_token()
    calendar_id = _get_conf_value("google_calendar_id", default="primary")

    response = requests.patch(
        _calendar_url(calendar_id, event_id=event_id),
        params={"conferenceDataVersion": 1, "sendUpdates": "none"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=_build_event_payload(encounter),
        timeout=30,
    )

    if not response.ok:
        raise GoogleCalendarAPIError(
            f"Google event update failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    return {
        "event_id": payload.get("id") or event_id,
        "meet_link": _extract_meet_link(payload),
    }


def sync_meet_event(encounter) -> dict:
    event_id = getattr(encounter, "google_calendar_event_id", None)
    if event_id:
        return update_meet_event(encounter, event_id)
    return create_meet_event(encounter)
