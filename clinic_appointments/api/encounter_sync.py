import frappe

from clinic_appointments.integrations.google_calendar import (
    GoogleCalendarAPIError,
    GoogleCalendarConfigError,
    sync_meet_event,
)
from clinic_appointments.utils.sync_audit import add_sync_comment, get_changed_fields
from clinic_appointments.utils.sync_mapper import build_appointment_payload_from_encounter

def _derive_appointment_status(encounter):
    status = (getattr(encounter, "sr_encounter_status", None) or "").strip()
    if status:
        return status
    return "Draft"


def _derive_advance_payment(encounter):
    total = 0
    for row in getattr(encounter, "enc_multi_payments", []) or []:
        total += float(getattr(row, "mmp_paid_amount", 0) or 0)
    return total


def _is_online_appointment(encounter) -> bool:
    return (
        (getattr(encounter, "sr_encounter_type", None) or "").strip() == "Appointment"
        and (getattr(encounter, "sr_encounter_place", None) or "").strip() == "Online"
    )


def _should_sync_clinic_appointment(encounter) -> bool:
    encounter_type = (getattr(encounter, "sr_encounter_type", None) or "").strip()
    place = (getattr(encounter, "sr_encounter_place", None) or "").strip()
    if encounter_type != "Appointment":
        return False
    if place == "OPD":
        return True
    return _is_online_appointment(encounter)


def _notify_user(message):
    if getattr(frappe.local, "request", None):
        frappe.msgprint(message, alert=True, indicator="orange")


def _sync_google_fields_back_to_appointment(encounter):
    appointment_name = getattr(encounter, "encounter_reference", None)
    if not appointment_name:
        return

    appointment_updates = {}
    appointment_meta = frappe.get_meta("Clinic Appointment")

    if appointment_meta.get_field("google_meet_link") and getattr(encounter, "google_meet_link", None):
        appointment_updates["google_meet_link"] = getattr(encounter, "google_meet_link")

    if appointment_meta.get_field("google_calendar_event_id") and getattr(
        encounter, "google_calendar_event_id", None
    ):
        appointment_updates["google_calendar_event_id"] = getattr(
            encounter, "google_calendar_event_id"
        )

    if appointment_updates:
        frappe.db.set_value(
            "Clinic Appointment",
            appointment_name,
            appointment_updates,
            update_modified=False,
        )


def _sync_google_meet_link(encounter):
    if not _is_online_appointment(encounter):
        return

    meta = frappe.get_meta("Patient Encounter")
    if not meta.get_field("google_meet_link"):
        return

    if not getattr(encounter, "pe_appointment_date", None) and not getattr(
        encounter, "encounter_date", None
    ):
        return

    if not getattr(encounter, "pe_appointment_time", None) and not getattr(
        encounter, "appointment_time", None
    ):
        return

    try:
        result = sync_meet_event(encounter)
    except GoogleCalendarConfigError as exc:
        _notify_user(
            f"Online appointment saved, but Google Meet link was not generated: {exc}"
        )
        return
    except GoogleCalendarAPIError:
        frappe.log_error(frappe.get_traceback(), "Google Meet Sync Failed")
        _notify_user(
            "Online appointment saved, but Google Meet link generation failed. "
            "Please check Google Calendar settings."
        )
        return
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Google Meet Sync Failed")
        _notify_user(
            "Online appointment saved, but Google Meet link generation failed. "
            "Please check Google Calendar settings."
        )
        return

    updates = {}
    meet_link = result.get("meet_link")
    event_id = result.get("event_id")

    if meet_link and getattr(encounter, "google_meet_link", None) != meet_link:
        updates["google_meet_link"] = meet_link

    if meta.get_field("google_calendar_event_id") and event_id:
        if getattr(encounter, "google_calendar_event_id", None) != event_id:
            updates["google_calendar_event_id"] = event_id

    if updates:
        frappe.db.set_value("Patient Encounter", encounter.name, updates, update_modified=False)
        for key, value in updates.items():
            setattr(encounter, key, value)


def create_or_update_clinic_appointment_from_encounter(doc, method=None):
    try:
        if getattr(doc.flags, "skip_clinic_appointment_sync", False):
            _sync_google_meet_link(doc)
            _sync_google_fields_back_to_appointment(doc)
            return

        _sync_google_meet_link(doc)

        if not _should_sync_clinic_appointment(doc):
            return

        appointment_name = getattr(doc, "encounter_reference", None) or frappe.db.get_value(
            "Clinic Appointment",
            {"encounter_reference": doc.name},
            "name",
        )

        payload = build_appointment_payload_from_encounter(doc)
        advance_payment = _derive_advance_payment(doc)
        payload["appointment_status"] = _derive_appointment_status(doc)
        payload["advance_payment_received"] = advance_payment
        payload["payment_status"] = "Paid" if advance_payment > 0 else "Unpaid"

        if appointment_name:
            clinic_appointment = frappe.get_doc("Clinic Appointment", appointment_name)
            changed_fields = get_changed_fields(clinic_appointment, payload)
            clinic_appointment.update(payload)
            clinic_appointment.flags.skip_encounter_sync = True
            clinic_appointment.flags.ignore_validate_update_after_submit = True
            clinic_appointment.save(ignore_permissions=True)
            add_sync_comment(clinic_appointment, "Patient Encounter", doc.name, changed_fields)
        else:
            clinic_appointment = frappe.get_doc(
                {
                    "doctype": "Clinic Appointment",
                    **payload,
                }
            )
            clinic_appointment.flags.skip_encounter_sync = True
            clinic_appointment.insert(ignore_permissions=True)
            add_sync_comment(
                clinic_appointment,
                "Patient Encounter",
                doc.name,
                payload.keys(),
            )

        if getattr(doc, "encounter_reference", None) != clinic_appointment.name:
            frappe.db.set_value(
                "Patient Encounter",
                doc.name,
                "encounter_reference",
                clinic_appointment.name,
                update_modified=False,
            )
            doc.encounter_reference = clinic_appointment.name

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Clinic Appointment Sync Failed",
        )
