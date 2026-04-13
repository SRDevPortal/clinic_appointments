import frappe
from frappe.utils import getdate


@frappe.whitelist()
def get_setup_status():
    frappe.only_for(("System Manager",))

    return {
        "counts": {
            "clinic_appointments": frappe.db.count("Clinic Appointment"),
        },
        "recent_appointments": frappe.get_all(
            "Clinic Appointment",
            fields=[
                "name",
                "patient_name",
                "mobile_number",
                "appointment_date",
                "appointment_status",
                "encounter_reference",
                "practitioner",
                "modified",
            ],
            order_by="modified desc",
            limit=20,
        ),
    }


@frappe.whitelist()
def smoke_check():
    frappe.only_for(("System Manager",))

    checks = [
        {
            "name": "doctype:Clinic Appointment",
            "ok": bool(frappe.db.exists("DocType", "Clinic Appointment")),
            "message": "Clinic Appointment available"
            if frappe.db.exists("DocType", "Clinic Appointment")
            else "Clinic Appointment missing",
        },
        {
            "name": "doctype:Patient Encounter",
            "ok": bool(frappe.db.exists("DocType", "Patient Encounter")),
            "message": "Patient Encounter available"
            if frappe.db.exists("DocType", "Patient Encounter")
            else "Patient Encounter missing",
        },
        {
            "name": "sync-method",
            "ok": True,
            "message": "clinic_appointments.api.encounter_sync.create_or_update_clinic_appointment_from_encounter",
        },
    ]

    return {
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
    }


@frappe.whitelist()
def get_practitioner_slot_summary(practitioner=None, appointment_date=None, appointment_time=None):
    frappe.only_for(("System Manager",))

    if not practitioner or not appointment_date:
        return {
            "slots": [],
            "slot_count": 0,
            "message": "Select practitioner and appointment date."
        }

    appointment_date = getdate(appointment_date)
    day = appointment_date.strftime("%A")

    practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)

    practitioner_name = practitioner_doc.practitioner_name

    slots = []

    # 🔥 CORRECT FLOW
    for row in practitioner_doc.practitioner_schedules:
        schedule_name = row.schedule

        time_slots = frappe.get_all(
            "Healthcare Schedule Time Slot",
            filters={
                "parent": schedule_name,
                "day": day
            },
            fields=["from_time", "to_time"]
        )

        for t in time_slots:
            slots.append(f"{t.from_time} - {t.to_time}")

    return {
        "practitioner": practitioner,
        "practitioner_name": practitioner_name,
        "appointment_date": str(appointment_date),
        "appointment_time": appointment_time,
        "slot_count": len(slots),
        "slots": slots,
        "message": "Slots loaded successfully" if slots else "No slots for this day"
    }


@frappe.whitelist()
def get_available_slots(practitioner, appointment_date):
    from frappe.utils import getdate

    appointment_date = getdate(appointment_date)
    day = appointment_date.strftime("%A")

    practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)

    all_slots = []

    # 🔹 Get all schedule slots
    for row in practitioner_doc.practitioner_schedules:
        schedule = row.schedule

        time_slots = frappe.get_all(
            "Healthcare Schedule Time Slot",
            filters={
                "parent": schedule,
                "day": day
            },
            fields=["from_time"]
        )

        for t in time_slots:
            all_slots.append(str(t.from_time)[:5])  # HH:MM

    # 🔹 Get already booked slots
    booked = frappe.get_all(
        "Clinic Appointment",
        filters={
            "practitioner": practitioner,
            "appointment_date": appointment_date,
            "appointment_status": ["not in", ["Cancelled", "No Show"]]
        },
        fields=["appointment_time"]
    )

    booked_slots = [str(b.appointment_time)[:5] for b in booked]

    # 🔹 Filter available
    available = [s for s in all_slots if s not in booked_slots]

    return {
        "all_slots": all_slots,
        "booked_slots": booked_slots,
        "available_slots": available
    }