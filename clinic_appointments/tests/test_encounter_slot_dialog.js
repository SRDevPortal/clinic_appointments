const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(require("node:path").join(__dirname, "../public/js/patient_encounter.js"), "utf8");
async function check(isNew) {
    const calls = [], alerts = [];
    let dialog, saves = 0;
    const wrapper = {html() {}, off() {return this;}, on() {return this;}};
    const frappe = {
        ui: {form: {on() {}}, Dialog: function(options) {
            Object.assign(this, options);
            this.fields_dict = {slots_html: {$wrapper: wrapper}};
            this.$wrapper = wrapper;
            this.show = () => {}; this.hide = () => {};
            dialog = this;
        }},
        datetime: {get_today: () => "2026-09-28"},
        show_alert: value => alerts.push(value),
        call: options => {
            calls.push(options);
            if (options.method.endsWith("get_available_slots"))
                return Promise.resolve({message: {all_slots: ["12:30:00"], booked_slots: []}});
            options.callback({message: "TEST-APPOINTMENT"});
        }
    };
    const frm = {
        doc: {name: isNew ? "new-patient-encounter-test" : "TEST-ENCOUNTER",
            patient: "TEST-PATIENT", pe_practitioner: "TEST-PRACTITIONER",
            pe_appointment_date: "2026-09-29"},
        is_new: () => isNew,
        set_value: (key, value) => {frm.doc[key] = value; return Promise.resolve();},
        save: () => {saves++;}
    };
    const context = {frappe, __: value => value};
    vm.createContext(context); vm.runInContext(source, context);
    context.open_slot_dialog(frm);
    await Promise.resolve();
    dialog.selected_slot = "12:30:00";
    dialog.primary_action();
    await Promise.resolve();
    assert.equal(frm.doc.pe_appointment_time, "12:30:00");
    if (isNew) {
        assert.equal(calls.length, 1, "No appointment RPC before first save");
        assert.equal(saves, 0, "Agent can finish required fields before saving");
        assert.match(alerts[0].message, /Save the Encounter/);
    } else {
        assert.equal(calls.length, 2);
        assert.equal(calls[1].args.data.encounter, "TEST-ENCOUNTER");
        assert.equal(frm.doc.encounter_reference, "TEST-APPOINTMENT");
        assert.equal(saves, 1);
    }
}
(async () => {await check(true); await check(false); console.log("2 slot-dialog regressions passed");})().catch(e => {console.error(e); process.exit(1);});
