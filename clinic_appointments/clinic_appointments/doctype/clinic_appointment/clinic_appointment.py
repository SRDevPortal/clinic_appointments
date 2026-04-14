from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, get_time, getdate, now_datetime

ACTIVE_STATUSES = {"Draft", "Scheduled", "Confirmed", "Checked In", "Consulted"}


def autofill_from_patient(doc):
    if not doc.patient:
        return

    patient = frappe.db.get_value(
        "Patient",
        doc.patient,
        [
            "patient_name",
            "mobile",
            "phone",  # 👈 added
            "sr_medical_department",
            "sex",
            "sr_patient_id"
        ],
        as_dict=True,
    )

    if not patient:
        return

    # ✅ Do NOT overwrite user-entered values
    doc.patient_name = doc.patient_name or patient.get("patient_name")
    doc.mobile_number = doc.mobile_number or patient.get("mobile")
    doc.alternate_mobile = doc.alternate_mobile or patient.get("phone")

    # ✅ Always sync system fields
    doc.patient_gender = patient.get("sex")
    doc.patient_id = patient.get("sr_patient_id")
    doc.department = patient.get("sr_medical_department")


class ClinicAppointment(Document):
    def validate(self):
        autofill_from_patient(self)

        if self.duplicate_override and not self.duplicate_override_reason:
            frappe.throw(_("Duplicate Override Reason is required."))

        validate_future_appointment(self)
        validate_duplicate_patient(self)
        validate_doctor_conflict(self)
        validate_slot_available(self)

        update_status_based_on_time(self)


# -----------------------------
# VALIDATIONS
# -----------------------------

def validate_future_appointment(doc):
    if not doc.appointment_date:
        return

    appointment_date = getdate(doc.appointment_date)
    today = getdate(now_datetime())

    if appointment_date < today:
        frappe.throw(_("Appointment date cannot be in the past."))

    if doc.appointment_time:
        appointment_datetime = get_datetime(f"{appointment_date} {doc.appointment_time}")
        if appointment_datetime < now_datetime():
            frappe.throw(_("Appointment time cannot be in the past."))

def validate_duplicate_patient(doc):
    filters = {
        "appointment_date": doc.appointment_date,
        "name": ["!=", doc.name],
        "appointment_status": ["in", list(ACTIVE_STATUSES)],
    }

    if doc.patient:
        filters["patient"] = doc.patient
    else:
        filters["mobile_number"] = doc.mobile_number

    if frappe.db.exists("Clinic Appointment", filters) and not doc.duplicate_override:
        frappe.throw(_("Patient already has an active appointment on this date."))


def validate_doctor_conflict(doc):
    if not doc.practitioner or not doc.appointment_time:
        return

    exists = frappe.db.exists(
        "Clinic Appointment",
        {
            "practitioner": doc.practitioner,
            "appointment_date": doc.appointment_date,
            "appointment_time": doc.appointment_time,
            "name": ["!=", doc.name],
            "appointment_status": ["in", list(ACTIVE_STATUSES)],
        },
    )

    if exists:
        frappe.throw(_("Doctor already has an appointment at this time."))


# 🔥 NEW VALIDATION
def validate_slot_available(doc):
    if not doc.practitioner or not doc.appointment_date or not doc.appointment_time:
        return

    booked = frappe.db.exists(
        "Clinic Appointment",
        {
            "practitioner": doc.practitioner,
            "appointment_date": doc.appointment_date,
            "appointment_time": doc.appointment_time,
            "name": ["!=", doc.name],
            "appointment_status": ["not in", ["Cancelled", "No Show"]],
        }
    )

    if booked:
        frappe.throw(_("Selected slot is already booked. Please choose another."))


# -----------------------------
# AUTO STATUS LOGIC
# -----------------------------

def update_status_based_on_time(doc):
    if not doc.appointment_date or not doc.appointment_time:
        return

    now = datetime.now()

    appointment_datetime = datetime.combine(
        getdate(doc.appointment_date),
        get_time(doc.appointment_time)
    )

    if doc.appointment_status in ["Scheduled", "Confirmed"]:
        if appointment_datetime < now:
            doc.appointment_status = "No Show"
