import frappe

TARGET_DOCTYPE = "Patient Encounter"

# ❌ Skip system/internal fields
SKIP_FIELDS = {
    "name", "owner", "creation", "modified", "modified_by",
    "docstatus", "doctype", "idx",
    "parent", "parenttype", "parentfield",
    "_comments", "_liked_by", "_assign"
}

# 🚫 Do NOT override these fields
PROTECTED_FIELDS = {
    "patient",
    "company"
}

# 🔁 Custom mapping
FIELD_MAP = {
    "mobile_number": "sr_pe_mobile",
    "alternate_mobile": "sr_pe_alt_mobile",
    "patient_id": "sr_pe_id",
    "department": "sr_pe_deptt",
    "appointment_date": "pe_appointment_date",
    "appointment_time": "pe_appointment_time",

    # 🔥 FIX: practitioner mapping
    "practitioner": "pe_practitioner",
}

# ⚠️ KEEP FALSE IN PRODUCTION
ALLOW_FIELD_CREATION = False


# =====================================================
# MAIN MAPPER
# =====================================================
def map_appointment_to_encounter(appt, enc):

    source_meta = frappe.get_meta(appt.doctype)
    target_meta = frappe.get_meta(TARGET_DOCTYPE)

    for df in source_meta.fields:

        fieldname = df.fieldname

        # ❌ skip system/internal fields
        if fieldname in SKIP_FIELDS:
            continue

        # ❌ skip layout/UI fields
        if df.fieldtype in ["Table", "Section Break", "Column Break", "HTML"]:
            continue

        value = appt.get(fieldname)

        # ❌ skip empty values
        if not value:
            continue

        # 🔁 map field name
        target_field = FIELD_MAP.get(fieldname, fieldname)

        # 🚫 skip protected fields
        if target_field in PROTECTED_FIELDS:
            continue

        # ❌ skip if field does not exist
        if not target_meta.has_field(target_field):
            if ALLOW_FIELD_CREATION:
                ensure_field_exists(df, target_field)
                target_meta = frappe.get_meta(TARGET_DOCTYPE)  # refresh meta
            else:
                continue

        try:
            # ✅ do NOT overwrite existing values
            if not enc.get(target_field):
                enc.set(target_field, value)

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Mapping failed for field: {target_field}"
            )


# =====================================================
# OPTIONAL FIELD CREATION (DEV MODE ONLY)
# =====================================================
def ensure_field_exists(df, target_field):

    if frappe.db.exists("Custom Field", {
        "dt": TARGET_DOCTYPE,
        "fieldname": target_field
    }):
        return

    cf = frappe.new_doc("Custom Field")

    cf.dt = TARGET_DOCTYPE
    cf.fieldname = target_field
    cf.label = df.label
    cf.fieldtype = df.fieldtype
    cf.insert_after = "patient"

    # handle special types
    if df.fieldtype in ["Link", "Table", "Select"]:
        cf.options = df.options

    cf.insert(ignore_permissions=True)

    frappe.clear_cache(doctype=TARGET_DOCTYPE)