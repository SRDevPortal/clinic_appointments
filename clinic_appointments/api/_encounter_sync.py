import frappe
from frappe.utils import getdate, now_datetime


ACTIVE_STATUSES = {"Draft", "Scheduled", "Confirmed", "Checked In", "Consulted"}


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


def create_or_update_clinic_appointment_from_encounter(doc, method=None):
    try:
        # Only OPD encounters
        if getattr(doc, "sr_encounter_place", None) != "OPD":
            return

        appointment_date = getattr(doc, "encounter_date", None) or getdate(now_datetime())

        appointment_name = frappe.db.get_value(
            "Clinic Appointment",
            {"linked_encounter": doc.name},
            "name"
        )

        advance = _derive_advance_payment(doc)

        practitioner = (
            getattr(doc, "practitioner", None)
            or getattr(doc, "sr_ayurvedic_practitioner", None)
            or getattr(doc, "sr_homeopathy_practitioner", None)
            or getattr(doc, "sr_allopathy_practitioner", None)
        )

        created_by = getattr(doc, "created_by_agent", None) or getattr(doc, "owner", None)

        payload = {
            "patient": getattr(doc, "patient", None),
            "patient_name": getattr(doc, "patient_name", None),
            "mobile_number": getattr(doc, "sr_pe_mobile", None),
            "appointment_date": appointment_date,
            "appointment_time": getattr(doc, "appointment_time", None) or "09:00:00",
            "appointment_status": _derive_appointment_status(doc),
            "linked_encounter": doc.name,
            "encounter_number": doc.name,
            "encounter_status": getattr(doc, "sr_encounter_status", None),
            "encounter_type": getattr(doc, "sr_encounter_type", None),
            "encounter_place": getattr(doc, "sr_encounter_place", None),
            "created_by_agent": created_by,
            "created_by_agent_name": frappe.db.get_value("User", created_by, "full_name"),
            "advance_payment_received": advance,
            "payment_status": "Paid" if advance > 0 else "Unpaid",
            "practitioner": practitioner,
            "department": getattr(doc, "medical_department", None)
                          or getattr(doc, "sr_pe_deptt", None),
            "team": getattr(doc, "team", None),
            "remarks": getattr(doc, "sr_notes", None),
        }

        if appointment_name:
            clinic_appointment = frappe.get_doc("Clinic Appointment", appointment_name)
            clinic_appointment.update(payload)
            clinic_appointment.flags.ignore_validate_update_after_submit = True
            clinic_appointment.save(ignore_permissions=True)
        else:
            clinic_appointment = frappe.get_doc({
                "doctype": "Clinic Appointment",
                **payload
            })
            clinic_appointment.insert(ignore_permissions=True)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Clinic Appointment Sync Failed"
        )