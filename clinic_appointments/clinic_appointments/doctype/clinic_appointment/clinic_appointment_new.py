import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, get_time
from datetime import datetime


ACTIVE_STATUSES = {"Draft", "Scheduled", "Confirmed", "Checked In", "Consulted"}


# =====================================================
# MAIN DOC CLASS
# =====================================================
class ClinicAppointment(Document):

    def validate(self):

        # =====================================================
        # 🔥 FORCE PATIENT DATA (FINAL FIX)
        # =====================================================
        if self.patient:

            patient_data = frappe.db.get_value(
                "Patient",
                self.patient,
                [
                    "patient_name",
                    "mobile",
                    "phone",
                    "sex",
                    "sr_patient_id",
                    "sr_medical_department"
                ],
                as_dict=True
            )

            if patient_data:
                self.patient_name = self.patient_name or patient_data.get("patient_name")
                self.mobile_number = self.mobile_number or patient_data.get("mobile")
                self.alternate_mobile = self.alternate_mobile or patient_data.get("phone")

                self.patient_gender = patient_data.get("sex")
                self.patient_id = patient_data.get("sr_patient_id")
                self.department = patient_data.get("sr_medical_department")

        # =====================================================
        # 🚨 HARD VALIDATION (PREVENT ERROR)
        # =====================================================
        if not self.patient_name:
            frappe.throw(_("Patient Name is required"))

        if not self.mobile_number:
            frappe.throw(_("Mobile Number is required"))

        # =====================================================
        # OTHER VALIDATIONS
        # =====================================================
        if self.duplicate_override and not self.duplicate_override_reason:
            frappe.throw(_("Duplicate Override Reason is required."))

        validate_slot_available(self)
        update_status_based_on_time(self)


# =====================================================
# SLOT VALIDATION (FINAL LOGIC)
# =====================================================
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


# =====================================================
# AUTO STATUS LOGIC
# =====================================================
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