import frappe
from clinic_appointments.utils.field_mapper import map_appointment_to_encounter


# =====================================================
# APPOINTMENT → ENCOUNTER
# =====================================================
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

        enc.patient = doc.patient
        enc.practitioner = doc.practitioner
        enc.company = getattr(doc, "company", None)

        enc.sr_encounter_type = "Appointment"
        enc.sr_encounter_place = "OPD"

        enc.pe_practitioner = doc.practitioner
        enc.pe_appointment_date = doc.appointment_date
        enc.pe_appointment_time = doc.appointment_time

        enc.insert(ignore_permissions=True)

        doc.db_set("encounter_reference", enc.name, update_modified=False)

        return enc.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Encounter Creation Failed")
        raise


# =====================================================
# ENCOUNTER → APPOINTMENT
# =====================================================
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

    # ✅ SAFE EXISTING LOOKUP
    existing = frappe.db.get_value(
        "Clinic Appointment",
        {"encounter_reference": encounter},
        "name"
    )

    # -----------------------------
    # 🚫 SLOT CONFLICT CHECK
    # -----------------------------
    conflict_filters = {
        "practitioner": practitioner,
        "appointment_date": date,
        "appointment_time": time,
        "appointment_status": ["in", ["Scheduled", "Confirmed", "Checked In", "Consulted"]],
    }

    if existing:
        conflict_filters["name"] = ["!=", existing]

    conflict = frappe.db.exists("Clinic Appointment", conflict_filters)

    if conflict:
        frappe.throw("⚠️ This slot is already booked")

    # -----------------------------
    # 🔁 UPDATE EXISTING
    # -----------------------------
    if existing:
        appt = frappe.get_doc("Clinic Appointment", existing)

        if data.get("patient"):
            appt.patient = data.get("patient")

        appt.practitioner = practitioner
        appt.appointment_date = date
        appt.appointment_time = time
        appt.encounter_reference = encounter

        appt.flags.ignore_validate = True
        appt.save(ignore_permissions=True)

        return appt.name

    # -----------------------------
    # 🆕 CREATE NEW
    # -----------------------------
    appt = frappe.new_doc("Clinic Appointment")

    appt.patient = data.get("patient")
    appt.practitioner = practitioner
    appt.appointment_date = date
    appt.appointment_time = time
    appt.status = "Scheduled"
    appt.encounter_reference = encounter

    appt.flags.ignore_validate = True
    appt.insert(ignore_permissions=True)

    encounter_doc.db_set("encounter_reference", appt.name, update_modified=False)

    return appt.name


# =====================================================
# INTERNAL HELPER
# =====================================================
def _create_or_update_from_encounter(doc):

    if not doc.pe_practitioner or not doc.pe_appointment_date or not doc.pe_appointment_time:
        return

    create_appointment_from_encounter({
        "patient": doc.patient,
        "practitioner": doc.pe_practitioner,
        "appointment_date": doc.pe_appointment_date,
        "appointment_time": doc.pe_appointment_time,
        "encounter": doc.name
    })


# =====================================================
# SYNC APPOINTMENT → ENCOUNTER
# =====================================================
def sync_encounter_from_appointment(doc):

    if not getattr(doc, "encounter_reference", None):
        return

    try:
        enc = frappe.get_doc("Patient Encounter", doc.encounter_reference)

        enc.pe_practitioner = doc.practitioner
        enc.pe_appointment_date = doc.appointment_date
        enc.pe_appointment_time = doc.appointment_time

        # 🔥 LOOP SAFE
        enc.flags.ignore_validate = True
        enc.flags.ignore_links = True
        enc.save(ignore_permissions=True)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Encounter Sync Failed")


# =====================================================
# APPOINTMENT HOOKS
# =====================================================
def after_insert(doc, method):

    try:
        if not getattr(doc, "encounter_reference", None):
            create_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto Encounter Creation Failed")
        raise


def on_update(doc, method):

    try:
        if (
            doc.appointment_status == "Checked In"
            and not getattr(doc, "encounter_reference", None)
        ):
            create_encounter_from_appointment(doc)

        sync_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "on_update Failed")
        raise


# =====================================================
# ENCOUNTER HOOKS
# =====================================================
def after_insert_encounter(doc, method):
    """
    Disabled to prevent early duplicate creation
    """
    return


def on_update_encounter(doc, method):

    try:
        # 🔥 IMPORTANT: DO NOT create appointment if already linked
        if doc.encounter_reference:
            return

        if doc.sr_encounter_type != "Appointment":
            return

        _create_or_update_from_encounter(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto Appointment Update Failed")
        raise