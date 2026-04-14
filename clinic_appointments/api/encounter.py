import frappe
from frappe.utils import cstr, get_datetime, getdate, now_datetime

from clinic_appointments.utils.sync_audit import add_sync_comment, get_changed_fields
from clinic_appointments.utils.field_mapper import map_appointment_to_encounter
from clinic_appointments.utils.sync_mapper import (
    build_appointment_payload_from_encounter,
    build_encounter_payload_from_appointment,
)


def _active_status_filters():
    return ["Scheduled", "Confirmed", "Checked In", "Consulted"]


def _validate_future_appointment(date, time=None):
    appointment_date = getdate(date)
    today = getdate(now_datetime())

    if appointment_date < today:
        frappe.throw("Appointment date cannot be in the past")

    if time:
        appointment_datetime = get_datetime(f"{appointment_date} {time}")
        if appointment_datetime < now_datetime():
            frappe.throw("Appointment time cannot be in the past")


def _apply_encounter_updates(encounter, updates):
    for fieldname, value in updates.items():
        encounter.set(fieldname, value)


def create_encounter_from_appointment(doc):
    if getattr(doc, "encounter_reference", None):
        return

    try:
        enc = frappe.new_doc("Patient Encounter")

        if hasattr(enc, "appointment"):
            enc.appointment = doc.name

        map_appointment_to_encounter(doc, enc)

        if not doc.patient:
            frappe.throw("Patient is required to create Encounter")

        if not doc.practitioner:
            frappe.throw("Practitioner is required to create Encounter")

        _apply_encounter_updates(enc, build_encounter_payload_from_appointment(doc))
        enc.company = getattr(doc, "company", None)

        enc.flags.skip_clinic_appointment_sync = True
        enc.insert(ignore_permissions=True)
        add_sync_comment(enc, "Clinic Appointment", doc.name, build_encounter_payload_from_appointment(doc).keys())

        doc.db_set("encounter_reference", enc.name, update_modified=False)

        return enc.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Encounter Creation Failed")
        raise


@frappe.whitelist()
def create_appointment_from_encounter(data):
    data = frappe.parse_json(data)

    encounter = data.get("encounter")

    if not encounter:
        frappe.throw("Encounter is required")

    encounter_doc = frappe.get_doc("Patient Encounter", encounter)

    practitioner = data.get("practitioner") or encounter_doc.pe_practitioner
    date = data.get("appointment_date")
    time = data.get("appointment_time")

    if not practitioner or not date or not time:
        return

    _validate_future_appointment(date, time)

    existing = frappe.db.get_value("Clinic Appointment", {"encounter_reference": encounter}, "name")

    conflict_filters = {
        "practitioner": practitioner,
        "appointment_date": date,
        "appointment_time": time,
        "appointment_status": ["in", _active_status_filters()],
    }

    if existing:
        conflict_filters["name"] = ["!=", existing]

    conflict = frappe.db.exists("Clinic Appointment", conflict_filters)

    if conflict:
        frappe.throw("This slot is already booked")

    payload = build_appointment_payload_from_encounter(encounter_doc)
    payload.update(
        {
            "patient": data.get("patient") or payload.get("patient"),
            "practitioner": practitioner,
            "appointment_date": date,
            "appointment_time": time,
            "encounter_reference": encounter,
        }
    )

    if existing:
        appt = frappe.get_doc("Clinic Appointment", existing)
        changed_fields = get_changed_fields(appt, payload)
        appt.update(payload)
        appt.flags.skip_encounter_sync = True
        appt.flags.ignore_validate = True
        appt.save(ignore_permissions=True)
        add_sync_comment(appt, "Patient Encounter", encounter, changed_fields)
        return appt.name

    appt = frappe.new_doc("Clinic Appointment")
    appt.update(payload)
    appt.appointment_status = payload.get("appointment_status") or "Scheduled"
    appt.flags.skip_encounter_sync = True
    appt.flags.ignore_validate = True
    appt.insert(ignore_permissions=True)
    add_sync_comment(appt, "Patient Encounter", encounter, payload.keys())

    encounter_doc.db_set("encounter_reference", appt.name, update_modified=False)

    return appt.name


def _create_or_update_from_encounter(doc):
    if not doc.pe_practitioner or not doc.pe_appointment_date or not doc.pe_appointment_time:
        return

    create_appointment_from_encounter(
        {
            "patient": doc.patient,
            "practitioner": doc.pe_practitioner,
            "appointment_date": doc.pe_appointment_date,
            "appointment_time": doc.pe_appointment_time,
            "encounter": doc.name,
        }
    )


def sync_encounter_from_appointment(doc):
    if not getattr(doc, "encounter_reference", None):
        return

    try:
        enc = frappe.get_doc("Patient Encounter", doc.encounter_reference)
        updates = build_encounter_payload_from_appointment(doc)
        changed_fields = get_changed_fields(enc, updates)

        _apply_encounter_updates(enc, updates)

        enc.flags.ignore_validate = True
        enc.flags.ignore_links = True
        enc.flags.skip_clinic_appointment_sync = True
        enc.save(ignore_permissions=True)
        add_sync_comment(enc, "Clinic Appointment", doc.name, changed_fields)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Encounter Sync Failed")


def after_insert(doc, method):
    try:
        if getattr(doc.flags, "skip_encounter_sync", False):
            return

        if not getattr(doc, "encounter_reference", None):
            create_encounter_from_appointment(doc)
        else:
            sync_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto Encounter Creation Failed")
        raise


def on_update(doc, method):
    try:
        if getattr(doc.flags, "skip_encounter_sync", False):
            return

        if doc.appointment_status == "Checked In" and not getattr(doc, "encounter_reference", None):
            create_encounter_from_appointment(doc)

        sync_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "on_update Failed")
        raise


def after_insert_encounter(doc, method):
    return


def on_update_encounter(doc, method):
    try:
        if cstr(getattr(doc, "encounter_reference", None)).strip():
            return

        if doc.sr_encounter_type != "Appointment":
            return

        _create_or_update_from_encounter(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto Appointment Update Failed")
        raise
