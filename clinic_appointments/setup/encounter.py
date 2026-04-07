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

    fields = [
        "pe_practitioner",
        "pe_appointment_date",
        "pe_appointment_time",
        "encounter_reference",
        "medical_department",
    ]

    condition = 'eval:doc.sr_encounter_type=="Appointment"'

    for field in fields:
        upsert_property_setter(
            DT,
            field,
            "depends_on",
            condition,
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

    logger.info("✅ Read-only fields applied")