from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import frappe
from clinic_appointments.clinic_appointments.doctype.clinic_appointment import clinic_appointment as module


class AppointmentTimeTests(TestCase):
    def setUp(self):
        for name, value in [
            ("now_datetime", lambda: datetime(2026, 9, 24, 15, 50)),
            ("_", lambda text: text),
        ]:
            p = patch.object(module, name, value)
            p.start()
            self.addCleanup(p.stop)
        def throw(message):
            raise frappe.ValidationError(message)
        p = patch.object(module.frappe, "throw", throw)
        p.start()
        self.addCleanup(p.stop)

    def doc(self, day="2026-09-24", time="15:45:00", *, new=False,
            old_day=date(2026, 9, 24), old_time=timedelta(hours=15, minutes=45)):
        old = SimpleNamespace(appointment_date=old_day, appointment_time=old_time)
        return SimpleNamespace(
            appointment_date=day, appointment_time=time,
            is_new=lambda: new, get_doc_before_save=lambda: old,
        )

    def test_payment_update_to_elapsed_appointment_is_allowed(self):
        module.validate_future_appointment(self.doc())

    def test_existing_previous_day_appointment_can_be_updated(self):
        module.validate_future_appointment(self.doc(day="2026-09-23", old_day=date(2026, 9, 23)))

    def test_new_appointment_in_past_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            module.validate_future_appointment(self.doc(new=True))

    def test_rescheduling_to_elapsed_time_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            module.validate_future_appointment(self.doc(old_time=timedelta(hours=16)))

    def test_rescheduling_to_previous_day_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            module.validate_future_appointment(self.doc(day="2026-09-23"))

    def test_adding_elapsed_time_to_existing_date_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            module.validate_future_appointment(self.doc(old_time=None))

    def test_future_creation_and_rescheduling_are_allowed(self):
        module.validate_future_appointment(self.doc(time="16:00:00", new=True))
        module.validate_future_appointment(self.doc(time="16:00:00"))

    def test_missing_original_snapshot_does_not_bypass_validation(self):
        doc = self.doc()
        doc.get_doc_before_save = lambda: None
        with self.assertRaises(frappe.ValidationError):
            module.validate_future_appointment(doc)

    def test_blank_time_representations_do_not_make_an_old_slot_a_reschedule(self):
        module.validate_future_appointment(self.doc(day="2026-09-23", time="",
            old_day=date(2026, 9, 23), old_time=None))
