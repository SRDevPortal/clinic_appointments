frappe.ui.form.on('CRM Lead', {
	refresh(frm) {
		frm.add_custom_button(__('Create Clinic Appointment'), () => {

			const route = {
				lead_reference: frm.doc.name,
				patient_name: frm.doc.lead_name || '',
				mobile_number: frm.doc.mobile_no || frm.doc.phone || '',
				remarks: __('Created from Lead {0}', [frm.doc.name])
			};

			frappe.new_doc('Clinic Appointment', route);

		}, __('Create'));
	}
});