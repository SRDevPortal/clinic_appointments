import frappe
from clinic_appointments.utils.field_mapper import map_appointment_to_encounter


# =====================================================
# APPOINTMENT → ENCOUNTER
# =====================================================
def create_encounter_from_appointment(doc):

    # ✅ prevent duplicate
    if getattr(doc, "encounter_reference", None):
        return

    try:
        enc = frappe.new_doc("Patient Encounter")

        # 🔗 link appointment (if standard field exists)
        if hasattr(enc, "appointment"):
            enc.appointment = doc.name

        # 🔥 dynamic mapping
        map_appointment_to_encounter(doc, enc)

        # ✅ mandatory validations
        if not doc.patient:
            frappe.throw("Patient is required to create Encounter")

        if not doc.practitioner:
            frappe.throw("Practitioner is required to create Encounter")

        # core fields
        enc.patient = doc.patient
        enc.practitioner = doc.practitioner
        enc.company = getattr(doc, "company", None)

        # custom fields
        enc.sr_encounter_type = "Appointment"
        enc.sr_encounter_place = "OPD"

        enc.pe_practitioner = doc.practitioner
        enc.pe_appointment_date = doc.appointment_date
        enc.pe_appointment_time = doc.appointment_time

        # insert
        enc.insert(ignore_permissions=True)

        # 🔗 back link
        doc.db_set("encounter_reference", enc.name, update_modified=False)

        return enc.name

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Encounter Creation Failed"
        )
        raise


# =====================================================
# ENCOUNTER → APPOINTMENT
# =====================================================
@frappe.whitelist()
def create_appointment_from_encounter(data):
    """
    Create OR Update Clinic Appointment from Patient Encounter
    """

    data = frappe.parse_json(data)

    encounter = data.get("encounter")

    if not encounter:
        frappe.throw("Encounter is required")

    encounter_doc = frappe.get_doc("Patient Encounter", encounter)

    practitioner = data.get("practitioner") or encounter_doc.pe_practitioner
    date = data.get("appointment_date")
    time = data.get("appointment_time")

    # ⚠️ safety: don't create without full data
    if not practitioner or not date or not time:
        return

    # 🔍 existing link
    existing = getattr(encounter_doc, "encounter_reference", None)

    # =====================================================
    # 🚫 PREVENT DOUBLE BOOKING (FINAL FIX)
    # =====================================================
    conflict_filters = {
        "practitioner": practitioner,
        "appointment_date": date,
        "appointment_time": time,
    }

    # exclude same appointment
    if existing:
        conflict_filters["name"] = ["!=", existing]

    # 🔥 MOST IMPORTANT FIX
    # exclude same encounter-linked appointment
    conflict_filters["custom_encounter"] = ["!=", encounter]

    conflict = frappe.db.exists("Clinic Appointment", conflict_filters)

    if conflict:
        frappe.throw("⚠️ This slot is already booked")

    # =====================================================
    # 🔁 UPDATE EXISTING
    # =====================================================
    if existing:
        appt = frappe.get_doc("Clinic Appointment", existing)

        appt.patient = data.get("patient")
        appt.practitioner = practitioner
        appt.appointment_date = date
        appt.appointment_time = time
        appt.custom_encounter = encounter

        appt.save(ignore_permissions=True)

        return appt.name

    # =====================================================
    # 🆕 CREATE NEW
    # =====================================================
    appt = frappe.new_doc("Clinic Appointment")

    appt.patient = data.get("patient")
    appt.practitioner = practitioner
    appt.appointment_date = date
    appt.appointment_time = time
    appt.status = "Scheduled"
    appt.custom_encounter = encounter

    appt.insert(ignore_permissions=True)

    # 🔗 update encounter
    encounter_doc.db_set(
        "encounter_reference",
        appt.name,
        update_modified=False
    )

    return appt.name


# =====================================================
# INTERNAL HELPER (IMPORTANT 🔥)
# =====================================================
def _create_or_update_from_encounter(doc):
    """
    Internal helper to avoid duplication
    """

    # ⚠️ prevent incomplete creation
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
    """
    Keep Encounter updated when Appointment changes
    """

    if not getattr(doc, "custom_encounter", None):
        return

    try:
        enc = frappe.get_doc("Patient Encounter", doc.custom_encounter)

        enc.pe_practitioner = doc.practitioner
        enc.pe_appointment_date = doc.appointment_date
        enc.pe_appointment_time = doc.appointment_time

        enc.save(ignore_permissions=True)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Encounter Sync Failed"
        )


# =====================================================
# APPOINTMENT HOOKS
# =====================================================
def after_insert(doc, method):
    """
    Auto create encounter when appointment is created
    """

    try:
        if not getattr(doc, "encounter_reference", None):
            create_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Auto Encounter Creation Failed (after_insert)"
        )
        raise


def on_update(doc, method):

    try:
        # ⭐ create encounter on check-in
        if (
            doc.appointment_status == "Checked In"
            and not getattr(doc, "encounter_reference", None)
        ):
            create_encounter_from_appointment(doc)

        # 🔄 always sync
        sync_encounter_from_appointment(doc)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "on_update Failed"
        )
        raise


# =====================================================
# ENCOUNTER HOOKS
# =====================================================
def after_insert_encounter(doc, method):
    if (
        doc.sr_encounter_type == "Appointment"
        and doc.pe_practitioner
        and doc.pe_appointment_date
        and doc.pe_appointment_time
    ):
        _create_or_update_from_encounter(doc)


def on_update_encounter(doc, method):
    """
    Update appointment when encounter changes
    """

    try:
        if doc.sr_encounter_type != "Appointment":
            return

        _create_or_update_from_encounter(doc)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Auto Appointment Update Failed (on_update)"
        )
        raise