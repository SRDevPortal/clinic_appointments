const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
    path.join(__dirname, "../public/js/clinic_appointment.js"),
    "utf8",
);

function makeContext(getResponse) {
    const context = {
        __: value => value,
        setTimeout,
        frappe: {
            ui: {form: {on() {}}},
            datetime: {
                str_to_obj: value => new Date(value),
                get_today: () => "2026-10-05",
            },
            call: () => getResponse(),
        },
    };
    vm.createContext(context);
    vm.runInContext(source, context);
    return context;
}

function makeForm(doc) {
    const required = {};
    const refreshed = [];
    const frm = {
        doc: {...doc},
        set_df_property(fieldname, property, value) {
            if (property === "reqd") required[fieldname] = value;
        },
        set_value(values) {
            Object.assign(this.doc, values);
            return Promise.resolve();
        },
        refresh_field(fieldname) { refreshed.push(fieldname); },
    };
    return {frm, required, refreshed};
}

(async () => {
    const restricted = {
        patient_name: "Second Synthetic",
        mask_mobile: "******0111",
        mask_phone: "******0122",
        resolve_numbers_on_server: true,
    };
    let context = makeContext(() => Promise.resolve({message: restricted}));
    let state = makeForm({
        patient: "P2",
        patient_name: "First Synthetic",
        mobile_number: "2025550101",
        alternate_mobile: "2025550199",
        __privacy_shield: {edit_original: false},
    });
    state.frm.__privacy_patient_source = "P1";
    await context.set_patient_values(state.frm);
    assert.equal(state.required.mobile_number, 0);
    assert.equal(state.frm.doc.patient_name, "Second Synthetic");
    assert.equal(state.frm.doc.mask_mobile, "******0111");
    assert.equal(state.frm.doc.mask_alternate_mobile, "******0122");
    assert.equal("mobile_number" in state.frm.doc, false);
    assert.equal("alternate_mobile" in state.frm.doc, false);
    assert.deepEqual(state.refreshed, ["mobile_number", "alternate_mobile"]);

    const fullView = {
        patient_name: "Full View Synthetic",
        mobile: "2025550133",
        phone: "2025550144",
        resolve_numbers_on_server: false,
    };
    context = makeContext(() => Promise.resolve({message: fullView}));
    state = makeForm({patient: "P3", mobile_number: "", alternate_mobile: ""});
    await context.set_patient_values(state.frm);
    assert.equal(state.required.mobile_number, 1);
    assert.equal(state.frm.doc.mobile_number, "2025550133");
    assert.equal(state.frm.doc.alternate_mobile, "2025550144");

    let resolveLookup;
    context = makeContext(() => new Promise(resolve => { resolveLookup = resolve; }));
    state = makeForm({patient: "P4", patient_name: "Unchanged"});
    const pending = context.set_patient_values(state.frm);
    state.frm.doc.patient = "P5";
    resolveLookup({message: fullView});
    await pending;
    assert.equal(state.frm.doc.patient_name, "Unchanged");
    assert.equal("mobile_number" in state.frm.doc, false);

    console.log("Clinic Appointment privacy UI checks passed: restricted projection, patient change, full view, stale response.");
})().catch(error => {
    console.error(error);
    process.exit(1);
});