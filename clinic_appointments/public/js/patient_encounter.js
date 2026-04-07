frappe.ui.form.on("Patient Encounter", {
    pe_practitioner(frm) {
        trigger_slot_dialog(frm);
    },
    pe_appointment_date(frm) {
        trigger_slot_dialog(frm);
    }
});


// -----------------------------
// AUTO SLOT POPUP
// -----------------------------
function trigger_slot_dialog(frm) {

    // prevent multiple triggers
    if (frm._slot_dialog_open) return;

    // require fields
    if (!frm.doc.pe_practitioner || !frm.doc.pe_appointment_date) return;

    // optional: prevent reopening if already selected
    if (frm.doc.pe_appointment_time) return;

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
            practitioner: frm.doc.pe_practitioner,
            appointment_date: frm.doc.pe_appointment_date
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
            primary_action_label: 'Select',
            primary_action() {

                if (!d.selected_slot) {
                    frappe.msgprint("Please select a slot");
                    return;
                }

                let selected_time = d.selected_slot;

                // ✅ set time
                frm.set_value("pe_appointment_time", selected_time).then(() => {

                    // 🔥 CREATE / UPDATE APPOINTMENT
                    frappe.call({
                        method: "clinic_appointments.api.encounter.create_appointment_from_encounter",
                        args: {
                            data: {
                                patient: frm.doc.patient,
                                practitioner: frm.doc.pe_practitioner,
                                appointment_date: frm.doc.pe_appointment_date,
                                appointment_time: selected_time,
                                encounter: frm.doc.name
                            }
                        },
                        freeze: true,
                        callback: function (r) {
                            if (r.message) {

                                // 🔗 link appointment
                                frm.set_value("encounter_reference", r.message);

                                frappe.show_alert({
                                    message: "✅ Appointment Linked: " + r.message,
                                    indicator: "green"
                                });

                                // optional save
                                frm.save();
                            }
                        },
                        error: function (err) {
                            frappe.msgprint(err.message || "⚠️ Slot already booked");
                        }
                    });

                });

                d.hide();
            }
        });

        d.fields_dict.slots_html.$wrapper.html(html);

        // ✅ FIX: prevent multiple bindings
        d.$wrapper
            .off('click', '.slot-btn')
            .on('click', '.slot-btn', function () {

                if ($(this).prop('disabled')) return;

                $('.slot-btn').css("background", "#f5f5f5");
                $(this).css("background", "#d0eaff");

                d.selected_slot = $(this).data('slot');
            });

        d.show();
    });
}