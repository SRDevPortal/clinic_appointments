import frappe
import logging

from clinic_appointments.utils.setup_utils import (
    create_cf_with_module,
    ensure_field_after,
    ensure_module_def,
    upsert_property_setter
)

logger = logging.getLogger(__name__)

DT = "Patient Encounter"


def apply():
    ensure_module_def()
    _setup_appointment_fields()
    _set_appointment_field_visibility()
    _set_read_only_fields()


# =====================================================
# CREATE FIELDS
# =====================================================
def _setup_appointment_fields():

    create_cf_with_module({
        DT: [

            {
                "fieldname": "pe_practitioner",
                "label": "Appointment With",
                "fieldtype": "Link",
                "options": "Healthcare Practitioner",
                "insert_after": "encounter_time",
                "in_standard_filter": 1,
            },

            {
                "fieldname": "pe_appointment_date",
                "label": "Appointment Date",
                "fieldtype": "Date",
                "insert_after": "pe_practitioner",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },

            {
                "fieldname": "pe_appointment_time",
                "label": "Appointment Time",
                "fieldtype": "Time",
                "insert_after": "pe_appointment_date",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "encounter_reference",
                "label": "Linked Appointment",
                "fieldtype": "Link",
                "options": "Clinic Appointment",
                "insert_after": "pe_appointment_time",
            },
            {
                "fieldname": "google_meet_link",
                "label": "Google Meet Link",
                "fieldtype": "Data",
                "insert_after": "encounter_reference",
            },
            {
                "fieldname": "google_calendar_event_id",
                "label": "Google Calendar Event ID",
                "fieldtype": "Data",
                "insert_after": "google_meet_link",
            },

        ]
    })

    ensure_field_after(DT, "pe_appointment_time", "pe_appointment_date")

    frappe.clear_cache(doctype=DT)

    logger.info("✅ Appointment fields setup completed")


# =====================================================
# FIELD VISIBILITY LOGIC
# =====================================================
def _set_appointment_field_visibility():
    """
    Show fields only when Encounter Type = Appointment
    """

    appointment_fields = [
        "pe_practitioner",
        "pe_appointment_date",
        "pe_appointment_time",
        "encounter_reference",
        "medical_department",
    ]

    appointment_condition = 'eval:doc.sr_encounter_type=="Appointment"'
    online_appointment_condition = (
        'eval:doc.sr_encounter_type=="Appointment" && doc.sr_encounter_place=="Online"'
    )

    for field in appointment_fields:
        upsert_property_setter(
            DT,
            field,
            "depends_on",
            appointment_condition,
            "Data"
        )

    for field in ["google_meet_link", "google_calendar_event_id"]:
        upsert_property_setter(
            DT,
            field,
            "depends_on",
            online_appointment_condition,
            "Data"
        )

    logger.info("✅ Appointment field visibility applied")


# =====================================================
# READ ONLY FIELD
# =====================================================
def _set_read_only_fields():
    """
    Make appointment fields read-only
    """

    # Appointment Time
    upsert_property_setter(
        DT,
        "pe_appointment_time",
        "read_only",
        "1",
        "Check"
    )

    # ✅ Linked Appointment (NEW)
    upsert_property_setter(
        DT,
        "encounter_reference",
        "read_only",
        "1",
        "Check"
    )

    upsert_property_setter(
        DT,
        "google_meet_link",
        "read_only",
        "1",
        "Check"
    )

    upsert_property_setter(
        DT,
        "google_calendar_event_id",
        "read_only",
        "1",
        "Check"
    )

    logger.info("✅ Read-only fields applied")