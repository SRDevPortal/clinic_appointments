import frappe
import json
import logging
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields as _ccf

logger = logging.getLogger(__name__)

MODULE_DEF_NAME = "Clinic Appointments" # Desk Module Def label
APP_PY_MODULE = "clinic_appointments"   # Python package name (matches app folder)


# =====================================================
# MODULE UTILITIES
# =====================================================
def ensure_module_def(module_name=MODULE_DEF_NAME, app_name=APP_PY_MODULE):
    """Ensure Module Def exists"""
    if not frappe.db.exists("Module Def", module_name):
        logger.info(f"Creating Module Def: {module_name}")
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": app_name
        }).insert(ignore_permissions=True)

        frappe.db.commit()


# =====================================================
# CUSTOM FIELD CREATION
# =====================================================
def create_cf_with_module(mapping: dict, module: str = MODULE_DEF_NAME):
    """
    Wrapper over create_custom_fields
    Adds module automatically
    """

    for dt, fields in mapping.items():
        for f in fields:
            f.setdefault("module", module)

    logger.info("Creating custom fields")
    _ccf(mapping, ignore_validate=True)

    frappe.clear_cache()


# =====================================================
# PROPERTY SETTER
# =====================================================
def upsert_property_setter(doctype, fieldname, prop, value, property_type, module=MODULE_DEF_NAME):
    is_dt_level = not fieldname
    ps_name = f"{doctype}-{prop}" if is_dt_level else f"{doctype}-{fieldname}-{prop}"

    if frappe.db.exists("Property Setter", ps_name):
        ps = frappe.get_doc("Property Setter", ps_name)
    else:
        ps = frappe.new_doc("Property Setter")
        ps.name = ps_name
        ps.doc_type = doctype
        ps.doctype_or_field = "DocType" if is_dt_level else "DocField"
        ps.field_name = None if is_dt_level else fieldname
        ps.module = module

    ps.property = prop
    ps.value = value
    ps.property_type = property_type
    ps.module = module
    ps.save(ignore_permissions=True)

    frappe.db.commit()


# =====================================================
# FIELD ORDER UTILITIES
# =====================================================
def ensure_field_after(doctype: str, fieldname: str, after: str):
    meta = frappe.get_meta(doctype)
    fields = [df.fieldname for df in meta.fields]

    if fieldname not in fields or after not in fields:
        return

    fields.remove(fieldname)
    idx = fields.index(after)
    fields.insert(idx + 1, fieldname)

    upsert_property_setter(doctype, None, "field_order", json.dumps(fields), "Text")
    frappe.clear_cache(doctype=doctype)


# =====================================================
# OPTIONAL HELPERS (FUTURE USE)
# =====================================================
def set_label(dt: str, fieldname: str, label: str):
    upsert_property_setter(dt, fieldname, "label", label, "Data")


def collapse_section(dt: str, fieldname: str, collapse=True):
    upsert_property_setter(dt, fieldname, "collapsible", "1" if collapse else "0", "Check")


def upsert_title_field(doctype: str, fieldname: str):
    current = frappe.db.get_value("DocType", doctype, "title_field")

    if current != fieldname:
        frappe.db.set_value("DocType", doctype, "title_field", fieldname)
        frappe.clear_cache(doctype=doctype)