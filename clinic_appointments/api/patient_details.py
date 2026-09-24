import frappe


@frappe.whitelist()
def get_patient_details(patient):
    doc = frappe.get_doc("Patient", patient)
    doc.check_permission("read")
    fields = ("patient_name", "mobile", "phone", "sex", "sr_patient_id", "sr_medical_department")
    result = {field: doc.get(field) for field in fields if field in doc.permitted_fieldnames}
    if "privacy_shield" in frappe.get_installed_apps():
        from privacy_shield.activation import enabled_for
        if enabled_for("appointment_patient_details"):
            from privacy_shield.policy import current_capabilities
            from privacy_shield.projections import project_numbers
            capabilities = current_capabilities()
            result = project_numbers(result, {"mobile": "mask_mobile", "phone": "mask_phone"}, capabilities.view_full)
            result["resolve_numbers_on_server"] = not capabilities.view_full
    return result
