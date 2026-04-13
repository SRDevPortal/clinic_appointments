import frappe


def get_changed_fields(doc, updates):
    changed = []
    for fieldname, new_value in (updates or {}).items():
        if not hasattr(doc, "get"):
            continue
        old_value = doc.get(fieldname)
        if old_value != new_value:
            changed.append(fieldname)
    return changed


def _field_label(doctype, fieldname):
    meta = frappe.get_meta(doctype)
    df = meta.get_field(fieldname)
    if df and df.label:
        return df.label

    return fieldname.replace("_", " ").title()


def add_sync_comment(doc, source_doctype, source_name, changed_fields):
    if not changed_fields:
        return

    fields_text = ", ".join(
        sorted(_field_label(doc.doctype, fieldname) for fieldname in changed_fields)
    )
    doc.add_comment(
        "Comment",
        text=(
            f"Synced from {source_doctype} {source_name}. "
            f"Updated fields: {fields_text}"
        ),
    )
