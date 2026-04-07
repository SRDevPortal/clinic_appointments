frappe.ui.form.on('Clinic Appointment', {

	refresh(frm) {
		// 🔒 Disable manual time
		frm.set_df_property('appointment_time', 'read_only', 1);

		if (frm.doc.patient) {
			set_patient_values(frm);
		}
	},

	patient(frm) {
		set_patient_values(frm);
	},

	practitioner(frm) {
		trigger_slot_dialog(frm);
	},

	appointment_date(frm) {
		trigger_slot_dialog(frm);
	}
});


// -----------------------------
// PATIENT AUTO-FILL
// -----------------------------
function set_patient_values(frm) {

	// 🔴 Handle patient removed
	if (!frm.doc.patient) {
		frm.set_value({
			patient_name: '',
			mobile_number: '',
			patient_gender: '',
			patient_id: '',
			department: ''
		});
		return;
	}

	// 🟢 Fetch minimal data (fast)
	frappe.db.get_value('Patient', frm.doc.patient, [
		'patient_name',
		'mobile',
		'sex',
		'sr_patient_id',
		'sr_medical_department'
	]).then(r => {

		let p = r.message || {};

		frm.set_value({
			// 🧠 do not override if already typed
			patient_name: frm.doc.patient_name || p.patient_name || '',
			mobile_number: frm.doc.mobile_number || p.mobile || '',
            alternate_mobile: frm.doc.alternate_mobile || p.phone || '',

			// always update system fields
			patient_gender: p.sex || '',
			patient_id: p.sr_patient_id || '',
			department: p.sr_medical_department || ''
		});

	});
}


// -----------------------------
// AUTO SLOT POPUP
// -----------------------------
function trigger_slot_dialog(frm) {

	if (frm._slot_dialog_open) return;

	if (!frm.doc.practitioner || !frm.doc.appointment_date) return;

	frm._slot_dialog_open = true;

	setTimeout(() => {
		open_slot_dialog(frm);
		frm._slot_dialog_open = false;
	}, 300);
}


// -----------------------------
// SLOT DIALOG
// -----------------------------
function open_slot_dialog(frm) {

	frappe.call({
		method: "clinic_appointments.api.setup.get_available_slots",
		args: {
			practitioner: frm.doc.practitioner,
			appointment_date: frm.doc.appointment_date
		}
	}).then(r => {

		const data = r.message;

		let html = `<div style="display:flex;flex-wrap:wrap;gap:10px;">`;

		data.all_slots.forEach(slot => {

			let isBooked = data.booked_slots.includes(slot);

			html += `
				<button 
					class="slot-btn"
					data-slot="${slot}"
					style="
						padding:8px 14px;
						border-radius:20px;
						border:none;
						background:${isBooked ? '#e0e0e0' : '#f5f5f5'};
						color:${isBooked ? '#999' : '#000'};
						cursor:${isBooked ? 'not-allowed' : 'pointer'};
					"
					${isBooked ? 'disabled' : ''}
				>
					${slot}
				</button>
			`;
		});

		html += `</div>`;

		let d = new frappe.ui.Dialog({
			title: 'Available Slots',
			fields: [{ fieldtype: 'HTML', fieldname: 'slots_html' }],
			primary_action_label: 'Book',
			primary_action() {

				if (!d.selected_slot) {
					frappe.msgprint("Please select a slot");
					return;
				}

				frm.set_value("appointment_time", d.selected_slot + ":00");
				d.hide();
			}
		});

		d.fields_dict.slots_html.$wrapper.html(html);

		d.$wrapper.on('click', '.slot-btn', function () {

			if ($(this).prop('disabled')) return;

			$('.slot-btn').css("background", "#f5f5f5");
			$(this).css("background", "#d0eaff");

			d.selected_slot = $(this).data('slot');
		});

		d.show();
	});
}