import logging

from clinic_appointments.setup.clinic_appointment import apply as clinic_appointment_setup
from clinic_appointments.setup.encounter import apply as encounter_setup

logger = logging.getLogger(__name__)


def setup_all():
    """Run all setup steps"""

    logger.info("Running Clinic Appointments setup...")

    # 🔹 Encounter setup
    encounter_setup()
    clinic_appointment_setup()

    logger.info("✅ Clinic Appointments setup completed")