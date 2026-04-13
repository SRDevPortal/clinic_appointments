import frappe
from frappe.utils import getdate, now_datetime


ENCOUNTER_TO_APPOINTMENT_MAP = {
    "patient": "patient",
    "patient_name": "patient_name",
    "sr_pe_mobile": "mobile_number",
    "sr_pe_id": "patient_id",
    "sr_pe_deptt": "department",
    "team": "team",
    "sr_notes": "remarks",
    "created_by_agent": "created_by_agent",
    "google_meet_link": "google_meet_link",
    "google_calendar_event_id": "google_calendar_event_id",
    "sr_encounter_status": "encounter_status",
    "sr_encounter_type": "encounter_type",
    "sr_encounter_place": "encounter_place",
}

APPOINTMENT_TO_ENCOUNTER_MAP = {
    "patient": "patient",
    "patient_name": "patient_name",
    "mobile_number": "sr_pe_mobile",
    "patient_id": "sr_pe_id",
    "department": "sr_pe_deptt",
    "team": "team",
    "remarks": "sr_notes",
    "created_by_agent": "created_by_agent",
    "google_meet_link": "google_meet_link",
    "google_calendar_event_id": "google_calendar_event_id",
    "encounter_status": "sr_encounter_status",
    "encounter_type": "sr_encounter_type",
    "encounter_place": "sr_encounter_place",
}


def _meta_fieldnames(doctype):
    return {df.fieldname for df in frappe.get_meta(doctype).fields}


def filter_payload_for_doctype(doctype, payload):
    fieldnames = _meta_fieldnames(doctype)
    return {key: value for key, value in payload.items() if key in fieldnames}


def get_encounter_practitioner(encounter):
    return (
        getattr(encounter, "pe_practitioner", None)
        or getattr(encounter, "practitioner", None)
        or getattr(encounter, "sr_ayurvedic_practitioner", None)
        or getattr(encounter, "sr_homeopathy_practitioner", None)
        or getattr(encounter, "sr_allopathy_practitioner", None)
    )


def get_encounter_appointment_date(encounter):
    return (
        getattr(encounter, "pe_appointment_date", None)
        or getattr(encounter, "encounter_date", None)
        or getdate(now_datetime())
    )


def get_encounter_appointment_time(encounter):
    return (
        getattr(encounter, "pe_appointment_time", None)
        or getattr(encounter, "appointment_time", None)
        or "09:00:00"
    )


def build_appointment_payload_from_encounter(encounter):
    payload = {
        source_field: getattr(encounter, source_field, None)
        for source_field in ENCOUNTER_TO_APPOINTMENT_MAP
    }

    mapped_payload = {
        target_field: payload.get(source_field)
        for source_field, target_field in ENCOUNTER_TO_APPOINTMENT_MAP.items()
        if payload.get(source_field) not in (None, "")
    }

    created_by = getattr(encounter, "created_by_agent", None) or getattr(encounter, "owner", None)

    mapped_payload.update(
        {
            "practitioner": get_encounter_practitioner(encounter),
            "appointment_date": get_encounter_appointment_date(encounter),
            "appointment_time": get_encounter_appointment_time(encounter),
            "encounter_reference": encounter.name,
            "encounter_number": encounter.name,
            "created_by_agent": created_by,
            "created_by_agent_name": frappe.db.get_value("User", created_by, "full_name"),
        }
    )

    return filter_payload_for_doctype("Clinic Appointment", mapped_payload)


def build_encounter_payload_from_appointment(appointment):
    payload = {
        source_field: getattr(appointment, source_field, None)
        for source_field in APPOINTMENT_TO_ENCOUNTER_MAP
    }

    mapped_payload = {
        target_field: payload.get(source_field)
        for source_field, target_field in APPOINTMENT_TO_ENCOUNTER_MAP.items()
        if payload.get(source_field) not in (None, "")
    }

    mapped_payload.update(
        {
            "pe_practitioner": getattr(appointment, "practitioner", None),
            "pe_appointment_date": getattr(appointment, "appointment_date", None),
            "pe_appointment_time": getattr(appointment, "appointment_time", None),
            "encounter_reference": getattr(appointment, "name", None),
            "practitioner": getattr(appointment, "practitioner", None),
        }
    )

    if not mapped_payload.get("sr_encounter_type"):
        mapped_payload["sr_encounter_type"] = "Appointment"

    if not mapped_payload.get("sr_encounter_place"):
        mapped_payload["sr_encounter_place"] = "OPD"

    return filter_payload_for_doctype("Patient Encounter", mapped_payload)
