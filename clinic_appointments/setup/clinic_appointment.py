import logging

import frappe

from clinic_appointments.utils.setup_utils import create_cf_with_module, ensure_module_def, upsert_property_setter


logger = logging.getLogger(__name__)

DT = "Clinic Appointment"


def apply():
    ensure_module_def()
    _setup_sync_fields()
    _set_sync_field_properties()


def _setup_sync_fields():
    create_cf_with_module(
        {
            DT: [
                {
                    "fieldname": "encounter_number",
                    "label": "Encounter Number",
                    "fieldtype": "Data",
                    "insert_after": "encounter_reference",
                },
                {
                    "fieldname": "encounter_type",
                    "label": "Encounter Type",
                    "fieldtype": "Select",
                    "options": "\nFollowup\nOrder\nAppointment",
                    "insert_after": "encounter_number",
                },
                {
                    "fieldname": "encounter_place",
                    "label": "Encounter Place",
                    "fieldtype": "Select",
                    "options": "\nOnline\nOPD",
                    "insert_after": "encounter_type",
                },
                {
                    "fieldname": "encounter_status",
                    "label": "Encounter Status",
                    "fieldtype": "Data",
                    "insert_after": "encounter_place",
                },
                {
                    "fieldname": "created_by_agent",
                    "label": "Created By",
                    "fieldtype": "Link",
                    "options": "User",
                    "insert_after": "encounter_status",
                },
                {
                    "fieldname": "created_by_agent_name",
                    "label": "Created By Name",
                    "fieldtype": "Data",
                    "insert_after": "created_by_agent",
                },
                {
                    "fieldname": "advance_payment_received",
                    "label": "Advance Payment Received",
                    "fieldtype": "Currency",
                    "insert_after": "created_by_agent_name",
                },
                {
                    "fieldname": "payment_status",
                    "label": "Payment Status",
                    "fieldtype": "Data",
                    "insert_after": "advance_payment_received",
                },
                {
                    "fieldname": "google_meet_link",
                    "label": "Google Meet Link",
                    "fieldtype": "Data",
                    "insert_after": "payment_status",
                },
                {
                    "fieldname": "google_calendar_event_id",
                    "label": "Google Calendar Event ID",
                    "fieldtype": "Data",
                    "insert_after": "google_meet_link",
                },
            ]
        }
    )

    frappe.clear_cache(doctype=DT)
    logger.info("Clinic Appointment sync fields setup completed")


def _set_sync_field_properties():
    visible_when_linked = "eval:doc.encounter_reference"

    for field in [
        "encounter_number",
        "encounter_type",
        "encounter_place",
        "encounter_status",
        "created_by_agent",
        "created_by_agent_name",
        "advance_payment_received",
        "payment_status",
        "google_meet_link",
        "google_calendar_event_id",
    ]:
        upsert_property_setter(DT, field, "depends_on", visible_when_linked, "Data")

    for field in [
        "encounter_number",
        "created_by_agent",
        "created_by_agent_name",
        "advance_payment_received",
        "payment_status",
        "google_meet_link",
        "google_calendar_event_id",
    ]:
        upsert_property_setter(DT, field, "read_only", "1", "Check")

    logger.info("Clinic Appointment sync field properties applied")
